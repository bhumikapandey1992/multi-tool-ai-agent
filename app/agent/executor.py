from typing import List, Optional, Tuple
from fastapi import UploadFile
from app.agent.tools import TOOL_REGISTRY, TOOL_ALIASES
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


def _find_best_matching_tool(step: str, registry: dict) -> Optional[str]:
    """
    Find the best matching tool from the registry for a given plan step.
    Uses fuzzy string matching to handle variations in wording.

    Args:
        step: The plan step (e.g., "Generate summary stats", "Check for missing data")
        registry: The tool registry dictionary

    Returns:
        The best matching tool name from registry, or None if no good match found
    """
    if not registry:
        return None

    step_lower = step.lower()

    # 1) Exact or alias keyword match
    best_alias_match = None
    best_alias_len = 0
    for tool_name in registry.keys():
        if step_lower == tool_name.lower():
            return tool_name
        for alias in TOOL_ALIASES.get(tool_name, []):
            if alias in step_lower and len(alias) > best_alias_len:
                best_alias_match = tool_name
                best_alias_len = len(alias)

    if best_alias_match:
        logger.info(f"Matched step '{step}' to tool '{best_alias_match}' via alias")
        return best_alias_match
    best_match = None
    best_score = 0.0
    threshold = 0.5  # Minimum similarity score (0-1)

    for tool_name in registry.keys():
        tool_name_lower = tool_name.lower()
        # Calculate similarity ratio between step and tool name
        similarity = SequenceMatcher(None, step_lower, tool_name_lower).ratio()

        logger.debug(f"Comparing '{step}' to '{tool_name}': similarity={similarity:.2f}")

        if similarity > best_score and similarity >= threshold:
            best_score = similarity
            best_match = tool_name

    if best_match:
        logger.info(f"Matched step '{step}' to tool '{best_match}' (score: {best_score:.2f})")
    else:
        logger.warning(f"Could not find matching tool for step: '{step}'")

    return best_match


def execute_plan(
        plan: List[str],
        file: Optional[UploadFile]
) -> Tuple[str, list]:
    """
    Execute a planned sequence of steps using registered tools.

    Uses intelligent matching to map plan steps to available tools,
    rather than hardcoded keyword matching.

    Returns:
        result (str): final output produced by the agent
        tool_calls (list): structured log of tool executions
    """

    tool_calls: list = []
    result: str = ""

    for step in plan:
        # Find the best matching tool for this step
        matched_tool_name = _find_best_matching_tool(step, TOOL_REGISTRY)

        if matched_tool_name is None:
            # No suitable tool found for this step
            logger.warning(f"No matching tool found for plan step: {step}")
            tool_calls.append({
                "tool_name": step,
                "arguments": {},
                "status": "skipped",
                "reason": "no_matching_tool",
                "error": f"Could not map '{step}' to any available tool"
            })
            continue

        tool = TOOL_REGISTRY.get(matched_tool_name)

        # Tool should exist since we got it from the registry
        if tool is None:
            tool_calls.append({
                "tool_name": matched_tool_name,
                "arguments": {},
                "status": "error",
                "error": "tool_not_found"
            })
            result = f"Requested tool '{matched_tool_name}' not available"
            continue

        # Check if file is required
        # File-requiring tools should work with UploadFile
        if file is None:
            tool_calls.append({
                "tool_name": matched_tool_name,
                "arguments": {},
                "status": "skipped",
                "reason": "no_file_provided",
                "error": f"Tool '{matched_tool_name}' requires a file, but none was provided"
            })
            result = f"No file provided for {matched_tool_name}"
            continue

        # Ensure the file pointer is at the start for this tool
        try:
            if hasattr(file, "file") and hasattr(file.file, "seek"):
                file.file.seek(0)
        except Exception as e:
            logger.warning(f"Could not seek file: {e}")

        # Execute tool safely
        try:
            logger.info(f"Executing tool: {matched_tool_name}")
            output = tool(file)
            tool_calls.append({
                "tool_name": matched_tool_name,
                "arguments": {},
                "status": "success"
            })
            result = output
            logger.info(f"Tool {matched_tool_name} executed successfully")
        except Exception as e:
            logger.error(f"Error executing tool {matched_tool_name}: {e}")
            tool_calls.append({
                "tool_name": matched_tool_name,
                "arguments": {},
                "status": "error",
                "error": str(e)
            })
            result = f"Error running tool '{matched_tool_name}': {e}"

    # End of plan loop — return collected results
    return result, tool_calls
