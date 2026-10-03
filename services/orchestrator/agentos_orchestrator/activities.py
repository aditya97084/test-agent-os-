"""Temporal activities: all DB/event writes for a running task (demo: steps).

demo_step is explicitly a Phase-0 durability test target, not product logic — prefix `demo:`
everywhere so nobody mistakes it for the future worker pipeline. The pure step implementation
is shared with the local dev engine so both engines have identical semantics.
"""
from __future__ import annotations

import asyncio

from temporalio import activity

from agentos_contracts.models import TaskStatus
from agentos_db import repo
from agentos_events import publish_event


async def pure_demo_step(step_seconds: float, resume_from: float = 0.0) -> dict:
    """Sleeps step_seconds; resumable mid-step from `resume_from` seconds slept."""
    slept = resume_from
    while slept < step_seconds:
        chunk = min(1.0, step_seconds - slept)
        await asyncio.sleep(chunk)
        slept += chunk
    return {"demo:outcome": f"done after {slept:.1f}s", "slept": slept}


@activity.defn(name="record_checkpoint_before")
async def record_checkpoint_before(task_id: str, step: str, attempt: int, payload: dict) -> None:
    await repo.save_checkpoint(task_id, step, attempt, payload)


@activity.defn(name="begin_step")
async def begin_step(task_id: str, step: str) -> int:
    attempt = await repo.begin_step(task_id, step)
    await publish_event(task_id, {"type": "step_started", "step": step, "attempt": attempt})
    return attempt


@activity.defn(name="demo_step")
async def demo_step(task_id: str, step: str, step_seconds: float) -> dict:
    """Heartbeats each second so a restarted worker resumes WITHIN the step instead of
    restarting it (checkpoint-within-step semantics, demo form)."""
    slept = 0.0
    details = activity.info().heartbeat_details
    if details and details.size():
        slept = float(details.payloads_to_obj()[0].get("slept", 0.0))
    while slept < step_seconds:
        chunk = min(1.0, step_seconds - slept)
        await asyncio.sleep(chunk)
        slept += chunk
        activity.heartbeat({"slept": slept})
    return {"demo:outcome": f"done after {slept:.1f}s", "slept": slept}


@activity.defn(name="complete_step")
async def complete_step(task_id: str, step: str, result: dict) -> None:
    await repo.complete_step(task_id, step, result)
    await publish_event(task_id, {"type": "step_completed", "step": step})


@activity.defn(name="set_status")
async def set_status(task_id: str, status: str) -> None:
    await repo.set_status(task_id, TaskStatus(status))
    await publish_event(task_id, {"type": "status", "status": status})


@activity.defn(name="note_failure")
async def note_failure(task_id: str, reason: str, agent: str | None = None) -> None:
    await repo.append_failure(task_id, reason, agent)
    await publish_event(task_id, {"type": "failure", "reason": reason})


@activity.defn(name="task_status")
async def task_status(task_id: str) -> str:
    st = await repo.load_task(task_id)
    return st.status.value if st else "MISSING"


ACTIVITIES = [
    record_checkpoint_before,
    begin_step,
    demo_step,
    complete_step,
    set_status,
    note_failure,
    task_status,
]
