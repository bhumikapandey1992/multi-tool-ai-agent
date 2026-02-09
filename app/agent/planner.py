def create_plan_rulebased(task: str, has_file: bool = False) -> list[str]:
    """
    Convert a user task into high-level execution steps (rule-based fallback).

    `has_file` allows the caller to inform the planner whether a CSV was uploaded.
    """

    task_lower = task.lower()
    steps: list[str] = []

    wants_summary = (
        "summarize" in task_lower
        or "summary" in task_lower
        or "stats" in task_lower
        or "statistics" in task_lower
        or "describe" in task_lower
        or "profile" in task_lower
        or "overview" in task_lower
    )
    wants_cleaning = "clean" in task_lower
    mentions_csv = "csv" in task_lower

    # If a CSV is mentioned or a file is uploaded, plan CSV-related steps
    if mentions_csv or has_file:
        steps.append("Load the CSV file")

        if "missing" in task_lower:
            steps.append("Detect missing values")

        if wants_summary:
            steps.append("Generate summary statistics")

    # If no file context but user explicitly wants summary
    elif wants_summary:
        steps.append("Generate summary statistics")

    # Fallback when nothing matches
    if not steps:
        steps.append("Analyze the task")
        steps.append("Execute the task")

    return steps
