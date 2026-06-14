import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os, time
from config import PLOT_OUTPUT_DIR

os.makedirs(PLOT_OUTPUT_DIR, exist_ok=True)


def _save_plot(prefix: str) -> str:
    path = f"{PLOT_OUTPUT_DIR}/{prefix}_{int(time.time()*1000)}.png"
    plt.savefig(path, bbox_inches='tight', dpi=150)
    plt.close('all')
    return path


def _is_blank_plot(path: str) -> bool:
    """Detect blank/empty plots."""
    try:
        from PIL import Image
        import numpy as np
        img = np.array(Image.open(path).convert('L'))
        unique_pixels = len(np.unique(img))
        return unique_pixels < 5  # nearly all same color = blank
    except Exception:
        # fallback: check file size
        return os.path.getsize(path) < 5000


def analyze_missing_values(df: pd.DataFrame) -> dict:
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    result = {
        "has_missing": len(missing) > 0,
        "total_missing_cells": int(df.isnull().sum().sum()),
        "columns_with_missing": {
            col: {
                "count": int(cnt),
                "pct": round(cnt / len(df) * 100, 2)
            }
            for col, cnt in missing.items()
        }
    }
    return result


def analyze_duplicates(df: pd.DataFrame) -> dict:
    dup_count = int(df.duplicated().sum())
    return {
        "duplicate_rows": dup_count,
        "duplicate_pct": round(dup_count / len(df) * 100, 2)
    }


def analyze_numeric_columns(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if not numeric_cols:
        return {}
    desc = df[numeric_cols].describe().round(4)
    skewness = df[numeric_cols].skew().round(4).to_dict()
    return {
        "columns": numeric_cols,
        "descriptive_stats": desc.to_dict(),
        "skewness": skewness
    }


def analyze_categorical_columns(df: pd.DataFrame) -> dict:
    cat_cols = df.select_dtypes(include='object').columns.tolist()
    result = {}
    for col in cat_cols:
        vc = df[col].value_counts()
        result[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": vc.head(10).to_dict(),
            "missing": int(df[col].isnull().sum())
        }
    return result


def detect_outliers(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    result = {}
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = df[(df[col] < lower) | (df[col] > upper)]
        result[col] = {
            "lower_bound": round(float(lower), 4),
            "upper_bound": round(float(upper), 4),
            "outlier_count": len(outliers),
            "outlier_pct": round(len(outliers) / len(df) * 100, 2)
        }
    return result


def analyze_correlations(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if len(numeric_cols) < 2:
        return {}

    corr_matrix = df[numeric_cols].corr(method='pearson').round(4)
    strong_pairs = []
    for i, col1 in enumerate(numeric_cols):
        for col2 in numeric_cols[i+1:]:
            r = corr_matrix.loc[col1, col2]
            if abs(r) >= 0.3:
                n = df[[col1, col2]].dropna().shape[0]
                if n > 2:
                    t_stat = r * np.sqrt((n-2) / (1-r**2))
                    p_val = float(2 * stats.t.sf(abs(t_stat), df=n-2))
                else:
                    p_val = None
                strong_pairs.append({
                    "col1": col1,
                    "col2": col2,
                    "pearson_r": round(float(r), 4),
                    "p_value": round(p_val, 6) if p_val else None
                })

    return {
        "method": "pearson",
        "matrix": corr_matrix.to_dict(),
        "strong_pairs": sorted(strong_pairs, key=lambda x: abs(x["pearson_r"]), reverse=True)
    }


def analyze_target_variable(df: pd.DataFrame, target_col: str) -> dict:
    """Analyze a binary or categorical target variable."""
    if target_col not in df.columns:
        return {}

    result = {
        "target_column": target_col,
        "value_counts": df[target_col].value_counts().to_dict(),
        "value_pcts": df[target_col].value_counts(normalize=True).round(4).mul(100).to_dict(),
    }

    # Chi-square tests against categorical columns
    cat_cols = df.select_dtypes(include='object').columns.tolist()
    chi2_results = []
    for col in cat_cols:
        if col == target_col:
            continue
        try:
            ct = pd.crosstab(df[col], df[target_col])
            chi2, p, dof, _ = stats.chi2_contingency(ct)
            chi2_results.append({
                "column": col,
                "chi2": round(float(chi2), 4),
                "p_value": round(float(p), 6),
                "dof": int(dof),
                "significant": p < 0.05
            })
        except Exception:
            pass

    # T-tests against numeric columns
    ttest_results = []
    target_vals = df[target_col].unique()
    if len(target_vals) == 2:
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        for col in numeric_cols:
            try:
                g1 = df[df[target_col] == target_vals[0]][col].dropna()
                g2 = df[df[target_col] == target_vals[1]][col].dropna()
                t_stat, p_val = stats.ttest_ind(g1, g2)
                ttest_results.append({
                    "column": col,
                    "group1": str(target_vals[0]),
                    "group1_mean": round(float(g1.mean()), 4),
                    "group2": str(target_vals[1]),
                    "group2_mean": round(float(g2.mean()), 4),
                    "t_statistic": round(float(t_stat), 4),
                    "p_value": round(float(p_val), 6),
                    "significant": p_val < 0.05
                })
            except Exception:
                pass

    result["chi2_tests"] = sorted(chi2_results, key=lambda x: x["p_value"])
    result["ttest_results"] = sorted(ttest_results, key=lambda x: x["p_value"])
    return result


def run_statistical_tests(df: pd.DataFrame) -> dict:
    """Run correlation significance tests on all numeric pairs."""
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    results = []
    for i, col1 in enumerate(numeric_cols):
        for col2 in numeric_cols[i+1:]:
            try:
                clean = df[[col1, col2]].dropna()
                r, p = stats.pearsonr(clean[col1], clean[col2])
                results.append({
                    "col1": col1, "col2": col2,
                    "test": "pearson",
                    "statistic": round(float(r), 4),
                    "p_value": round(float(p), 6),
                    "significant": p < 0.05
                })
            except Exception:
                pass
    return {"pearson_tests": results}


def generate_visualizations(df: pd.DataFrame, target_col: str = None) -> list[str]:
    """Generate an intelligent visualization suite based on data types."""
    plots = []
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(include='object').columns.tolist()

    # 1. Missing value heatmap
    if df.isnull().sum().sum() > 0:
        try:
            plt.figure(figsize=(10, 6))
            sns.heatmap(df.isnull(), yticklabels=False, cbar=True, cmap='viridis')
            plt.title('Missing Values Heatmap')
            plt.tight_layout()
            path = _save_plot('missing_heatmap')
            if not _is_blank_plot(path):
                plots.append(path)
        except Exception:
            plt.close('all')

    # 2. Correlation heatmap
    if len(numeric_cols) >= 2:
        try:
            plt.figure(figsize=(12, 8))
            corr = df[numeric_cols].corr()
            mask = np.triu(np.ones_like(corr, dtype=bool))
            sns.heatmap(corr, mask=mask, annot=True, fmt='.2f',
                       cmap='RdYlGn', center=0, square=True)
            plt.title('Correlation Heatmap')
            plt.tight_layout()
            path = _save_plot('correlation_heatmap')
            if not _is_blank_plot(path):
                plots.append(path)
        except Exception:
            plt.close('all')

    # 3. Target variable analysis
    if target_col and target_col in df.columns:
        # Target distribution
        try:
            plt.figure(figsize=(8, 5))
            vc = df[target_col].value_counts()
            ax = sns.barplot(x=vc.index.astype(str), y=vc.values)
            for p in ax.patches:
                ax.annotate(f'{int(p.get_height())} ({p.get_height()/len(df)*100:.1f}%)',
                           (p.get_x() + p.get_width()/2., p.get_height()),
                           ha='center', va='bottom')
            plt.title(f'{target_col} Distribution')
            plt.xlabel(target_col)
            plt.ylabel('Count')
            plt.tight_layout()
            path = _save_plot('target_distribution')
            if not _is_blank_plot(path):
                plots.append(path)
        except Exception:
            plt.close('all')

        # Target vs categorical columns (top 4 most significant)
        for col in cat_cols[:4]:
            if col == target_col:
                continue
            try:
                plt.figure(figsize=(10, 5))
                ct = pd.crosstab(df[col], df[target_col], normalize='index') * 100
                ct.plot(kind='bar', ax=plt.gca(), colormap='Set2')
                plt.title(f'{target_col} Rate by {col} (%)')
                plt.xlabel(col)
                plt.ylabel('Percentage')
                plt.xticks(rotation=45, ha='right')
                plt.legend(title=target_col)
                plt.tight_layout()
                path = _save_plot(f'target_by_{col}')
                if not _is_blank_plot(path):
                    plots.append(path)
            except Exception:
                plt.close('all')

        # Target vs numeric columns (box plots, top 4)
        for col in numeric_cols[:4]:
            try:
                plt.figure(figsize=(8, 5))
                df.boxplot(column=col, by=target_col, ax=plt.gca())
                plt.title(f'{col} by {target_col}')
                plt.suptitle('')
                plt.xlabel(target_col)
                plt.ylabel(col)
                plt.tight_layout()
                path = _save_plot(f'{col}_by_target')
                if not _is_blank_plot(path):
                    plots.append(path)
            except Exception:
                plt.close('all')

    else:
        # No target — numeric distributions
        cols_to_plot = numeric_cols[:6]
        if cols_to_plot:
            try:
                n = len(cols_to_plot)
                fig, axes = plt.subplots(2, (n+1)//2, figsize=(14, 8))
                axes = axes.flatten()
                for i, col in enumerate(cols_to_plot):
                    axes[i].hist(df[col].dropna(), bins=30, edgecolor='black', color='steelblue')
                    axes[i].set_title(col)
                    axes[i].set_xlabel(col)
                    axes[i].set_ylabel('Frequency')
                for j in range(i+1, len(axes)):
                    axes[j].set_visible(False)
                plt.suptitle('Numeric Distributions')
                plt.tight_layout()
                path = _save_plot('numeric_distributions')
                if not _is_blank_plot(path):
                    plots.append(path)
            except Exception:
                plt.close('all')

        # Top categorical bar charts
        for col in cat_cols[:3]:
            try:
                plt.figure(figsize=(10, 5))
                vc = df[col].value_counts().head(15)
                sns.barplot(x=vc.values, y=vc.index.astype(str))
                plt.title(f'Top Values — {col}')
                plt.xlabel('Count')
                plt.ylabel(col)
                plt.tight_layout()
                path = _save_plot(f'categorical_{col}')
                if not _is_blank_plot(path):
                    plots.append(path)
            except Exception:
                plt.close('all')

    return plots


def detect_target_column(df: pd.DataFrame) -> str | None:
    """Auto-detect binary target column."""
    binary_candidates = []
    for col in df.columns:
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) == 2:
            binary_candidates.append(col)

    # Common target column names
    target_keywords = ['target', 'label', 'attrition', 'churn', 'survived',
                       'outcome', 'default', 'fraud', 'class', 'y']
    for col in df.columns:
        if col.lower() in target_keywords:
            return col
    for col in binary_candidates:
        for kw in target_keywords:
            if kw in col.lower():
                return col

    return binary_candidates[0] if binary_candidates else None


def build_analysis_results(df: pd.DataFrame) -> dict:
    """Run full analysis pipeline and return structured results."""
    target_col = detect_target_column(df)

    results = {
        "dataset_summary": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict()
        },
        "missing_values": analyze_missing_values(df),
        "duplicates": analyze_duplicates(df),
        "numeric_summary": analyze_numeric_columns(df),
        "categorical_summary": analyze_categorical_columns(df),
        "outliers": detect_outliers(df),
        "correlations": analyze_correlations(df),
        "target_analysis": analyze_target_variable(df, target_col) if target_col else {},
        "statistical_tests": run_statistical_tests(df),
        "plots": generate_visualizations(df, target_col),
        "insights": [],
        "target_column": target_col
    }

    return results