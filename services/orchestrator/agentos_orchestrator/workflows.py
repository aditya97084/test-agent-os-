"""TaskExecution — the durable Phase-0 spine workflow (Temporal).

Properties (blueprint §2 / Phase 0 acceptance target):
- deterministic loop; all side effects are activities (survive worker restart)
- checkpoint written BEFORE each step attempt
- pause/resume/cancel signals + external PAUSED status honored at step boundaries
- skip steps already completed (resumed workflows don't repeat work even if history
  is replayed against a fresh DB projection)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from agentos_orchestrator.activities import pure_demo_step  # noqa: F401 (pattern ref)


@dataclass
class TaskExecInput:
    task_id: str
    steps: int
    step_seconds: float

ACTIVITY_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=0,  # retry forever: task waits for a worker, never dies
    non_retryable_error_types=["ValueError"],
)


@workflow.defn(name="task-execution")
class TaskExecution:
    @workflow.init
    def __init__(self, inp: TaskExecInput) -> None:
        self.task_id = inp.task_id
        self.steps = inp.steps
        self.step_seconds = inp.step_seconds
        self._paused = False
        self._cancelled = False

    @workflow.signal
    def pause(self) -> None:
        self._paused = True

    @workflow.signal
    def resume(self) -> None:
        self._paused = False

    @workflow.signal
    def cancel(self) -> None:
        self._cancelled = True

    @workflow.run
    async def run(self, inp: TaskExecInput) -> str:  # noqa: ARG002 (state set in init)
        step_names = [f"demo_step_{i + 1}" for i in range(self.steps)]
        await workflow.execute_activity(
            "set_status", args=[self.task_id, "RUNNING"], start_to_close_timeout=timedelta(seconds=10),
            retry_policy=ACTIVITY_RETRY,
        )
        for i, step in enumerate(step_names, start=1):
            while self._paused and not self._cancelled:
                await workflow.wait_condition(lambda: (not self._paused) or self._cancelled, timeout=None)
            if self._cancelled:
                await workflow.execute_activity(
                    "set_status", args=[self.task_id, "CANCELLED"],
                    start_to_close_timeout=timedelta(seconds=10), retry_policy=ACTIVITY_RETRY,
                )
                return "CANCELLED"
            # external pause (gateway flipped status): honor at boundary, poll with a timer
            status = await workflow.execute_activity(
                "task_status", args=[self.task_id], start_to_close_timeout=timedelta(seconds=10),
                retry_policy=ACTIVITY_RETRY,
            )
            while status == "PAUSED" and not self._cancelled:
                await workflow.sleep(timedelta(seconds=5))
                status = await workflow.execute_activity(
                    "task_status", args=[self.task_id], start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=ACTIVITY_RETRY,
                )
            if self._cancelled:
                await workflow.execute_activity(
                    "set_status", args=[self.task_id, "CANCELLED"],
                    start_to_close_timeout=timedelta(seconds=10), retry_policy=ACTIVITY_RETRY,
                )
                return "CANCELLED"
            # CHECKPOINT BEFORE THE STEP — the durability contract
            await workflow.execute_activity(
                "record_checkpoint_before",
                args=[self.task_id, step, i, {"engine": "temporal", "input_artifacts": [], "output_artifacts": []}],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=ACTIVITY_RETRY,
            )
            await workflow.execute_activity(
                "begin_step", args=[self.task_id, step],
                start_to_close_timeout=timedelta(seconds=10), retry_policy=ACTIVITY_RETRY,
            )
            result = await workflow.execute_activity(
                "demo_step",
                args=[self.task_id, step, self.step_seconds],
                start_to_close_timeout=timedelta(seconds=self.step_seconds * 4 + 60),
                heartbeat_timeout=timedelta(seconds=15),
                retry_policy=ACTIVITY_RETRY,
            )
            await workflow.execute_activity(
                "complete_step", args=[self.task_id, step, result],
                start_to_close_timeout=timedelta(seconds=10), retry_policy=ACTIVITY_RETRY,
            )
        await workflow.execute_activity(
            "set_status", args=[self.task_id, "COMPLETED"], start_to_close_timeout=timedelta(seconds=10),
            retry_policy=ACTIVITY_RETRY,
        )
        return "COMPLETED"
