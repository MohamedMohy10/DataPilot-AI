TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": (
                "Execute Python code against the dataframe `df`. "
                "Use print() to output results. "
                "Use plt to create plots — they are auto-saved. "
                "df (pandas DataFrame) is always in scope."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Valid Python code. df is in scope. Always print results."
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Why you are running this code — what you expect to find."
                    }
                },
                "required": ["code", "rationale"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_dataframe",
            "description": "Run automatic EDA on the full dataset. Call this first before any analysis.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_insight",
            "description": "Record a key insight discovered from executed results. Call after each analysis step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "insight": {
                        "type": "string",
                        "description": "A specific, data-backed insight. Must reference actual numbers from results."
                    }
                },
                "required": ["insight"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finalize",
            "description": "Call this when analysis is complete and you are ready to write the final report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why the analysis is complete."
                    }
                },
                "required": ["reason"]
            }
        }
    }
]