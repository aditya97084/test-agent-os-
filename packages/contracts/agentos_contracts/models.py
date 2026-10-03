"""AgenticOS shared contracts (pydantic).

The normative schema is the JSON contract at repo root: contracts/task_state.schema.json.
These models are the enforcement layer — gateway and workers validate through them, so a
malformed task state can never be persisted (Phase 2 hard requirement, seeded here at Phase 0).
"""
from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    WAITING_FOR_RESOURCE = "WAITING_FOR_RESOURCE"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED_FINAL = "FAILED_FINAL"
    CANCELLED = "CANCELLED"


class EvidenceTag(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"
    HYPOTHESIS = "HYPOTHESIS"


class Checkpoint(BaseModel):
    model_config = ConfigDict(extra="allow")
    step: str = "0"
    attempt: int = 0
    git_commit: str | None = None
    input_artifacts: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    selected_model: str | None = None
    state_blob_ref: str | None = None
    saved_at: dt.datetime | None = None


class AgentHistoryEntry(BaseModel):
    agent: str
    from_at: dt.datetime
    to_at: dt.datetime | None = None
    steps_done: list[str] = Field(default_factory=list)


class FailureEntry(BaseModel):
    at: dt.datetime
    agent: str | None = None
    model: str | None = None
    reason: str
    recovered_via: str | None = None


class TaskState(BaseModel):
    """Mirror of contracts/task_state.schema.json (required fields + enums enforced here)."""

    model_config = ConfigDict(extra="allow")

    task_id: str = Field(pattern=r"^task_[a-z0-9]{6,40}$")
    goal: str
    priority: int = Field(default=2, ge=0, le=5)
    status: TaskStatus = TaskStatus.CREATED
    current_agent: str | None = None
    requested_agent: str | None = None
    actual_reason: str | None = None
    mode: str = "AUTONOMOUS"
    checkpoint: Checkpoint = Field(default_factory=Checkpoint)
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    updated_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    completed_steps: list[str] = Field(default_factory=list)
    remaining_steps: list[str] = Field(default_factory=list)
    files_changed: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    agent_history: list[AgentHistoryEntry] = Field(default_factory=list)
    failure_history: list[FailureEntry] = Field(default_factory=list)
    evidence_tag: EvidenceTag = EvidenceTag.FACT

    def touch(self) -> None:
        self.updated_at = dt.datetime.now(dt.timezone.utc)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def task_state_matches_json_contract() -> bool:
    """Sanity check used by tests: required fields of the JSON contract ⊆ model fields."""
    import json
    from pathlib import Path

    candidates = [
        Path(__file__).resolve().parents[3] / "contracts" / "task_state.schema.json",
        Path("contracts/task_state.schema.json"),
    ]
    for p in candidates:
        if p.exists():
            schema = json.loads(p.read_text())
            required = set(schema.get("required", []))
            return required.issubset(set(TaskState.model_fields.keys()))
    raise FileNotFoundError("task_state.schema.json not found")
