import json
from state import AnalystState
from observability.tracer import tracer
from config import get_client, MODEL
from prompts.final_answer import FINAL_ANSWER_SYSTEM, REPORT_USER


def final_answer_node(state: AnalystState) -> AnalystState:
    client = get_client()
    tracer.log("final_answer", "Generating evidence-based report")

    analysis_results = state.get("analysis_results", {})
    plots = state.get("generated_plots", [])

    # Build results summary — only what was actually computed
    results_summary = {
        "dataset_summary": analysis_results.get("dataset_summary", {}),
        "missing_values": analysis_results.get("missing_values", {}),
        "duplicates": analysis_results.get("duplicates", {}),
        "outliers": analysis_results.get("outliers", {}),
        "correlations": {
            "method": analysis_results.get("correlations", {}).get("method", ""),
            "strong_pairs": analysis_results.get("correlations", {}).get("strong_pairs", [])
        },
        "target_analysis": analysis_results.get("target_analysis", {}),
        "statistical_tests": analysis_results.get("statistical_tests", {}),
        "step_insights": state.get("accumulated_insights", []),
        "step_history_outputs": [
            {
                "step": h["step"],
                "description": h["description"],
                "output": str(h["result"].get("output", ""))[:500]
            }
            for h in state.get("step_history", [])
            if h["result"].get("status") == "success"
        ]
    }

    prompt = REPORT_USER.format(
        query=state["user_query"],
        rows=state["df_shape"][0],
        cols=state["df_shape"][1],
        results=json.dumps(results_summary, indent=2, default=str)[:6000],
        plots="\n".join(plots) if plots else "No plots generated"
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": FINAL_ANSWER_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=4000,
    )

    report = response.choices[0].message.content
    tracer.log("final_answer", "Report complete")

    # Update analysis_results with final insights for dashboard
    analysis_results["insights"] = state.get("accumulated_insights", [])

    return {
        **state,
        "final_report": report,
        "analysis_results": analysis_results
    }

def answer_followup(question: str, memory: dict, report: str, df_json: str) -> str:
    client = get_client()
    
    system = f"""You are a data analyst assistant. You have already completed a full analysis and generated a report.

Here is the report you generated:
{report}

The user may ask follow-up questions about the analysis, the data, or request additional insights.
Answer based strictly on the report and analysis already done.
If they ask for new calculations or plots, say you can only answer based on existing analysis."""

    memory.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}] + memory,
        temperature=0.3,
        #max_tokens=1000, <- adjust as needed based on your model limits
    )

    answer = response.choices[0].message.content
    memory.append({"role": "assistant", "content": answer})
    return answer