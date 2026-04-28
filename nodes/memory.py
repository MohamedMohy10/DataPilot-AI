from state import AnalystState
from observability.tracer import tracer

def memory_node(state: AnalystState) -> AnalystState:
    """Advance to next step or stay on current for retry."""
    decision = state["evaluation_decision"]

    tracer.log("memory", f"State update — decision: {decision}")

    if decision == "retry":
        # Stay on same step, reset retry counter
        return {**state, "retry_count": 0}
    elif decision == "continue":
        next_index = state["current_step_index"] + 1
        return {**state, "current_step_index": next_index, "retry_count": 0}
    else:
        # finalize — don't advance
        return state