class SessionMemory:
    """Short-term memory for the current analysis session."""

    def __init__(self):
        self.steps: list[dict] = []
        self.insights: list[str] = []
        self.plots: list[str] = []
        self.errors: list[str] = []

    def record_step(self, step: int, tool: str, code: str, result: dict, insight: str):
        self.steps.append({
            "step": step,
            "tool": tool,
            "code": code,
            "result_status": result.get("status"),
            "output_preview": str(result.get("output", ""))[:300],
            "insight": insight,
        })

    def get_context_summary(self) -> str:
        """Returns a compact summary for injection into LLM context."""
        if not self.steps:
            return "No steps executed yet."
        lines = []
        for s in self.steps:
            lines.append(
                f"Step {s['step']} [{s['tool']}] → {s['result_status']}: "
                f"{s['output_preview']}\nInsight: {s['insight']}"
            )
        return "\n\n".join(lines)

    def get_all_insights(self) -> list[str]:
        return [s["insight"] for s in self.steps if s["insight"]]