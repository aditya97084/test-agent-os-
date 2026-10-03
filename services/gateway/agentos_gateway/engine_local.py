"""LOCAL DEV ENGINE — not the production path.

Same step semantics as the Temporal workflow (checkpoint-before-step, skip completed steps,
resume after process restart from Postgres/SQLite truth, honor PAUSED/CANCELLED), but runs
inside the gateway process: a total machine loss would drop in-flight state (which is exactly
what Temporal exists to prevent — blueprint §2). Selected ONLY via AGENTOS_ENGINE=local for
machines without the stack; every response and log line says so, and preflight WARNs when it
is active. Phase 0 acceptance with this engine proves resume-after-kill; on the real compose
stack AGENTOS_ENGINE=temporal must be used.
"""
from __future__ import annotations

import asyncio
import logging

from agentos_contracts.models import TaskStatus
from agentos_db import repo
from agentos_events import publish_event
from agentos_orchestrator.activities import (
    pure_demo_step,
)

log = logging.getLogger("agentos.engine_local")

_active: dict[str, asyncio.Task] = {}


async def run_task(task_id: str, steps: int, step_seconds: float, settings) -> None:
    step_names = [f"demo_step_{i + 1}" for i in range(steps)]
    await repo.set_status(task_id, TaskStatus.RUNNING)
    for i, step in enumerate(step_names, start=1):
        while True:
            st = await repo.load_task(task_id)
            if st is None:
                return
            if st.status == TaskStatus.CANCELLED:
                return
            if st.status != TaskStatus.PAUSED:
                break
            await publish_event(task_id, {"type": "paused"})
            await asyncio.sleep(1.0)
        state = await repo.load_task(task_id)
        if state is None:
            return
        if step in state.completed_steps:
            continue  # never repeat completed work after resume
        attempt = i  # local engine retries at step granularity (dev-only)
        await repo.save_checkpoint(task_id, step, attempt, {"engine": "local(dev)", "input_artifacts": [], "output_artifacts": []})
        await repo.begin_step(task_id, step)
        await publish_event(task_id, {"type": "step_started", "step": step})
        result = await pure_demo_step(step_seconds)
        await repo.complete_step(task_id, step, result)
        await publish_event(task_id, {"type": "step_completed", "step": step})
    await repo.set_status(task_id, TaskStatus.COMPLETED)
    await publish_event(task_id, {"type": "status", "status": "COMPLETED"})


def start(task_id: str, steps: int, step_seconds: float, settings) -> None:
    t = asyncio.create_task(run_task(task_id, steps, step_seconds, settings))
    _active[task_id] = t


def signal_pause(task_id: str) -> None:  # status flag in DB is the control; this keeps API parity
    return


async def resume_open_tasks(settings) -> int:
    """After gateway restart: pick up RUNNING tasks from durable state and continue."""
    resumed = 0
    for st in await repo.list_tasks(limit=200):
        if st.status in (TaskStatus.CREATED, TaskStatus.RUNNING):
            done = len(st.completed_steps)
            log.info("resuming task %s from step %d", st.task_id, done + 1)
            start(st.task_id, settings.demo_steps, settings.demo_step_seconds, settings)
            resumed += 1
    return resumed
