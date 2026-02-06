from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class AgentRunRequest(BaseModel):
    task: str = Field(..., description="User's goal in plain English")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional extra context like user preferences, files, metadata, etc."
    )


class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    status: Optional[str] = Field(default=None, description="Optional status like 'skipped' or 'ok'")
    reason: Optional[str] = Field(default=None, description="Optional reason for skipped/error states")
    error: Optional[str] = Field(default=None, description="Optional error message if the tool failed")


class AgentRunResponse(BaseModel):
    task: str
    plan: List[str] = Field(default_factory=list, description="High-level steps the agent plans")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tools the agent decided to call")
    result: str = Field(..., description="Final answer/result returned to the user")
