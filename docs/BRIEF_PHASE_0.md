# BRIEF — Phase -1 + Phase 0 (paste this whole file's content to the coding agent)

You are building AgenticOS. obey `AGENTS.md` (12 Laws) and `docs/MASTER_BLUEPRINT.md` (architecture, §6 layout, §7 ladder). Implement **only** Phase -1 and Phase 0 below. Any future-phase code you write will be rejected.

---

## PHASE -1 — EXISTING SYSTEM AUDIT (blocking; you must not build until user confirms)

Target: the user's existing `D:\AI_SYSTEM` (Windows). If repo root is elsewhere, ask user for the path first.

1. Recursively inventory `D:\AI_SYSTEM`: every folder, file group, project, config, DB, service. Read-only.
2. Classify every component as exactly one of:
   `WORKING · PARTIAL · MOCK · BROKEN · MISSING · DO_NOT_REUSE`
   - MOCK = looks functional (buttons/hardcoded responses/fake integrations) — call these out explicitly with file:line evidence.
   - DO_NOT_REUSE = deprecated/dangerous/duplicate-of-target-stack, with reason.
3. For each found tool also record: does it have a real headless API/CLI, or only a GUI? (Determines worker feasibility per blueprint.)
4. Write `docs/AUDIT_REPORT.md`:
   - Summary counts per classification (tag every claim FACT/INFERENCE/UNKNOWN per Law 11).
   - Table: path · type · classification · evidence · preserve/migrate/isolate recommendation.
   - A "preserve list" (never delete) and a "do-not-touch list".
5. **STOP. Ask the user to confirm the report.** (Law 9.) Do not delete/rename/move anything, ever, in this phase.

## PHASE 0 — CORE SKELETON (durable execution spine)

Prereq: `deploy/docker-compose.yml` is already up and `verify` script passed (if not: run `deploy/scripts/setup.ps1|sh`, then `verify`; tell user to fill `deploy/.env` if missing).

Build, in this order:

1. **Monorepo layout** per `docs/MASTER_BLUEPRINT.md` §6 (create `services/`, `workers/`, `packages/`, `apps/`, `tests/`, `config/`, `data/`, `logs/`, `artifacts/`, `sandbox/` etc. — empty-but-wired, not fake-filled).
2. **`packages/contracts`** — Python (pydantic) + TypeScript types **generated from / validated against** `contracts/task_state.schema.json`, `contracts/agent_registry.schema.json`, `contracts/workflow_node.schema.json`. CI check: schemas ↔ models stay in sync.
3. **`services/gateway` (FastAPI, Python 3.12)**:
   - `POST /v1/tasks` (create task, full schema), `GET /v1/tasks/{id}`, `POST /v1/tasks/{id}/pause|resume|cancel`
   - starts a Temporal workflow per task (task queue `agentos-main`)
   - `GET /v1/events` — WebSocket/SSE live task status stream (Redis pub/sub)
   - structured logging to `logs/` with **secret redaction filter** (Law 7)
4. **`services/orchestrator` (Temporal workers)**:
   - Workflow `TaskExecution`: deterministic loop over steps; **upsert Search Attribute + save checkpoint to Postgres before every step**; on activity failure → retry policy → mark step `WAITING_FOR_RESOURCE` (never hard-fail silently).
   - Demo activity for Phase 0 only: `dummy_step(n)` that sleeps 15s per step × 6 steps, writing progress into task state (this is the durability test target, not product code — label it `demo:` prefix so it's unmistakable).
5. **DB migrations** (Alembic) — `tasks`, `task_steps`, `checkpoints`, `agent_history`, `failure_history` tables matching the schema; Postgres = machine truth.
6. **Tauri app stub** — only: window + "SYSTEM ● ONLINE/DEMO" status pulled from `GET /v1/health`. **No dashboard features. No mock UI (Law 10).** (If Node toolchain missing, ship a plain `apps/web` static page hitting the same endpoint and say so in PROGRESS.)
7. **Config** — `config/gateway.yaml` (ports, temporal namespace `agentos`, DB/Redis from **env vars**, never hardcoded); model groups file `config/model_groups.yaml` mirroring LiteLLM aliases (planning/coding/research/fast/vision/local) — read-only at this phase.
8. **`deploy/scripts/preflight.py` (E1) — the harness that defines "done" forever.** Live-chain checks against the RUNNING system, no mocks, tick/cross per check, `N pass / N fail / N warn` summary, exit non-zero on any fail. Phase 0 checks: server up + serving viewer; graph/state loads; a real task runs end-to-end via Temporal; config secrets NOT reachable from browser (must fail loudly if reachable); served JS == files on disk; every LiteLLM group answers one real minimal call with the key in `.env` (skip with WARN if that provider key is absent). From now on: **whenever you claim done, run preflight and paste its summary line.**
9. **Tests + tooling** — pytest for gateway/state-machine; `make dev` (or `scripts/dev.ps1`) to run gateway+workers locally; ruff/mypy strict on services.

## Phase 0 ACCEPTANCE TEST (must pass before you report "done")

Write `tests/acceptance/phase0_resume.py` + a shell/ps1 driver that:

1. boots compose stack + gateway + Temporal worker
2. creates a demo task (6×15s steps)
3. at ~step 3: **kills the gateway AND the worker AND the Tauri stub** (`Stop-Process` / `kill -9`)
4. restarts everything
5. asserts: task resumed at **step 4** (not 1), completed, and `task_steps` shows step 3 exactly once completed (no repeat)
6. prints PASS/FAIL with the actual step log

Paste that real output into `docs/PROGRESS.md` under `## Phase 0 — FACT`. If you cannot run it (e.g. Docker missing on this machine), the phase status is **UNKNOWN/NOT VERIFIED** — say so plainly; do not claim success (Laws 10–11).

## Deliverables checklist

- [ ] `docs/AUDIT_REPORT.md` written; user confirmation recorded
- [ ] repo tree per §6 exists and boots
- [ ] `POST /v1/tasks` end-to-end through Temporal
- [ ] checkpoint-before-every-step verified in DB rows
- [ ] live events visible via WS
- [ ] kill-and-resume acceptance test PASS (output in PROGRESS.md)
- [ ] `deploy/scripts/preflight.py` implemented and printing all-pass (E1)
- [ ] `docs/PROGRESS.md` updated, every claim tagged

Next phase (do NOT start without user go-ahead): Phase 1 — model+agent layer (LiteLLM routing already configured in `deploy/litellm/config.yaml`; you build registry, health manager, adapters, router client).
