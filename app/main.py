from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.agent.schemas import AgentRunResponse
from typing import Optional
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Multi-Tool AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Multi-tool AI agent backend is running"
    }

@app.post("/run", response_model=AgentRunResponse)
async def run_agent(
        task: str = Form(...),
        file: Optional[UploadFile] = File(None),
):
    """Run endpoint: plan (via LLM with fallback) -> execute plan -> return results.

    Planner: try LLM planner first (app.agent.llm_client.plan_via_llm). If it fails
    for any reason, fall back to the rule-based planner (create_plan_rulebased).
    """
    # Import here to avoid import-time dependency on OpenAI in environments that don't use it
    from app.agent.planner import create_plan_rulebased
    from app.agent import executor as executor_module
    from app.agent.tools import TOOL_REGISTRY, TOOL_ALIASES

    has_file = bool(file and file.filename)
    task_lower = task.lower()

    # Fast path: if there's no file and the task doesn't look like a tool request,
    # respond directly via LLM without planning/executing tools.
    is_tool_task = False
    for tool_name in TOOL_REGISTRY.keys():
        if tool_name.lower() in task_lower:
            is_tool_task = True
            break
        for alias in TOOL_ALIASES.get(tool_name, []):
            if alias in task_lower:
                is_tool_task = True
                break
        if is_tool_task:
            break

    if not has_file and not is_tool_task:
        try:
            from app.agent.llm_client import respond_via_llm
            logger.info("Non-tool task without file; responding directly via LLM")
            return AgentRunResponse(
                task=task,
                plan=[],
                tool_calls=[],
                result=respond_via_llm(task)
            )
        except Exception as e:
            logger.warning(f"Direct LLM response failed: {type(e).__name__}: {e}")

    # First, try to get a plan from the LLM planner
    plan = None
    planned_tool_calls = []
    try:
        from app.agent.llm_client import plan_via_llm
        logger.info(f"Attempting to use LLM planner for task: {task}")
        llm_resp = plan_via_llm(task, has_file=has_file)
        # Validate and use plan if present
        if isinstance(llm_resp, dict) and 'plan' in llm_resp and isinstance(llm_resp['plan'], list):
            plan = llm_resp['plan']
            logger.info(f"LLM planner succeeded with plan: {plan}")
            # Capture any suggested tool_calls the LLM provided so we can surface them (status: planned)
            raw_tc = llm_resp.get('tool_calls') or []
            for tc in raw_tc:
                try:
                    tn = tc.get('tool_name') if isinstance(tc, dict) else None
                    args = tc.get('arguments', {}) if isinstance(tc, dict) else {}
                    if tn:
                        planned_tool_calls.append({
                            'tool_name': tn,
                            'arguments': args,
                            'status': 'planned',
                            'reason': None,
                            'error': None
                        })
                except Exception:
                    continue
    except Exception as e:
        # LLM planner failed - fall back to rule-based
        logger.warning(f'LLM planner failed with error: {type(e).__name__}: {e}; falling back to rule-based planner')
        logger.exception('Full exception details:')
        plan = None

    # If LLM didn't produce a usable plan, use the rule-based fallback
    if plan is None:
        plan = create_plan_rulebased(task, has_file=has_file)

    # Execute the plan using the existing executor (unchanged)
    result, tool_calls = executor_module.execute_plan(plan, file)

    # If no tool actually ran successfully, fall back to a direct LLM response
    any_success = any(tc.get("status") == "success" for tc in tool_calls)
    if not any_success:
        try:
            from app.agent.llm_client import respond_via_llm
            logger.info("No successful tool calls; using direct LLM response")
            result = respond_via_llm(task)
        except Exception as e:
            logger.warning(f"LLM response fallback failed: {type(e).__name__}: {e}")

    # Prepend the planned_tool_calls (from LLM) to the executor tool_calls so the UI can show planner suggestions
    if planned_tool_calls:
        # Avoid duplicating tools: only prepend those not already present by name
        existing_names = {t.get('tool_name') for t in tool_calls}
        merged = []
        for pt in planned_tool_calls:
            if pt.get('tool_name') not in existing_names:
                merged.append(pt)
        tool_calls = merged + tool_calls

    return AgentRunResponse(
        task=task,
        plan=plan,
        tool_calls=tool_calls,
        result=result
    )
