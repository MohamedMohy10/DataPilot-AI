import json
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

class AgentTracer:
    """LangSmith-style step tracer for observability."""

    def __init__(self):
        self.trace_log: list[dict] = []

    def log(self, node: str, event: str, data: dict = None):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "node": node,
            "event": event,
            "data": data or {}
        }
        self.trace_log.append(entry)
        self._print(entry)

    def _print(self, entry: dict):
        color_map = {
            "planner": "cyan",
            "executor": "yellow",
            "evaluator": "magenta",
            "memory": "blue",
            "final_answer": "green",
        }
        color = color_map.get(entry["node"], "white")
        console.print(
            f"[{color}][{entry['node'].upper()}][/{color}] "
            f"[dim]{entry['event']}[/dim]"
        )
        if entry["data"].get("code"):
            console.print(Syntax(entry["data"]["code"], "python", theme="monokai"))
        if entry["data"].get("output"):
            console.print(Panel(str(entry["data"]["output"])[:500], title="Output"))

    def dump(self, path: str = "trace.json"):
        with open(path, "w") as f:
            json.dump(self.trace_log, f, indent=2)
        console.print(f"[dim]Trace saved → {path}[/dim]")

tracer = AgentTracer()