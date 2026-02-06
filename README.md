# Multi-Tool AI Agent

A planner → executor architecture (not a chatbot) that:
- Accepts tasks + CSV uploads
- Plans steps
- Executes tools (summary stats, missing values)
- Displays step-by-step execution in a UI

## Tech
- FastAPI
- Pandas
- Vanilla HTML/CSS/JS

## Run locally
```bash
uvicorn app.main:app --reload