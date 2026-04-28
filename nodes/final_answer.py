from openai import OpenAI
from state import AnalystState
from observability.tracer import tracer
from config import get_client, MODEL, MAX_ITERATIONS, MAX_RETRIES


REPORT_SYSTEM = """You are a senior data analyst writing a final analysis report.
Write in clear, executive-friendly language.
Base EVERY claim strictly on the insights provided — no hallucinations.
Format with markdown headers."""

def final_answer_node(state: AnalystState) -> AnalystState:
    client = get_client()

    tracer.log("final_answer", "Generating final report")

    insights_text = "\n".join(f"- {i}" for i in state["accumulated_insights"])
    plots_text = "\n".join(state["generated_plots"]) if state["generated_plots"] else "None"

    prompt = f"""Original query: {state['user_query']}

Dataset: {state['df_shape'][0]} rows × {state['df_shape'][1]} columns
Columns: {', '.join(state['df_columns'])}

Insights gathered during analysis:
{insights_text}

Plots generated: {plots_text}

Write a comprehensive final report covering:
1. Executive Summary
2. Key Findings (data-backed)
3. Correlations & Patterns
4. Anomalies
5. Recommendations
6. Limitations"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": REPORT_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    report = response.choices[0].message.content
    tracer.log("final_answer", "Report complete")

    return {**state, "final_report": report}

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
        max_tokens=1000,
    )

    answer = response.choices[0].message.content
    memory.append({"role": "assistant", "content": answer})
    return answer