from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from environment.env    import CodeSentinelEnv
from environment.models import (
    Action, TaskId, StepResponse, ResetResponse,
    EnvironmentState, ValidateResponse, Observation
)

app = FastAPI(
    title       = "CodeSentinel OpenEnv",
    description = "AI environment for automated code review agents",
    version     = "1.0.0",
)
env = CodeSentinelEnv()


class ResetRequest(BaseModel):
    task_id: TaskId = TaskId.bug_detection
    seed:    int    = 42


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>CodeSentinel — AI Code Review Environment</title>
      <meta name="description" content="OpenEnv-compliant AI training environment for code review agents.">
      <style>
        body{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;background:#0d1117;color:#e6edf3;}
        h1{font-size:2rem;color:#58a6ff;}
        h2{color:#79c0ff;border-bottom:1px solid #30363d;padding-bottom:.4rem;}
        a{color:#58a6ff;}
        table{border-collapse:collapse;width:100%;margin:1rem 0;}
        th,td{border:1px solid #30363d;padding:.5rem 1rem;text-align:left;}
        th{background:#161b22;}
        code{background:#161b22;padding:2px 6px;border-radius:4px;}
        .easy{color:#3fb950;}.medium{color:#d29922;}.hard{color:#f85149;}
      </style>
    </head>
    <body>
      <h1>🛡️ CodeSentinel</h1>
      <p>A real-world OpenEnv environment where AI agents learn to review code like a senior engineer.</p>
      <h2>Tasks</h2>
      <table>
        <tr><th>Task</th><th>Difficulty</th><th>Max Steps</th></tr>
        <tr><td>bug_detection</td><td class="easy">Easy</td><td>20</td></tr>
        <tr><td>security_audit</td><td class="medium">Medium</td><td>30</td></tr>
        <tr><td>architecture_review</td><td class="hard">Hard</td><td>50</td></tr>
      </table>
      <h2>API</h2>
      <ul>
        <li><a href="/validate">GET /validate</a> — Health check</li>
        <li><a href="/docs">GET /docs</a> — Swagger UI</li>
        <li>POST /reset — Start episode</li>
        <li>POST /step — Submit action</li>
        <li>GET /state — Inspect state</li>
      </ul>
    </body>
    </html>
    """


@app.get("/validate", response_model=ValidateResponse)
def validate():
    return ValidateResponse(
        valid   = True,
        version = "1.0.0",
        tasks   = ["bug_detection", "security_audit", "architecture_review"],
        message = "CodeSentinel is healthy and ready.",
    )


@app.post("/reset", response_model=Observation)
def reset(req: Optional[ResetRequest] = None):
    if req is None:
        req = ResetRequest()
    try:
        resp = env.reset(task_id=req.task_id, seed=req.seed)
        return resp.observation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step", response_model=StepResponse)
def step(action: Action):
    try:
        return env.step(action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state", response_model=EnvironmentState)
def state():
    try:
        return env.state()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
