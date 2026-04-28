import pandas as pd
import json

def analyze_dataframe(df: pd.DataFrame) -> dict:
    """Generate a full EDA profile of the dataframe."""
    profile = {
        "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        "columns": {},
        "missing_values": {},
        "duplicates": int(df.duplicated().sum()),
        "numeric_summary": {},
        "correlations": {},
        "sample": df.head(3).to_dict(orient="records"),
    }

    # Column types and missing
    for col in df.columns:
        profile["columns"][col] = str(df[col].dtype)
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            profile["missing_values"][col] = {
                "count": null_count,
                "pct": round(null_count / len(df) * 100, 2)
            }

    # Numeric summary
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        profile["numeric_summary"] = json.loads(
            df[numeric_cols].describe().round(3).to_json()
        )

    # Correlations
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr().round(3)
        # Return only strong correlations (abs > 0.5)
        strong = {}
        for i, col1 in enumerate(corr.columns):
            for col2 in corr.columns[i+1:]:
                val = corr.loc[col1, col2]
                if abs(val) > 0.5:
                    strong[f"{col1} ↔ {col2}"] = float(val)
        profile["correlations"] = strong

    return profile