import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

from . import engine
from .config import settings
from .engine import (
    TASKS,
    approve_action,
    approve_boundary,
    build_report,
    create_task,
    execute_task,
    get_task,
    plan_task,
    rollback_task,
    serialize_task,
)
from .inventory import PROJECTS, all_resources
from .models import CreateTaskRequest

logging.basicConfig(level=settings().log_level,
    format='{"time":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}')
app = FastAPI(title="Scope Guard API", version="0.1.0",
              description="Deterministic intent-bound execution control plane")
app.add_middleware(CORSMiddleware, allow_origins=settings().allowed_origins.split(","),
                   allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def request_context(request: Request,
                          call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    request_id = request.headers.get("x-request-id", str(uuid4()))
    correlation_id = request.headers.get("x-correlation-id", request_id)
    try:
        response = await call_next(request)
    except Exception as error:
        logging.exception("request_failed")
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR",
            "message": str(error), "request_id": request_id, "correlation_id": correlation_id}})
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


def demo_auth(x_demo_token: str = Header(default="")) -> str:
    if x_demo_token != settings().demo_api_token:
        raise HTTPException(status_code=401, detail={"code": "DEMO_AUTH_REQUIRED",
            "message": "Use the documented local demo token"})
    return "demo_user"


def task_or_404(task_id: str) -> object:
    try:
        return get_task(task_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail={"code": "TASK_NOT_FOUND"}) from error


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "mode": "demo" if settings().demo_mode else "live",
            "provider": "codex_demo" if settings().demo_mode else "codex_live"}


@app.get("/api/projects")
async def projects() -> list[dict[str, object]]:
    return [project.model_dump(mode="json") for project in PROJECTS]


@app.post("/api/inventory/scan")
async def scan(_: str = Depends(demo_auth)) -> dict[str, object]:
    return {"projects": [project.model_dump(mode="json") for project in PROJECTS],
            "resources": [resource.model_dump(mode="json") for resource in all_resources()],
            "source": "registered-synthetic-inventory"}


@app.post("/api/tasks", status_code=201)
async def tasks(request: CreateTaskRequest, _: str = Depends(demo_auth)) -> dict[str, object]:
    return serialize_task(create_task(request))


@app.get("/api/tasks/{task_id}")
async def task(task_id: str) -> dict[str, object]:
    return serialize_task(task_or_404(task_id))  # type: ignore[arg-type]


@app.post("/api/tasks/{task_id}/plan")
async def plan(task_id: str, _: str = Depends(demo_auth)) -> dict[str, object]:
    value = task_or_404(task_id)
    await plan_task(value)  # type: ignore[arg-type]
    return serialize_task(value)  # type: ignore[arg-type]


@app.post("/api/tasks/{task_id}/approve-boundary")
async def approve_manifest(task_id: str, actor: str = Depends(demo_auth)) -> dict[str, object]:
    value = task_or_404(task_id)
    approve_boundary(value, actor)  # type: ignore[arg-type]
    return serialize_task(value)  # type: ignore[arg-type]


@app.post("/api/tasks/{task_id}/execute")
async def execute(task_id: str, _: str = Depends(demo_auth)) -> dict[str, object]:
    value = task_or_404(task_id)
    await execute_task(value)  # type: ignore[arg-type]
    return serialize_task(value)  # type: ignore[arg-type]


@app.post("/api/tasks/{task_id}/actions/{action_id}/approve")
async def approve(task_id: str, action_id: str, _: str = Depends(demo_auth)) -> dict[str, object]:
    value = task_or_404(task_id)
    await approve_action(value, action_id)  # type: ignore[arg-type]
    return serialize_task(value)  # type: ignore[arg-type]


@app.post("/api/tasks/{task_id}/actions/{action_id}/reject")
async def reject(task_id: str, action_id: str, _: str = Depends(demo_auth)) -> dict[str, object]:
    value = task_or_404(task_id)
    if value.pending_action != action_id:  # type: ignore[attr-defined]
        raise HTTPException(status_code=409, detail={"code": "ACTION_NOT_PENDING"})
    value.pending_action = None  # type: ignore[attr-defined]
    value.status = "rejected"  # type: ignore[attr-defined]
    value.events.append(task_id, "action_rejected", "demo_user", {"action_id": action_id})  # type: ignore[attr-defined]
    return serialize_task(value)  # type: ignore[arg-type]


@app.post("/api/tasks/{task_id}/rollback")
async def rollback(task_id: str, _: str = Depends(demo_auth)) -> dict[str, object]:
    value = task_or_404(task_id)
    await rollback_task(value)  # type: ignore[arg-type]
    value.report = build_report(value)  # type: ignore[attr-defined,arg-type]
    return serialize_task(value)  # type: ignore[arg-type]


@app.get("/api/tasks/{task_id}/events")
async def events(task_id: str) -> StreamingResponse:
    value = task_or_404(task_id)

    async def stream() -> AsyncIterator[str]:
        for event in value.events.events:  # type: ignore[attr-defined]
            yield f"id: {event.id}\nevent: {event.event_type}\ndata: {event.model_dump_json()}\n\n"
        yield "event: stream_complete\ndata: {}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/tasks/{task_id}/report")
async def report(task_id: str, format: str = "json") -> Response:
    value = task_or_404(task_id)
    report_value = value.report or build_report(value)  # type: ignore[attr-defined,arg-type]
    if format == "markdown":
        blocked = len(report_value["blocked_actions"])
        text = (f"# Scope Guard execution report\n\nTask: `{task_id}`\n\n"
                f"- Status: {report_value['status']}\n- Provider: {report_value['provider']}\n"
                f"- Blocked actions: {blocked}\n- Audit integrity: {report_value['audit_integrity']}\n"
                f"- Rollback triggered: {report_value['rollback']['triggered']}\n")
        return PlainTextResponse(text, media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="scope-guard-{task_id}.md"'})
    return JSONResponse(report_value, headers={"Content-Disposition":
        f'attachment; filename="scope-guard-{task_id}.json"'})


@app.get("/api/evaluations/latest")
async def latest_evaluation() -> dict[str, object]:
    try:
        with open("evaluations/sentrybench/results/latest.json") as file:
            value: dict[str, object] = json.load(file)
            return value
    except FileNotFoundError:
        return {"status": "not_run", "metrics": {}, "scenarios": []}


@app.post("/api/demo/reset")
async def demo_reset(_: str = Depends(demo_auth)) -> dict[str, object]:
    result = await engine.runner.execute("reset")
    TASKS.clear()
    return {"reset": True, "protected_integrity": result["engageflow"]["healthy"]}


@app.get("/api/demo/status")
async def demo_status() -> dict[str, object]:
    return {"mode": "demo" if settings().demo_mode else "live", "provider":
            "codex_demo" if settings().codex_provider != "live" else "codex_live",
            "planner_provider": "gpt_demo" if settings().demo_mode else "gpt_live", "tasks": len(TASKS),
            "sandbox": "docker-required"}
