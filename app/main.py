from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.agent.schemas import AgentRunResponse
from typing import Optional

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
    from app.agent.planner import create_plan
    import app.agent.executor as executor_module

    has_file = bool(file and file.filename)

    plan = create_plan(task, has_file=has_file)
    result, tool_calls = executor_module.execute_plan(plan, file)

    return AgentRunResponse(
        task=task,
        plan=plan,
        tool_calls=tool_calls,
        result=result
    )
