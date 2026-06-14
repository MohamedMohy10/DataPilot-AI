from typing import TypedDict, Annotated, Any
from langgraph.graph.message import add_messages

class AnalystState(TypedDict):
    # Input
    user_query: str
    dataset_path: str

    # Data
    df_profile: dict
    df_columns: list[str]
    df_shape: tuple
    df_json: str                        # ← persisted df across steps

    # Planning
    plan: list[dict]
    current_step_index: int

    # Execution
    messages: Annotated[list, add_messages]
    generated_code: str
    execution_result: dict
    retry_count: int

    # Memory
    step_history: list[dict]
    accumulated_insights: list[str]
    generated_plots: list[str]

    # Control
    evaluation_decision: str
    iteration_count: int

    # Output
    final_report: str
    analysis_results: dict  