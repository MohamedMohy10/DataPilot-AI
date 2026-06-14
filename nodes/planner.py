import json
import pandas as pd
from state import AnalystState
from tools.eda import analyze_dataframe
from tools.analysis_modules import build_analysis_results
from observability.tracer import tracer
from config import get_client, MODEL


def planner_node(state: AnalystState) -> AnalystState:
    client = get_client()
    tracer.log("planner", "Starting planning phase")

    df = pd.read_csv(state["dataset_path"])
    profile = analyze_dataframe(df)

    tracer.log("planner", "EDA profile generated", {"shape": profile["shape"]})

    # Run full structured analysis immediately
    tracer.log("planner", "Running structured analysis pipeline")
    analysis_results = build_analysis_results(df)
    tracer.log("planner", f"Analysis complete — {len(analysis_results['plots'])} plots generated")

    # Ask LLM to create focused follow-up steps based on what was found
    prompt = f"""You are a senior data analyst. A structured analysis has already been run on a dataset.

Dataset: {profile['shape']['rows']} rows x {profile['shape']['columns']} columns
Columns: {df.columns.tolist()}
Target column detected: {analysis_results.get('target_column', 'None')}
Missing values: {analysis_results['missing_values']['has_missing']}
Strong correlations found: {len(analysis_results['correlations'].get('strong_pairs', []))}
Plots already generated: {len(analysis_results['plots'])}

User query: {state['user_query']}

Based on the above, create 2-3 ADDITIONAL focused analysis steps that go BEYOND the baseline analysis already done.
Only plan steps that add new value.

Return ONLY valid JSON:
{{
  "goal": "one sentence goal",
  "steps": [
    {{
      "step": 1,
      "description": "specific additional analysis to run",
      "tool": "run_python",
      "expected_numerical_outputs": ["exact metrics to compute"]
    }}
  ]
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        plan_data = json.loads(raw)
    except Exception:
        plan_data = {"goal": state["user_query"], "steps": []}

    tracer.log("planner", f"Plan created: {len(plan_data['steps'])} additional steps")

    return {
        **state,
        "df_profile": profile,
        "df_columns": df.columns.tolist(),
        "df_shape": (profile["shape"]["rows"], profile["shape"]["columns"]),
        "df_json": df.to_json(),
        "plan": plan_data["steps"],
        "current_step_index": 0,
        "iteration_count": 0,
        "retry_count": 0,
        "step_history": [],
        "accumulated_insights": [],
        "generated_plots": analysis_results["plots"],    # ← pre-populated
        "analysis_results": analysis_results,            # ← structured results
    }