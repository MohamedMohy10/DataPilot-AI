import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


def render_plotly_dashboard(df: pd.DataFrame, prompt: str, client, MODEL: str) -> str:
    """
    Generate and render an interactive Plotly dashboard based on user prompt.
    Returns interpretation text.
    """

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist()

    code_prompt = f"""You are a senior data analyst. Generate Python code using Plotly to create an interactive dashboard.

User request: "{prompt}"

DataFrame `df` info:
- Columns: {list(df.columns)}
- Shape: {df.shape}
- Numeric columns: {numeric_cols}
- Categorical columns: {categorical_cols}
- Sample data: {df.head(3).to_dict()}

AVAILABLE LIBRARIES (already imported, use directly):
- import plotly.express as px
- import plotly.graph_objects as go
- from plotly.subplots import make_subplots
- import pandas as pd
- import numpy as np
- df is already in scope

RULES:
- Create meaningful interactive charts relevant to the user request
- Use px.bar, px.scatter, px.histogram, px.box, px.line, px.pie, px.heatmap as appropriate
- For multiple charts: use make_subplots or return multiple figures as a list named `figures`
- Store all figures in a list called `figures = [fig1, fig2, ...]`
- Add proper titles, axis labels, and color coding
- For categorical columns with many values: use top 10-15 only
- Make charts visually clear and informative
- print() a one-line description of what each chart shows
- ONLY return Python code, no explanation"""

    code_response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": code_prompt}],
        temperature=0.1,
        max_tokens=2048,
    )

    code = code_response.choices[0].message.content.strip()
    if "```" in code:
        parts = code.split("```")
        for part in parts:
            cleaned = part.strip()
            if cleaned.startswith("python"):
                cleaned = cleaned[6:].strip()
            if cleaned and any(k in cleaned for k in ["px.", "go.", "fig", "plotly"]):
                code = cleaned
                break

    # Execute the Plotly code
    import io, contextlib
    stdout_buf = io.StringIO()

 # Patch fig.show() to prevent opening browser tabs
    import plotly.basedatatypes as _base
    original_show = _base.BaseFigure.show

    def _blocked_show(self, *args, **kwargs):
        pass  # block browser tab opening

    _base.BaseFigure.show = _blocked_show

    local_scope = {
        "df": df.copy(deep=True),
        "pd": pd,
        "np": np,
        "px": px,
        "go": go,
        "make_subplots": make_subplots,
        "figures": []
    }

    error = None
    try:
        with contextlib.redirect_stdout(stdout_buf):
            exec(compile(code, "<plotly>", "exec"), {}, local_scope)
    except Exception as e:
        error = str(e)
    finally:
        _base.BaseFigure.show = original_show  # always restore
    output = stdout_buf.getvalue().strip()

    # Render figures
    figures = local_scope.get("figures", [])

    # Also check if a single `fig` was created
    if not figures and "fig" in local_scope:
        fig = local_scope["fig"]
        if hasattr(fig, 'data'):
            figures = [fig]

    if figures:
        for fig in figures:
            if hasattr(fig, 'data') and fig.data:
                st.plotly_chart(fig, use_container_width=True)
    elif error:
        st.warning(f"Could not generate interactive chart: {error}")

    # Return interpretation
    interpretation = output if output else "Interactive dashboard generated."
    return interpretation, bool(figures)