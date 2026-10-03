"""Repository — all state writes flow through here so engine choices (temporal/local)
share identical semantics. Every mutation bumps updated_at and returns the new state."""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import func, select

from agentos_contracts.models import TaskState, TaskStatus
from agentos_db.engine import get_sessionmaker
from agentos_db.orm import (
    AgentHistoryRow,
    CheckpointRow,
    FailureHistoryRow,
    TaskRow,
    TaskStepRow,
)


async def create_task(state: TaskState) -> None:
    async with get_sessionmaker()() as s:
        s.add(
            TaskRow(
                id=state.task_id,
                status=state.status.value,
                priority=state.priority,
                mode=state.mode,
                goal=state.goal,
                current_agent=state.current_agent,
                state=state.model_dump(mode="json"),
            )
        )
        await s.commit()


async def load_task(task_id: str) -> TaskState | None:
    async with get_sessionmaker()() as s:
        row = await s.get(TaskRow, task_id)
        if row is None:
            return None
        return TaskState.model_validate(row.state)


async def list_tasks(limit: int = 50) -> list[TaskState]:
    async with get_sessionmaker()() as s:
        rows = (
            await s.execute(select(TaskRow).order_by(TaskRow.created_at.desc()).limit(limit))
        ).scalars()
        return [TaskState.model_validate(r.state) for r in rows]


async def save_state(state: TaskState) -> None:
    state.touch()
    async with get_sessionmaker()() as s:
        row = await s.get(TaskRow, state.task_id)
        if row is None:
            raise KeyError(state.task_id)
        row.status = state.status.value
        row.goal = state.goal
        row.priority = state.priority
        row.mode = state.mode
        row.current_agent = state.current_agent
        row.state = state.model_dump(mode="json")
        row.updated_at = dt.datetime.now(dt.timezone.utc)
        await s.commit()


async def set_status(task_id: str, status: TaskStatus, **extra: Any) -> None:
    state = await load_task(task_id)
    if state is None:
        raise KeyError(task_id)
    state.status = status
    for k, v in extra.items():
        setattr(state, k, v)
    await save_state(state)


async def save_checkpoint(task_id: str, step: str, attempt: int, payload: dict) -> None:
    """Called BEFORE invoking a step (Phase 0 rule: checkpoint-before-step)."""
    async with get_sessionmaker()() as s:
        s.add(CheckpointRow(task_id=task_id, step=step, attempt=attempt, payload=payload))
        row = await s.get(TaskRow, task_id)
        if row is not None:
            st = TaskState.model_validate(row.state)
            st.checkpoint = {"step": step, "attempt": attempt, **payload}  # type: ignore[assignment]
            st.touch()
            row.state = st.model_dump(mode="json")
            row.updated_at = dt.datetime.now(dt.timezone.utc)
        await s.commit()


async def begin_step(task_id: str, step: str) -> int:
    async with get_sessionmaker()() as s:
        prior = await s.execute(
            select(func.count()).select_from(TaskStepRow).where(
                TaskStepRow.task_id == task_id, TaskStepRow.step == step
            )
        )
        attempt = int(prior.scalar() or 0)
        s.add(TaskStepRow(task_id=task_id, step=step, attempt=attempt, state="running"))
        await s.commit()
        return attempt


async def complete_step(task_id: str, step: str, result: dict | None = None) -> None:
    """Single session: step row + task state updated atomically (no nested writers —
    critical for SQLite dev mode, correct for Postgres too)."""
    async with get_sessionmaker()() as s:
        rows = (
            await s.execute(
                select(TaskStepRow)
                .where(TaskStepRow.task_id == task_id, TaskStepRow.step == step)
                .order_by(TaskStepRow.pk.desc())
                .limit(1)
            )
        ).scalars().all()
        if rows:
            r = rows[0]
            r.state = "completed"
            r.completed_at = dt.datetime.now(dt.timezone.utc)
            r.result = result
        task_row = await s.get(TaskRow, task_id)
        if task_row is not None:
            state = TaskState.model_validate(task_row.state)
            if step not in state.completed_steps:
                state.completed_steps.append(step)
            if step in state.remaining_steps:
                state.remaining_steps.remove(step)
            state.touch()
            task_row.state = state.model_dump(mode="json")
            task_row.updated_at = dt.datetime.now(dt.timezone.utc)
        await s.commit()


async def steps_summary(task_id: str) -> dict[str, Any]:
    async with get_sessionmaker()() as s:
        rows = (
            await s.execute(
                select(TaskStepRow)
                .where(TaskStepRow.task_id == task_id)
                .order_by(TaskStepRow.pk)
            )
        ).scalars().all()
        cps = (
            await s.execute(
                select(CheckpointRow)
                .where(CheckpointRow.task_id == task_id)
                .order_by(CheckpointRow.pk)
            )
        ).scalars().all()
        completed = [r for r in rows if r.state == "completed"]
        return {
            "steps": [
                {
                    "step": r.step,
                    "attempt": r.attempt,
                    "state": r.state,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                }
                for r in rows
            ],
            "completed_count_per_step": {
                k: v for k, v in sorted((s.step, sum(1 for x in completed if x.step == s.step)) for s in completed)
            },
            "checkpoints": [
                {
                    "step": c.step,
                    "attempt": c.attempt,
                    "payload": c.payload,
                    "saved_at": c.saved_at.isoformat() if c.saved_at else None,
                }
                for c in cps
            ],
        }


async def append_agent_history(
    task_id: str, agent: str, requested: str | None = None, reason: str | None = None
) -> None:
    async with get_sessionmaker()() as s:
        s.add(AgentHistoryRow(task_id=task_id, agent=agent, requested=requested, reason=reason))
        await s.commit()


async def append_failure(task_id: str, reason: str, agent: str | None = None) -> None:
    async with get_sessionmaker()() as s:
        s.add(FailureHistoryRow(task_id=task_id, reason=reason, agent=agent))
        await s.commit()
