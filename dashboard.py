import streamlit as st
import pandas as pd
import numpy as np
import re
from io import StringIO


def extract_metrics(report_text: str) -> list[dict]:
    """Extract key numbers from the report for KPI cards."""
    metrics = []

    patterns = [
        (r'(\d+[\,\d]*)\s*rows?', 'Total Rows', ''),
        (r'(\d+)\s*columns?', 'Total Columns', ''),
        (r'(\d+\.?\d*)\s*%\s*survival', 'Survival Rate', '%'),
        (r'overall.*?(\d+\.?\d*)\s*%', 'Overall Rate', '%'),
        (r'mean.*?[\$£]?\s*(\d+[\,\d]*\.?\d*)', 'Mean Value', ''),
        (r'median.*?[\$£]?\s*(\d+[\,\d]*\.?\d*)', 'Median Value', ''),
        (r'missing.*?(\d+\.?\d*)\s*%', 'Missing Data', '%'),
        (r'(\d+\.?\d*)\s*%.*?surviv', 'Survival Rate', '%'),
        (r'r\s*=\s*([+-]?\d+\.?\d+)', 'Top Correlation (r)', ''),
        (r'accuracy.*?(\d+\.?\d*)\s*%', 'Accuracy', '%'),
    ]

    seen_labels = set()
    for pattern, label, unit in patterns:
        if label in seen_labels:
            continue
        match = re.search(pattern, report_text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '')
            try:
                num = float(value)
                metrics.append({
                    "label": label,
                    "value": f"{num:,.1f}{unit}" if '.' in value else f"{int(num):,}{unit}"
                })
                seen_labels.add(label)
            except ValueError:
                pass
        if len(metrics) >= 4:
            break

    return metrics


def render_static_dashboard(final_state: dict):
    """Render automatic static dashboard from analysis results."""

    st.markdown("---")
    st.subheader("📊 Analysis Dashboard")

    report = final_state.get("final_report", "")
    plots = final_state.get("generated_plots", [])
    df_json = final_state.get("df_json", "")
    columns = final_state.get("df_columns", [])
    shape = final_state.get("df_shape", (0, 0))
    insights = final_state.get("accumulated_insights", [])

    # ── KPI Cards ─────────────────────────────────────────────
    st.markdown("#### 📌 Key Metrics")

    # Always-available metrics
    kpi_data = [
        {"label": "Total Rows", "value": f"{shape[0]:,}"},
        {"label": "Total Columns", "value": str(shape[1])},
        {"label": "Insights Found", "value": str(len(insights))},
        {"label": "Plots Generated", "value": str(len(plots))},
    ]

    # Try to extract more from report
    extracted = extract_metrics(report)
    for e in extracted:
        if e["label"] not in [k["label"] for k in kpi_data]:
            kpi_data.append(e)

    # Render KPI cards
    cols = st.columns(min(len(kpi_data), 4))
    for i, kpi in enumerate(kpi_data[:4]):
        with cols[i]:
            st.metric(label=kpi["label"], value=kpi["value"])

    # ── Dataset Overview ──────────────────────────────────────
    if df_json:
        try:
            df = pd.read_json(StringIO(df_json))

            with st.expander("📋 Dataset Overview", expanded=False):
                tab1, tab2, tab3 = st.tabs(["Sample Data", "Statistics", "Missing Values"])

                with tab1:
                    st.dataframe(df.head(10), use_container_width=True)

                with tab2:
                    numeric_df = df.select_dtypes(include='number')
                    if not numeric_df.empty:
                        st.dataframe(
                            numeric_df.describe().round(3),
                            use_container_width=True
                        )

                with tab3:
                    missing = df.isnull().sum()
                    missing_pct = (missing / len(df) * 100).round(2)
                    missing_df = pd.DataFrame({
                        'Missing Count': missing,
                        'Missing %': missing_pct
                    }).sort_values('Missing Count', ascending=False)
                    missing_df = missing_df[missing_df['Missing Count'] > 0]
                    if missing_df.empty:
                        st.success("✅ No missing values found")
                    else:
                        st.dataframe(missing_df, use_container_width=True)

        except Exception:
            pass

    # ── Key Insights ──────────────────────────────────────────
    if insights:
        with st.expander("💡 Key Insights", expanded=True):
            for i, insight in enumerate(insights, 1):
                st.markdown(f"**{i}.** {insight}")

    # ── Generated Plots Grid ──────────────────────────────────
    if plots:
        import os
        valid_plots = [p for p in plots if os.path.exists(p)]

        if valid_plots:
            st.markdown("#### 📈 Visualizations")

            # Render in 2-column grid
            for i in range(0, len(valid_plots), 2):
                cols = st.columns(2)
                with cols[0]:
                    st.image(valid_plots[i], use_container_width=True)
                if i + 1 < len(valid_plots):
                    with cols[1]:
                        st.image(valid_plots[i + 1], use_container_width=True)