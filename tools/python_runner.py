import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io, traceback, contextlib, os, hashlib
from config import PLOT_OUTPUT_DIR

os.makedirs(PLOT_OUTPUT_DIR, exist_ok=True)


def run_python(code: str, df: pd.DataFrame) -> dict:
    """
    Safely execute Python code with df in scope.
    Each call gets its own plot counter and hash tracker — no globals.
    """
    stdout_buf = io.StringIO()
    plots_generated = []
    saved_hashes = set()      # ← per-call, not global
    plot_counter = [0]        # ← per-call, not global

    def save_plot_if_new():
        """Save any open figure if it hasn't been saved before."""
        if not plt.get_fignums():
            return
        for fig_num in plt.get_fignums():
            fig = plt.figure(fig_num)
            # Hash the figure content
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            buf.seek(0)
            plot_hash = hashlib.md5(buf.read()).hexdigest()

            if plot_hash not in saved_hashes:
                saved_hashes.add(plot_hash)
                plot_counter[0] += 1
                # Use timestamp in name to avoid collisions across steps
                import time
                path = f"{PLOT_OUTPUT_DIR}/plot_{int(time.time()*1000)}_{plot_counter[0]}.png"
                fig.savefig(path, bbox_inches='tight', dpi=150)
                plots_generated.append(path)

            plt.close(fig)

    # Patch plt.show to auto-save instead of display
    original_show = plt.show
    plt.show = lambda *a, **kw: save_plot_if_new()

    local_scope = {
        "df": df.copy(),
        "pd": pd,
        "np": np,
        "plt": plt,
        "sns": sns,
    }

    try:
        with contextlib.redirect_stdout(stdout_buf):
            exec(compile(code, "<agent>", "exec"), {}, local_scope)

        # Catch any plots that didn't call show()
        save_plot_if_new()

        output = stdout_buf.getvalue().strip() or "(no printed output)"
        return {
            "status": "success",
            "output": output,
            "error": None,
            "plots": plots_generated,
            "local_scope": local_scope   # ← return scope for df mutation capture
        }

    except Exception:
        save_plot_if_new()
        return {
            "status": "error",
            "output": None,
            "error": traceback.format_exc(),
            "plots": plots_generated,
            "local_scope": local_scope
        }

    finally:
        plt.show = original_show