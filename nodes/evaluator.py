import json
from openai import OpenAI
from state import AnalystState
from prompts.evaluator import EVALUATOR_SYSTEM, EVALUATOR_USER
from observability.tracer import tracer
from config import get_client, MODEL, MAX_ITERATIONS, MAX_RETRIES


def evaluator_node(state: AnalystState) -> AnalystState:
    client = get_client()
    last_result = state.get("execution_result", {})

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM},
            {
                "role": "user",
                "content": EVALUATOR_USER.format(
                    current=state["current_step_index"] + 1,
                    total=len(state["plan"]),
                    insight_count=len(state["accumulated_insights"]),
                    last_status=last_result.get("status", "unknown"),
                    last_error=last_result.get("error", "none"),
                    iterations=state["iteration_count"],
                    max_iterations=MAX_ITERATIONS,
                )
            }
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    eval_data = json.loads(raw)
    decision = eval_data["decision"]

    tracer.log("evaluator", f"Decision: {decision}", eval_data)

    # Force finalize if max iterations hit
    if state["iteration_count"] >= MAX_ITERATIONS:
        decision = "finalize"
        tracer.log("evaluator", "Max iterations reached — forcing finalize")

    return {**state, "evaluation_decision": decision}