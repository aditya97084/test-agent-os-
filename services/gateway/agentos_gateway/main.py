"""AgenticOS Gateway (FastAPI) — Layer 1 entry: intake, task CRUD, live stream.
No reasoning logic lives here (blueprint §2): Hermes/orchestrator plans via API; execution
is durable (Temporal, or explicitly-flagged local dev engine)."""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import secrets
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from temporalio.client import Client
from temporalio.service import RPCError  # noqa: F401

from agentos_contracts.config import get_settings
from agentos_contracts.models import TaskState, TaskStatus, now_iso
from agentos_db import close_engine, ensure_schema
from agentos_db import repo
from agentos_events import subscribe_events
from agentos_gateway.redact import install_redaction

log = logging.getLogger("agentos.gateway")
STATE: dict[str, Any] = {}


def _temporal_client() -> Client | None:
    return STATE.get("temporal")


class TaskCreate(BaseModel):
    goal: str = Field(min_length=1)
    priority: int = Field(default=2, ge=0, le=5)
    mode: str = Field(default="AUTONOMOUS", pattern="^(DIRECT|AUTONOMOUS)$")
    requested_agent: str | None = None


async def _start_workflow(state: TaskState) -> str:
    settings = get_settings()
    if settings.engine == "temporal":
        client = _temporal_client()
        if client is None:
            # TEMPORAL_UNREACHABLE: hard-fail intake; silently falling back to the local
            # engine at runtime would be a lie about durability.
            raise HTTPException(
                status_code=503,
                detail="TEMPORAL_UNREACHABLE — start the stack (deploy/scripts/setup) or set AGENTOS_ENGINE=local for dev-only mode",
            )
        handle = await client.start_workflow(
            "task-execution",
            args=[{"task_id": state.task_id, "steps": settings.demo_steps, "step_seconds": settings.demo_step_seconds}],
            id=f"wf_{state.task_id}",
            task_queue=settings.task_queue,
        )
        state.temporal_run_id = handle.result_run_id
        state.current_agent = "temporal-worker"
        await repo.save_state(state)
        return "temporal"
    from agentos_gateway import engine_local

    engine_local.start(state.task_id, settings.demo_steps, settings.demo_step_seconds, settings)
    state.current_agent = "local-dev-engine"
    await repo.save_state(state)
    return "local"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    install_redaction()
    await ensure_schema()
    STATE["ws_clients"] = set()
    if settings.engine == "temporal":
        try:
            STATE["temporal"] = await Client.connect(settings.temporal_host, namespace=settings.temporal_ns)
            log.info("temporal connected: %s ns=%s", settings.temporal_host, settings.temporal_ns)
        except Exception as e:  # keep serving; /v1/health reports it, intake returns 503
            STATE["temporal"] = None
            log.warning("temporal unreachable (%s) — health endpoint will report it", e)
    if settings.redis_url:
        STATE["events_queue"] = asyncio.Queue()
        STATE["events_task"] = asyncio.create_task(subscribe_events(STATE["events_queue"]))
    resumed = 0
    if settings.engine == "local":
        from agentos_gateway import engine_local

        resumed = await engine_local.resume_open_tasks(settings)
    STATE["resumed_on_boot"] = resumed
    log.info("gateway up engine=%s (resumed local tasks: %d)", settings.engine, resumed)
    yield
    with contextlib.suppress(Exception):
        STATE.get("events_task") and STATE["events_task"].cancel()
    await close_engine()


app = FastAPI(title="AgenticOS Gateway", version="0.0.1", lifespan=lifespan)


@app.get("/v1/health")
async def health() -> JSONResponse:
    settings = get_settings()
    ok_db = True
    try:
        await repo.list_tasks(limit=1)
    except Exception:
        ok_db = False
    return JSONResponse(
        {
            "system": "ONLINE" if ok_db else "DEGRADED",
            "engine": settings.engine + ("(dev)" if settings.engine == "local" else ""),
            "db": ok_db,
            "temporal": _temporal_client() is not None,
            "redis": bool(settings.redis_url),
            "demo": True,  # Phase 0 skeleton: executor is demo: steps until workers arrive
            "time": now_iso(),
        }
    )


@app.post("/v1/tasks", status_code=201)
async def create_task(body: TaskCreate) -> JSONResponse:
    settings = get_settings()
    steps = [f"demo_step_{i + 1}" for i in range(settings.demo_steps)]
    state = TaskState(
        task_id=f"task_{secrets.token_hex(6)}",
        goal=body.goal,
        priority=body.priority,
        mode=body.mode,
        requested_agent=body.requested_agent,
        current_agent=None,
        completed_steps=[],
        remaining_steps=list(steps),
        checkpoint={"step": "0", "attempt": 0},
    )
    await repo.create_task(state)
    started_on = await _start_workflow(state)
    return JSONResponse(
        {"state": (await repo.load_task(state.task_id)).model_dump(mode="json"), "started_on": started_on},
        status_code=201,
    )


@app.get("/v1/tasks")
async def tasks() -> dict:
    states = await repo.list_tasks()
    return {"tasks": [s.model_dump(mode="json") for s in states]}


async def _get_or_404(task_id: str) -> TaskState:
    state = await repo.load_task(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="no such task")
    return state


@app.get("/v1/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    state = await _get_or_404(task_id)
    return {"state": state.model_dump(mode="json")}


@app.get("/v1/tasks/{task_id}/steps")
async def get_steps(task_id: str) -> dict:
    await _get_or_404(task_id)
    return await repo.steps_summary(task_id)


async def _signal(task_id: str, name: str, status: TaskStatus) -> dict:
    settings = get_settings()
    if settings.engine == "temporal":
        client = _temporal_client()
        if client is not None:
            with contextlib.suppress(Exception):
                await client.get_workflow_handle(f"wf_{task_id}").signal(name)
    await repo.set_status(task_id, status)
    return {"status": status.value, "engine": settings.engine}


@app.post("/v1/tasks/{task_id}/pause")
async def pause(task_id: str) -> dict:
    return await _signal(task_id, "pause", TaskStatus.PAUSED)


@app.post("/v1/tasks/{task_id}/resume")
async def resume(task_id: str) -> dict:
    return await _signal(task_id, "resume", TaskStatus.RUNNING)


@app.post("/v1/tasks/{task_id}/cancel")
async def cancel(task_id: str) -> dict:
    await _signal(task_id, "cancel", TaskStatus.CANCELLED)
    # hard-cancel the temporal workflow too; local engine checks DB flag at boundaries
    settings = get_settings()
    if settings.engine == "temporal" and _temporal_client() is not None:
        with contextlib.suppress(Exception):
            await _temporal_client().get_workflow_handle(f"wf_{task_id}").cancel()
    return {"status": TaskStatus.CANCELLED.value}


@app.get("/v1/diag")
async def diag() -> dict:
    """E2 truth endpoint — booleans/counters only, read from THIS running process."""
    settings = get_settings()
    tasks = await repo.list_tasks(limit=500)
    return {
        "process": "gateway",
        "engine": settings.engine,
        "temporal_connected": _temporal_client() is not None,
        "task_total": len(tasks),
        "tasks_active": sum(1 for t in tasks if t.status in (TaskStatus.RUNNING, TaskStatus.CREATED)),
        "tasks_paused": sum(1 for t in tasks if t.status == TaskStatus.PAUSED),
        "ws_clients": len(STATE.get("ws_clients", ())),
        "resumed_on_boot": STATE.get("resumed_on_boot", 0),
        "db_url_scheme": settings.db_url.split("+")[0],  # scheme only, never creds
    }


@app.websocket("/v1/events")
async def events(ws: WebSocket) -> None:
    await ws.accept()
    clients = STATE["ws_clients"]
    clients.add(ws)
    try:
        q = STATE.get("events_queue")
        last: dict[str, str] = {}
        while True:
            payload: str | None = None
            if q is not None:
                try:
                    payload = json.dumps(await asyncio.wait_for(q.get(), timeout=1.0))
                except asyncio.TimeoutError:
                    pass
            if payload is None:  # tailer: DB is truth — emit state changes too
                for t in await repo.list_tasks(limit=50):
                    stamp = t.updated_at.isoformat() + t.status.value
                    if last.get(t.task_id) != stamp:
                        last[t.task_id] = stamp
                        payload = json.dumps({"task_id": t.task_id, "type": "state", "status": t.status.value})
                        break
            if payload:
                await ws.send_text(payload)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        clients.discard(ws)


# viewer: served ONLY from apps/web/ — config/.env/db are not mounted (preflight enforces)
from agentos_contracts.config import repo_root  # noqa: E402

_VIEWER = repo_root() / "apps" / "web"


@app.get("/", include_in_schema=False)
async def viewer_root() -> FileResponse:
    return FileResponse(_VIEWER / "index.html")


@app.get("/viewer/{path:path}", include_in_schema=False)
async def viewer_path(path: str) -> FileResponse:
    f = (_VIEWER / path).resolve()
    if not str(f).startswith(str(_VIEWER.resolve())) or not f.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(f)
