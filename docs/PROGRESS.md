# PROGRESS.md — living status ledger (every agent MUST update after each phase)

Format rules: every line tagged **FACT** (ran it — output below), **INFERENCE** (reasoned, not executed), **UNKNOWN** (cannot verify here), **HYPOTHESIS** (design assumption). A phase claim without attached command output = not done. No tag = invalid entry.

---

## Status board

| Phase | State | Verified how |
|---|---|---|
| -1 Audit | NOT_STARTED (laptop-only — needs D:\AI_SYSTEM) | — |
| 0 Core skeleton | **PARTIAL** — code pre-written + validated on local dev engine in sandbox; Temporal-engine E2E pending on real stack | see Phase 0 log below |
| 1 Model+agent layer | NOT_STARTED | — |
| 2 Task state + failover | PARTIAL — durable state schema/tables/checkpoint-before-step + exactly-once resume already exercised (subset of Phase 2) | Phase 0 log |
| 3–11 | NOT_STARTED | — |

---

## Phase log

### Phase 0 — skeleton pre-built in handoff repo — 2026-09-21 (arena sandbox)

- FACT: gateway + durable-task engine + checkpointed step log implemented (`services/gateway`, `services/orchestrator`, `packages/db|contracts|events`), imports clean, `pip install -e .` works, `pytest tests/unit` → **4 passed**.
- FACT: **kill→resume acceptance PASS** (`tests/acceptance/phase0_resume.py`, local dev engine):
  step 1-3 completed pre-kill exactly once; step 4 interrupted mid-`pure_demo_step` → row kept `running` (attempt 0, history NOT rewritten); after SIGKILL of gateway + restart: `resumed_on_boot: 1`, step 4 re-executed attempt=1 → completed; steps 5-6 each completed once; final status COMPLETED →
  verdicts printed: `PASS COMPLETED reached / PASS every step completed exactly once / PASS steps 1-3 started before kill / PASS post-kill steps completed after kill / PASS local engine resumed task on boot` → `RESULT: PASS ✅ durable resume proven`.
- FACT: **preflight (E1 harness) = 7 pass, 0 fail, 2 warn** — incl. real task E2E, checkpoint-count==step-count, served-viewer==disk-file sha256 match, `.env`/config unreachable from browser routes, /v1/diag booleans-only. WARNs by design here: engine=local(dev) (no Temporal binary downloadable in sandbox — temporal.download + GitHub release assets blocked) and LITELLM_MASTER_KEY unset (no keys in sandbox, correct free-first honesty).
- FACT: LiteLLM routing config (`deploy/litellm/config.yaml`) verified at config level (YAML parse + fallback-graph consistency check); raw model IDs `claude-sonnet-4-6` / `MiniMax-M3` / `claude-haiku-4-5-20251001` confirmed current via vendor docs 2026-09.
- UNKNOWN: **Temporal-engine end-to-end** (workflow classes validate at import via temporalio decorators; no server binary in sandbox). On laptop: `deploy/scripts/setup.sh` → `AGENTOS_ENGINE=temporal` → re-run the SAME acceptance test; it must show the same verdicts with engine=temporal AND survive gateway-kill while workflow state lives in Temporal history.
- HYPOTHESIS: local dev-engine semantics are a strict subset of the Temporal path (shared activity/repo code; heartbeat-resume within step is Temporal-only bonus).
- Not done here on purpose: Tauri shell (apps/web viewer serves Phase 0 instead — stated, not hidden), agent registry health (Phase 1).

### Phase -1 — audit
- NOT_STARTED: requires the physical laptop. Prompt ready in docs/AUDIT_PROMPT.md; brief wiring in docs/BRIEF_PHASE_0.md.

<!-- future phases: append, newest first -->
