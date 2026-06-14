from state import AnalystState
from observability.tracer import tracer

def memory_node(state: AnalystState) -> AnalystState:
    decision = state["evaluation_decision"]

    tracer.log("memory", f"State update — decision: {decision}")

    if decision == "retry":
        return {**state, "retry_count": 0}
    elif decision == "continue":
        next_index = state["current_step_index"] + 1
        # ← add this: force finalize if we've exceeded the plan
        if next_index >= len(state["plan"]):
            return {**state, "current_step_index": next_index,
                    "retry_count": 0, "evaluation_decision": "finalize"}
        return {**state, "current_step_index": next_index, "retry_count": 0}
    else:
        return state