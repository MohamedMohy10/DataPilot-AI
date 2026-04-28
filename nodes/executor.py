import json
from io import StringIO
import pandas as pd
from openai import OpenAI
from state import AnalystState
from tools.python_runner import run_python
from tools.eda import analyze_dataframe
from tools.registry import TOOL_SCHEMAS
from memory.session import SessionMemory
from prompts.executor import EXECUTOR_SYSTEM, EXECUTOR_USER
from observability.tracer import tracer
from config import get_client, MODEL, MAX_RETRIES

session_memory = SessionMemory()


def executor_node(state: AnalystState) -> AnalystState:
    client = get_client()

    # ← load persisted df if available, otherwise load fresh from CSV
    if state.get("df_json"):
        df = pd.read_json(StringIO(state["df_json"]))
    else:
        df = pd.read_csv(state["dataset_path"])

    step = state["plan"][state["current_step_index"]]
    tracer.log("executor", f"Executing step {step['step']}: {step['description']}")

    profile = state["df_profile"]
    messages = [
        {"role": "system", "content": EXECUTOR_SYSTEM},
        {
            "role": "user",
            "content": EXECUTOR_USER.format(
                step_description=step["description"],
                shape=state["df_shape"],
                columns=state["df_columns"],
                dtypes=profile["columns"],
                history=session_memory.get_context_summary()
            )
        }
    ]

    execution_result = {}
    insight = ""
    new_plots = []
    retry_count = state.get("retry_count", 0)
    fn_name = ""
    fn_args = {}
    updated_df = df.copy()      # ← track df mutations across tool calls

    for attempt in range(MAX_RETRIES):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.1,
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            tracer.log("executor", "No tool call returned", {"content": msg.content})
            execution_result = {"status": "success", "output": msg.content or "(done)", "error": None, "plots": []}
            break

        should_retry = False

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            tracer.log("executor", f"Tool called: {fn_name}", fn_args)

            if fn_name == "run_python":
                result = run_python(fn_args["code"], updated_df)
                execution_result = result
                new_plots.extend(result.get("plots", []))

                tracer.log(
                    "executor",
                    f"Code execution: {result['status']}",
                    {"output": result.get("output"), "error": result.get("error")}
                )

                if result["status"] == "error" and attempt < MAX_RETRIES - 1:
                    tracer.log("executor", f"Retry {attempt + 1}/{MAX_RETRIES}")
                    retry_count += 1
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"ERROR — fix and retry:\n{result['error']}"
                    })
                    should_retry = True
                    break
                else:
                    # ← re-run code to capture df mutations into updated_df
                    _capture_df_mutations(fn_args["code"], updated_df, result)

                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"OUTPUT:\n{result['output']}"
                    })

            elif fn_name == "analyze_dataframe":
                result = analyze_dataframe(updated_df)
                execution_result = {
                    "status": "success",
                    "output": json.dumps(result),
                    "error": None,
                    "plots": []
                }
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

            elif fn_name == "generate_insight":
                insight = fn_args["insight"]
                tracer.log("executor", f"Insight: {insight}")
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "Insight recorded."
                })

            elif fn_name == "finalize":
                tracer.log("executor", "Agent called finalize")
                execution_result = {
                    "status": "success",
                    "output": "Finalized.",
                    "error": None,
                    "plots": []
                }
                break

        if not should_retry and execution_result.get("status") == "success":
            break

    # Record to session memory
    session_memory.record_step(
        step=step["step"],
        tool=fn_name or step.get("tool", "run_python"),
        code=fn_args.get("code", ""),
        result=execution_result,
        insight=insight
    )

    updated_history = state["step_history"] + [{
        "step": step["step"],
        "description": step["description"],
        "result": execution_result,
        "insight": insight
    }]

    updated_insights = state["accumulated_insights"] + ([insight] if insight else [])
    updated_plots = state["generated_plots"] + new_plots

    return {
        **state,
        "df_json": updated_df.to_json(),    # ← persist mutated df back to state
        "execution_result": execution_result,
        "step_history": updated_history,
        "accumulated_insights": updated_insights,
        "generated_plots": updated_plots,
        "retry_count": retry_count,
        "iteration_count": state["iteration_count"] + 1,
    }


def _capture_df_mutations(code: str, df: pd.DataFrame, execution_result: dict):
    """
    Capture df mutations from already-executed code using the returned local scope.
    No re-execution — just copy columns from the scope we already have.
    """
    local_scope = execution_result.get("local_scope", {})
    if "df" not in local_scope:
        return

    captured = local_scope["df"]
    try:
        for col in captured.columns:
            df[col] = captured[col].values
        for col in list(df.columns):
            if col not in captured.columns:
                df.drop(columns=[col], inplace=True)
    except Exception:
        pass