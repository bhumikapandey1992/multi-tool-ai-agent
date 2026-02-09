import os
import json
import re
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def _extract_json(text: str) -> str:
    """Try to extract the first JSON object from text."""
    # Find first '{' and matching '}' naive approach
    start = text.find('{')
    if start == -1:
        raise ValueError('No JSON object found in LLM response')
    # Try to find a matching closing brace by simple scanning
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    # Fallback: return substring from first brace to end
    return text[start:]


def plan_via_llm(task: str, has_file: bool = False, model: str = 'gpt-4') -> Dict[str, Any]:
    """
    Call the OpenAI Chat API to produce a structured plan JSON object.

    Returns a dict with at least:
      {"plan": ["step1", "step2", ...], "tool_calls": [{"tool_name": "...", "arguments": {...}}, ...]}

    Raises Exception on any failure (network, parsing, missing API key).
    """
    if not OPENAI_API_KEY:
        raise EnvironmentError('OPENAI_API_KEY not set in environment')

    try:
        from openai import OpenAI
    except ImportError as e:
        raise ImportError('The openai package is required for the LLM planner. Please install `openai` in your environment.') from e

    # Initialize the modern OpenAI client (v1.0+)
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Get available tools from the registry
    try:
        from app.agent.tools import TOOL_REGISTRY
        available_tools = list(TOOL_REGISTRY.keys())
        tools_info = ", ".join(available_tools) if available_tools else "No tools available"
    except Exception:
        available_tools = []
        tools_info = "Unable to load tool registry"

    # Compose an instruction that requires JSON-only output
    system_prompt = (
        "You are an assistant that converts a user's plain-English task into a structured execution plan. "
        "Respond ONLY with a single valid JSON object and nothing else. The JSON must contain the keys:"
        " 'plan' (an array of short human-readable step strings) and 'tool_calls' (an array of objects with keys 'tool_name' and 'arguments'). "
        "If there are no suggested tool calls, return an empty array for 'tool_calls'. Keep the plan concise.\n\n"
        f"Available tools to reference in your plan:\n- {tools_info}"
    )

    example = {
        "plan": ["Load the CSV file", "Detect missing values", "Generate summary statistics"],
        "tool_calls": [
            {"tool_name": "Detect missing values", "arguments": {}},
            {"tool_name": "Generate summary statistics", "arguments": {}}
        ]
    }

    user_prompt = (
        f"Task: {task}\nHas file: {has_file}\n\n"
        f"Generate a plan that references the available tools (if applicable). "
        f"Return the JSON object that represents the plan. Example format:\n{json.dumps(example)}\n"
    )

    try:
        logger.info(f"Calling OpenAI API with model: {model}, task: {task}")
        logger.debug(f"Available tools: {available_tools}")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=800,
        )
    except Exception as e:
        logger.error(f'Error calling OpenAI API: {e}')
        raise RuntimeError(f'Error calling OpenAI API: {e}') from e

    try:
        content = resp.choices[0].message.content
    except Exception as e:
        logger.error(f'Unexpected response format from OpenAI API: {e}')
        raise RuntimeError('Unexpected response format from OpenAI API') from e

    # Extract JSON from content and parse
    try:
        json_text = _extract_json(content)
        parsed = json.loads(json_text)
    except Exception as e:
        # As a fallback, try to load the entire content
        try:
            parsed = json.loads(content)
        except Exception:
            logger.error(f'Could not parse JSON from LLM response: {content}')
            raise ValueError(f'Could not parse JSON from LLM response: {e}\nRaw response:\n{content}')

    # Validate basic shape
    if 'plan' not in parsed or not isinstance(parsed['plan'], list):
        raise ValueError('LLM response JSON does not contain a valid "plan" array')
    if 'tool_calls' in parsed and not isinstance(parsed['tool_calls'], list):
        raise ValueError('LLM response JSON "tool_calls" is not a list')

    logger.info(f"Successfully generated plan with {len(parsed['plan'])} steps")
    logger.debug(f"Plan details: {parsed}")
    return parsed


def respond_via_llm(task: str, model: str = 'gpt-4') -> str:
    """
    Call the OpenAI Chat API to produce a direct natural-language response.

    Returns the assistant's response text.
    """
    if not OPENAI_API_KEY:
        raise EnvironmentError('OPENAI_API_KEY not set in environment')

    try:
        from openai import OpenAI
    except ImportError as e:
        raise ImportError('The openai package is required for LLM responses. Please install `openai` in your environment.') from e

    client = OpenAI(api_key=OPENAI_API_KEY)

    system_prompt = (
        "You are a helpful assistant. Provide a concise, direct answer. "
        "If the question is unclear, ask a brief clarifying question."
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ],
            temperature=0.2,
            max_tokens=800,
        )
    except Exception as e:
        logger.error(f'Error calling OpenAI API for response: {e}')
        raise RuntimeError(f'Error calling OpenAI API: {e}') from e

    try:
        content = resp.choices[0].message.content
    except Exception as e:
        logger.error(f'Unexpected response format from OpenAI API: {e}')
        raise RuntimeError('Unexpected response format from OpenAI API') from e

    return content.strip()

