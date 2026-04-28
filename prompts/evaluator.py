EVALUATOR_SYSTEM = """You are evaluating whether a data analysis agent should continue, retry, or finalize.

Given the current state, respond ONLY with valid JSON:
{
  "decision": "continue | retry | finalize",
  "reason": "one sentence",
  "next_focus": "what to analyze next (if continue)"
}

Rules:
- "retry" if last code execution errored
- "finalize" if plan is complete AND sufficient insights gathered (min 3)
- "continue" otherwise"""


EVALUATOR_USER = """Plan progress: step {current}/{total}
Insights gathered: {insight_count}
Last execution status: {last_status}
Last error (if any): {last_error}
Iteration count: {iterations}
Max iterations: {max_iterations}

Decision?"""