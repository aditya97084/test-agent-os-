# Worker Contract — the interface that makes agents replaceable

Every agent (Claude Code, Codex, Antigravity, OpenCode, Hermes-adapter, local) and every tool-runner implements **exactly this** (blueprint §5, Doc3 §10). If a product has no real headless route, it is wrapped by GUI automation behind the same contract — and marked `PARTIAL` honestly; a fake implementation is a Law-10 violation.

## Python (Temporal activity implementation)

```python
from typing import Protocol, Literal
from contracts.models import TaskContext, WorkerResult, Health  # generated from contracts/*.json

class Worker(Protocol):
    id: str                      # registry id, e.g. "claude-code"
    capabilities: list[str]      # routing keys

    async def health_check(self) -> Health: ...
        # state ∈ AVAILABLE/BUSY/RATE_LIMITED/QUOTA_EXHAUSTED/AUTH_EXPIRED/
        #        SUBSCRIPTION_EXPIRED/CLI_MISSING/CRASHED/OFFLINE/DISABLED

    async def execute(self, task: TaskContext) -> WorkerResult: ...
        # MUST be resumable: task.checkpoint tells you where to continue.
        # MUST return {completed_steps, artifacts, files_changed, next_state,
        #              error?: {reason, recoverable: bool}}

    async def pause(self, task_id: str) -> None: ...       # optional
    async def resume(self, task: TaskContext) -> WorkerResult: ...  # optional
```

**Rules the engine enforces regardless of worker:**
1. Checkpoint is written **before** invoking a step (Temporal upsert + Postgres row).
2. A worker receives: `goal · completed_steps · repo state · branch · tests · remaining_steps · failure_reason · checkpoint` — never a predecessor's raw chat history.
3. `WorkerResult.error.recoverable = false` only for validation-type failures; provider/health failures are `recoverable = true` → engine marks `WAITING_FOR_RESOURCE`/`RETRY_SCHEDULED` and re-routes (`fallback_order`).
4. Every swap appends `agent_history` + `failure_history` and exposes `Requested/Actual/Reason` (Law 4).
5. LLM calls inside workers go through the LiteLLM gateway with a group alias from `model_groups` — base URL + `LITELLM_MASTER_KEY` from env (Law 1/7).
6. Cost (tokens/USD) returned in the result; gateway accumulates `task.cost` (Law 8).

## TypeScript (worker-side helper, e.g. for n8n / Tauri bridge)

```ts
export interface Worker {
  id: string;
  capabilities: string[];
  healthCheck(): Promise<Health>;
  execute(task: TaskContext): Promise<WorkerResult>;
  pause?(taskId: string): Promise<void>;
  resume?(task: TaskContext): Promise<WorkerResult>;
}
```

## Adapter notes (locked expectations)

| Worker | Headless route (verify at Phase 1, don't trust READMEs) | Notes |
|---|---|---|
| Claude Code | `claude -p --output-format stream-json` (non-interactive mode) | resume via `--resume <session>`; state still comes from OUR task context, not its session |
| Codex | `codex exec` / app-server JSON-RPC | sandbox flags per config; log stderr tail on failure |
| OpenCode | CLI/API per project docs | free-first candidate for routine diffs |
| Antigravity | verify availability — GUI-first product; if no documented headless API/CLI → OS **launches the app** and drives via Playwright/UIA path; never invent an SDK | explicitly allowed outcome: "GUI-only" flag in registry |
| Hermes | adapter via its API/skills loop | Layer-2 cognitive: plans, answers, delegates — long work still runs in Temporal (§2 of blueprint) |
