import json
import pandas as pd
from openai import OpenAI
from state import AnalystState
from tools.eda import analyze_dataframe
from prompts.planner import PLANNER_SYSTEM, PLANNER_USER
from observability.tracer import tracer
from config import get_client, MODEL


def planner_node(state: AnalystState) -> AnalystState:
    client = get_client()
    tracer.log("planner", "Starting planning phase")

    df = pd.read_csv(state["dataset_path"], encoding="utf-8")  # Adjust encoding as needed
    profile = analyze_dataframe(df)

    tracer.log("planner", "EDA profile generated", {"shape": profile["shape"]})

    prompt = PLANNER_USER.format(
        profile=json.dumps(profile, indent=2),
        query=state["user_query"]
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    plan_data = json.loads(raw)

    tracer.log("planner", f"Plan created: {len(plan_data['steps'])} steps", plan_data)

    return {
        **state,
        "df_profile": profile,
        "df_columns": list(profile["columns"].keys()),
        "df_shape": (profile["shape"]["rows"], profile["shape"]["columns"]),
        "df_json": df.to_json(),        # ← serialize original df into state
        "plan": plan_data["steps"],
        "current_step_index": 0,
        "iteration_count": 0,
        "retry_count": 0,
        "step_history": [],
        "accumulated_insights": [],
        "generated_plots": [],
    }