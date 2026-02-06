from typing import List, Optional, Tuple
from fastapi import UploadFile
from app.agent.tools import TOOL_REGISTRY


def execute_plan(
        plan: List[str],
        file: Optional[UploadFile]
) -> Tuple[str, list]:
    """
    Execute a planned sequence of steps using registered tools.

    Returns:
        result (str): final output produced by the agent
        tool_calls (list): structured log of tool executions
    """

    tool_calls: list = []
    result: str = ""

    for step in plan:
        step_lower = step.lower()

        # ============================================================
        # Generate Summary Statistics
        # ============================================================
        if "summary statistics" in step_lower:
            tool_name = "Generate summary statistics"
            tool = TOOL_REGISTRY.get(tool_name)

            # Tool missing from registry
            if tool is None:
                tool_calls.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "status": "error",
                    "error": "tool_not_found"
                })
                result = "Requested tool not available"
                continue

            # File required but not provided
            if file is None:
                tool_calls.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "status": "skipped",
                    "reason": "no_file_provided"
                })
                result = "No file provided for generating summary statistics"
                continue

            # Ensure the file pointer is at the start for this tool
            try:
                if hasattr(file, "file") and hasattr(file.file, "seek"):
                    file.file.seek(0)
            except Exception:
                # non-fatal: if we can't rewind, proceed and let the tool handle errors
                pass

            # Execute tool safely
            try:
                output = tool(file)
                tool_calls.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "status": "success"
                })
                result = output
            except Exception as e:
                tool_calls.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "status": "error",
                    "error": str(e)
                })
                result = f"Error running tool: {e}"

        # ============================================================
        # Detect Missing Values
        # ============================================================
        elif "missing values" in step_lower or "missing" in step_lower:
            tool_name = "Detect missing values"
            tool = TOOL_REGISTRY.get(tool_name)

            if tool is None:
                tool_calls.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "status": "error",
                    "error": "tool_not_found"
                })
                result = "Missing-values tool not available"
                continue

            if file is None:
                tool_calls.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "status": "skipped",
                    "reason": "no_file_provided"
                })
                result = "No file provided to detect missing values"
                continue

            # Rewind file pointer before calling tool
            try:
                if hasattr(file, "file") and hasattr(file.file, "seek"):
                    file.file.seek(0)
            except Exception:
                pass

            try:
                output = tool(file)
                tool_calls.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "status": "success"
                })
                result = output
            except Exception as e:
                tool_calls.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "status": "error",
                    "error": str(e)
                })
                result = f"Error detecting missing values: {e}"

    # End of plan loop — return collected results
    return result, tool_calls