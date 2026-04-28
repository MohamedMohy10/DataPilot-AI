import streamlit as st
import tempfile
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from graph import build_graph
from pdf_generator import generate_pdf_report

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Data Analyst Agent",
    page_icon="📊",
    layout="wide"
)

# ── Styles ────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #6a40f5;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .step-box {
        background: #383838;
        border-left: 4px solid #0f3460;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
    .insight-box {
        background: #383838;
        border-left: 4px solid #38a169;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
    .error-box {
        background: #383838;
        border-left: 4px solid #e53e3e;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.markdown('<div class="main-header">📊 Agentic Data Analyst</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Powered by LangGraph · ReAct Loop · Auto EDA</div>', unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info("Upload a CSV and ask any analytical question. The agent will plan, execute, and generate a full report.")
    st.markdown("---")
    st.markdown("**Agent Architecture**")
    st.markdown("- 🧠 Planner Node")
    st.markdown("- ⚙️ Executor Node")
    st.markdown("- 🔍 Evaluator Node")
    st.markdown("- 💾 Memory Node")
    st.markdown("- 📝 Final Answer Node")
    st.markdown("---")
    st.markdown("**Capabilities**")
    st.markdown("- Auto EDA")
    st.markdown("- Code generation & execution")
    st.markdown("- Self-healing retry loop")
    st.markdown("- PDF report export")

# ── Main layout ───────────────────────────────────────────────
col1, col2 = st.columns([1, 1.6])

with col1:
    st.subheader("📁 Upload Dataset")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_file.read())
            st.session_state["csv_path"] = tmp.name

        df_preview = pd.read_csv(st.session_state["csv_path"])
        st.success(f"✅ Loaded: {df_preview.shape[0]} rows × {df_preview.shape[1]} columns")
        st.dataframe(df_preview.head(5), use_container_width=True)

    st.subheader("💬 Your Question")
    query = st.text_area(
        "What would you like to analyze?",
        placeholder="e.g. Analyze this dataset and find key insights, correlations, and anomalies.",
        height=100
    )

    run_button = st.button("🚀 Run Agent", type="primary", use_container_width=True)

with col2:
    st.subheader("🤖 Agent Activity")
    activity_container = st.container()

# ── Agent execution ───────────────────────────────────────────
if run_button:
    if not uploaded_file:
        st.error("Please upload a CSV file first.")
    elif not query.strip():
        st.error("Please enter a question.")
    else:
        with activity_container:
            log_placeholder = st.empty()
            logs = []

            def add_log(msg: str, kind: str = "step"):
                css_class = "step-box" if kind == "step" else "insight-box" if kind == "insight" else "error-box"
                logs.append(f'<div class="{css_class}">{msg}</div>')
                log_placeholder.markdown("\n".join(logs), unsafe_allow_html=True)

        # Monkey-patch tracer to stream logs into UI
        from observability.tracer import tracer
        original_log = tracer.log

        def ui_log(node, event, data=None):
            original_log(node, event, data)
            icon_map = {
                "planner": "🧠",
                "executor": "⚙️",
                "evaluator": "🔍",
                "memory": "💾",
                "final_answer": "📝"
            }
            icon = icon_map.get(node, "•")
            kind = "insight" if "Insight" in event else "step"
            add_log(f"{icon} <b>[{node.upper()}]</b> {event}", kind)

        tracer.log = ui_log

        initial_state = {
            "user_query": query,
            "dataset_path": st.session_state["csv_path"],
            "messages": [],
            "generated_code": "",
            "execution_result": {},
            "step_history": [],
            "accumulated_insights": [],
            "generated_plots": [],
            "evaluation_decision": "",
            "iteration_count": 0,
            "retry_count": 0,
            "final_report": "",
            "plan": [],
            "current_step_index": 0,
            "df_profile": {},
            "df_columns": [],
            "df_shape": (0, 0),
            "df_json": "",
        }

        with st.spinner("Agent is working..."):
            try:
                graph = build_graph()
                # Reset chat history when running new analysis
                st.session_state["chat_history"] = []
                st.session_state["chat_memory"] = []
                final_state = graph.invoke(initial_state)
                st.session_state["final_state"] = final_state
                add_log("✅ Analysis complete!", "insight")
            except Exception as e:
                add_log(f"❌ Error: {str(e)}", "error")
                st.exception(e)
            finally:
                tracer.log = original_log

# ── Results ───────────────────────────────────────────────────
if "final_state" in st.session_state:
    final_state = st.session_state["final_state"]

    st.markdown("---")
    st.subheader("📊 Final Report")
    st.markdown(final_state["final_report"])

    # Plots
    if final_state.get("generated_plots"):
        st.subheader("📈 Generated Plots")
        plot_cols = st.columns(min(len(final_state["generated_plots"]), 2))
        for i, plot_path in enumerate(final_state["generated_plots"]):
            if os.path.exists(plot_path):
                with plot_cols[i % 2]:
                    st.image(plot_path, use_container_width=True)

    # PDF download
    st.markdown("---")
    st.subheader("📥 Export Report")
    if st.button("Generate PDF Report", type="secondary"):
        with st.spinner("Generating PDF..."):
            pdf_path = generate_pdf_report(
                report_text=final_state["final_report"],
                plots=final_state.get("generated_plots", []),
                output_path="analysis_report.pdf"
            )
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF",
                    data=f,
                    file_name="analysis_report.pdf",
                    mime="application/pdf",
                    type="primary",
                    #use_container_width=True
                )

# ── Follow-up Chat ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("💬 Ask Follow-up Questions")
    st.caption("Chat with the agent — ask questions or request new plots")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "chat_memory" not in st.session_state:
        st.session_state["chat_memory"] = []

    if st.session_state["chat_history"]:
        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                if msg.get("type") == "plot":
                    st.image(msg["content"], use_container_width=True)
                else:
                    st.markdown(msg["content"])

        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state["chat_history"] = []
            st.session_state["chat_memory"] = []
            st.rerun()

    if prompt := st.chat_input("Ask anything or request a plot..."):
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    from config import get_client, MODEL
                    from tools.python_runner import run_python
                    from io import StringIO
                    import pandas as pd

                    client = get_client()

                    # Detect if user wants a plot
                    plot_keywords = ["plot", "chart", "graph", "draw", "visualize",
                                    "histogram", "scatter", "bar", "pie", "heatmap"]
                    wants_plot = any(kw in prompt.lower() for kw in plot_keywords)

                    if wants_plot:
                        # Ask LLM to generate Python code for the plot
                        df = pd.read_json(StringIO(final_state.get("df_json", "")))

                        code_prompt = f"""The user wants a plot. Generate ONLY Python code using matplotlib/seaborn.
The dataframe is called `df` and has these columns: {list(df.columns)}.
User request: {prompt}

Rules:
- Use plt.figure() to create the plot
- Add title and axis labels
- Use print() to describe what the plot shows
- Do NOT call plt.show()
- if you generate a plot, it will be auto-saved and shown to the user, so just focus on generating correct code.
- If the request is ambiguous, ask the user for clarification instead of guessing.
- If you cannot generate a plot, say that you can not and if possible respond with a concise explanation in print() instead."""

                        code_response = client.chat.completions.create(
                            model=MODEL,
                            messages=[{"role": "user", "content": code_prompt}],
                            temperature=0.1,
                            max_tokens=500,
                        )

                        code = code_response.choices[0].message.content.strip()
                        # Strip markdown fences if present
                        if code.startswith("```"):
                            code = code.split("\n", 1)[1].rsplit("```", 1)[0].strip()

                        result = run_python(code, df)

                        if result["plots"]:
                            for plot_path in result["plots"]:
                                if os.path.exists(plot_path):
                                    st.image(plot_path, use_container_width=True)
                                    st.session_state["chat_history"].append({
                                        "role": "assistant",
                                        "content": plot_path,
                                        "type": "plot"
                                    })
                            if result["output"] and result["output"] != "(no printed output)":
                                st.markdown(result["output"])
                                st.session_state["chat_history"].append({
                                    "role": "assistant",
                                    "content": result["output"]
                                })
                        else:
                            msg = result.get("error") or result.get("output") or "Could not generate plot."
                            st.markdown(msg)
                            st.session_state["chat_history"].append({
                                "role": "assistant", "content": msg
                            })

                    else:
                        # Regular follow-up answer
                        system = f"""You are a data analyst assistant. You completed a full analysis and generated this report:

{final_state['final_report']}

Answer the user's follow-up questions based on this report.
Be concise and reference actual numbers from the report when relevant."""

                        st.session_state["chat_memory"].append({
                            "role": "user", "content": prompt
                        })

                        response = client.chat.completions.create(
                            model=MODEL,
                            messages=[{"role": "system", "content": system}] + st.session_state["chat_memory"],
                            temperature=0.3,
                            max_tokens=1000,
                        )

                        answer = response.choices[0].message.content
                        st.session_state["chat_memory"].append({
                            "role": "assistant", "content": answer
                        })
                        st.session_state["chat_history"].append({
                            "role": "assistant", "content": answer
                        })
                        st.markdown(answer)

                except Exception as e:
                    st.error(f"Error: {str(e)}")