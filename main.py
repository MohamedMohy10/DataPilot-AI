import os
from rich.console import Console
from rich.markdown import Markdown
from graph import build_graph
from observability.tracer import tracer
from config import PLOT_OUTPUT_DIR, MODEL

console = Console()
print("KEY FOUND:", bool(os.getenv("NVIDIA_API_KEY")))
def main():
    console.print("\n[bold cyan]🤖 Agentic Data Analyst[/bold cyan]")
    console.print(f"[dim]LangGraph + {MODEL}[/dim]\n")

    dataset_path = input("CSV path: ").strip()
    query = input("Your question: ").strip()

    if not os.path.exists(dataset_path):
        console.print("[red]File not found.[/red]")
        return

    initial_state = {
        "user_query": query,
        "dataset_path": dataset_path,
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
        "analysis_results": {},
    }

    console.print("\n[bold yellow]Starting agent...[/bold yellow]\n")

    graph = build_graph()
    final_state = graph.invoke(initial_state)

    console.print("\n" + "─" * 60)
    console.print("[bold green]📊 FINAL REPORT[/bold green]\n")
    console.print(Markdown(final_state["final_report"]))

    if final_state["generated_plots"]:
        console.print(f"\n[dim]Plots saved → {PLOT_OUTPUT_DIR}/[/dim]")
        for p in final_state["generated_plots"]:
            console.print(f"  • {p}")

    tracer.dump("trace.json")

if __name__ == "__main__":
    main()