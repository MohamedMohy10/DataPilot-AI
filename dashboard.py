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
    st.markdown("---")
    st.subheader("📊 Analysis Dashboard")

    analysis = final_state.get("analysis_results", {})
    plots = final_state.get("generated_plots", [])
    insights = analysis.get("insights", []) or final_state.get("accumulated_insights", [])

    summary = analysis.get("dataset_summary", {})
    missing = analysis.get("missing_values", {})
    duplicates = analysis.get("duplicates", {})
    correlations = analysis.get("correlations", {})
    target = analysis.get("target_analysis", {})

    # ── KPI Cards — from structured results only ───────────────
    st.markdown("#### 📌 Key Metrics")

    kpi_data = [
        {"label": "Total Rows", "value": f"{summary.get('rows', 0):,}"},
        {"label": "Total Columns", "value": str(summary.get('columns', 0))},
        {"label": "Missing Cells", "value": str(missing.get('total_missing_cells', 0))},
        {"label": "Duplicate Rows", "value": str(duplicates.get('duplicate_rows', 0))},
    ]

    if target:
        target_col = target.get("target_column", "")
        value_pcts = target.get("value_pcts", {})
        if value_pcts:
            top_val = list(value_pcts.keys())[0]
            top_pct = list(value_pcts.values())[0]
            kpi_data.append({
                "label": f"{target_col}: {top_val}",
                "value": f"{top_pct:.1f}%"
            })

    strong_pairs = correlations.get("strong_pairs", [])
    if strong_pairs:
        top = strong_pairs[0]
        kpi_data.append({
            "label": f"Top Correlation",
            "value": f"r={top['pearson_r']}"
        })

    cols = st.columns(min(len(kpi_data), 4))
    for i, kpi in enumerate(kpi_data[:4]):
        with cols[i]:
            st.metric(label=kpi["label"], value=kpi["value"])

    if len(kpi_data) > 4:
        cols2 = st.columns(min(len(kpi_data) - 4, 4))
        for i, kpi in enumerate(kpi_data[4:8]):
            with cols2[i]:
                st.metric(label=kpi["label"], value=kpi["value"])

    # ── Dataset Overview ──────────────────────────────────────
    df_json = final_state.get("df_json", "")
    if df_json:
        try:
            import pandas as pd
            from io import StringIO
            df = pd.read_json(StringIO(df_json))

            with st.expander("📋 Dataset Overview", expanded=False):
                tab1, tab2, tab3 = st.tabs(["Sample Data", "Statistics", "Missing Values"])

                with tab1:
                    st.dataframe(df.head(10), use_container_width=True)

                with tab2:
                    numeric_df = df.select_dtypes(include='number')
                    if not numeric_df.empty:
                        st.dataframe(numeric_df.describe().round(3), use_container_width=True)

                with tab3:
                    cols_missing = missing.get("columns_with_missing", {})
                    if not cols_missing:
                        st.success("✅ No missing values found")
                    else:
                        missing_df = pd.DataFrame(cols_missing).T
                        st.dataframe(missing_df, use_container_width=True)
        except Exception:
            pass

    # ── Statistical Results ───────────────────────────────────
    if strong_pairs:
        with st.expander("📐 Strong Correlations (Pearson)", expanded=False):
            import pandas as pd
            corr_df = pd.DataFrame(strong_pairs)
            st.dataframe(corr_df, use_container_width=True)

    if target:
        ttest = target.get("ttest_results", [])
        chi2 = target.get("chi2_tests", [])

        if ttest:
            with st.expander("📊 T-Test Results vs Target", expanded=False):
                import pandas as pd
                st.dataframe(pd.DataFrame(ttest), use_container_width=True)

        if chi2:
            with st.expander("📊 Chi-Square Tests vs Target", expanded=False):
                import pandas as pd
                st.dataframe(pd.DataFrame(chi2), use_container_width=True)

    # ── Key Insights ──────────────────────────────────────────
    if insights:
        with st.expander("💡 Key Insights", expanded=True):
            for i, insight in enumerate(insights, 1):
                st.markdown(f"**{i}.** {insight}")

    # ── Generated Plots Grid ──────────────────────────────────
    import os
    valid_plots = [p for p in plots if os.path.exists(p)]

    if valid_plots:
        st.markdown("#### 📈 Visualizations")
        for i in range(0, len(valid_plots), 2):
            cols = st.columns(2)
            with cols[0]:
                st.image(valid_plots[i], use_container_width=True)
            if i + 1 < len(valid_plots):
                with cols[1]:
                    st.image(valid_plots[i + 1], use_container_width=True)