# Multi-Tool AI Agent

A planner → executor architecture (not a chatbot) that:
- Accepts tasks + CSV uploads
- Plans steps (now using an LLM planner with a rule-based fallback)
- Executes tools (summary stats, missing values)
- Displays step-by-step execution in a UI

## Tech
- FastAPI
- Pandas
- React + Vite (UI)

## LLM planner
The planner now prefers an LLM-based planner (OpenAI) to convert a plain-English `task` into a structured plan JSON. If an LLM call fails (no API key, network error, parse error), the system falls back to the original rule-based planner.

To enable the LLM planner you must set your OpenAI API key in the environment.

This project loads `.env` automatically at startup (via `python-dotenv`), so you can set it there or export it directly:

`.env`:
```
OPENAI_API_KEY=sk-...
```

```bash
export OPENAI_API_KEY="sk-..."
```

If no key is present the server will still run and will use the rule-based planner.

## Direct LLM responses (non-tool tasks)
If a request does not match any CSV/tool intent and no file is uploaded, the API will return a direct LLM response (instead of attempting tool execution). This requires `OPENAI_API_KEY` to be set.

## Run locally
Install Python dependencies and start the backend and UI:

```bash
# from repo root
python -m pip install -r requirements.txt
# start backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# in a separate terminal, start the UI
cd ui
npm install
npm run dev
```

## Quick test (curl)
- Without a file (will often cause the summary tool to be skipped):

```bash
curl -X POST http://127.0.0.1:8000/run -F "task=Generate summary statistics"
```

- With a sample CSV:

```bash
curl -X POST http://127.0.0.1:8000/run -F "task=Generate summary statistics" -F "file=@tmp/test.csv"
```

The response is a JSON object with keys: `task`, `plan` (array of steps), `tool_calls` (array of tool call records) and `result` (final output string).
