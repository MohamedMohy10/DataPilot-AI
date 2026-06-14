from langgraph.graph import StateGraph, END
from state import AnalystState
from nodes.planner import planner_node
from nodes.executor import executor_node
from nodes.evaluator import evaluator_node
from nodes.memory import memory_node
from nodes.final_answer import final_answer_node

def route_after_evaluation(state: AnalystState) -> str:
    decision = state["evaluation_decision"]
    if decision == "finalize":
        return "final_answer"
    else:
        return "memory"

def route_after_memory(state: AnalystState) -> str:
    """After memory update, check if we should finalize or continue executing."""
    if state["evaluation_decision"] == "finalize":
        return "final_answer"
    return "executor"

def build_graph() -> StateGraph:
    graph = StateGraph(AnalystState)

    # Register nodes
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("memory", memory_node)
    graph.add_node("final_answer", final_answer_node)

    # Edges
    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "evaluator")

    # Conditional routing after evaluation
    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {
            "memory": "memory",
            "final_answer": "final_answer",
        }
    )

    # Memory always loops back to executor
    # ✅ new
    graph.add_conditional_edges(
        "memory",
        route_after_memory,
        {
            "executor": "executor",
            "final_answer": "final_answer"
        }
    )

    # Final answer ends the graph
    graph.add_edge("final_answer", END)

    return graph.compile()