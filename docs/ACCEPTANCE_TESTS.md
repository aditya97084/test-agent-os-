# ACCEPTANCE_TESTS — every gate, exact commands, expected evidence

Rule: a phase is DONE only when its test's **real terminal output** is pasted into `docs/PROGRESS.md` **and `deploy/scripts/preflight.py` prints all-pass** (E1: "done = preflight passed"). No output = not done (Law 11). Tests live in `tests/acceptance/` and must be re-runnable at any time (they are the regression suite). Every organ additionally ships its `/diag` + probe (E2) and those are part of the gate.

## Infra gates (run before & after every phase)

```powershell
pwsh deploy/scripts/verify.ps1     # or bash deploy/scripts/verify.sh
```
Expected: `postgres OK · redis OK · temporal OK · litellm OK · PLANNING ✓ (claude-sonnet-4-6) · FALLBACK ✓ (MiniMax-M3) · LOCAL ✓` (LOCAL only when `local` profile up).

## Phase -1 — Audit
- `docs/AUDIT_REPORT.md` exists with summary counts + per-class table + PRESERVE/DO-NOT-TOUCH lists.
- Every MOCK finding has file:line evidence.
- User confirmation message recorded in PROGRESS.md.

## Phase 0 — Resume-after-kill
`python tests/acceptance/phase0_resume.py`
1. create task (6 demo steps × 15 s) → 2. kill gateway+worker+app at ~step 3 → 3. relaunch → 4. assert resume at step 4, task COMPLETED, `task_steps` has step 3 completed exactly once.
PASS line must include the DB step-log dump.

## Phase 1 — Model disable failover
1. `curl` a task routed to `planning` group; 2. meanwhile set `ANTHROPIC_API_KEY` invalid / kill provider via LiteLLM block-key API; 3. assert request completes via `MiniMax-M3`; 4. gateway logs show `Requested: planning-primary, Actual: planning-secondary, Reason: provider error` (Law 4).
Also: `GET /v1/agents` shows per-agent health state enum from `contracts/agent_registry.schema.json`.

## Phase 2 — Mid-task agent swap
1. real coding task with Claude Code worker; 2. simulate crash mid-step (kill worker PID); 3. Temporal reschedules to Codex; 4. **git diff proves completed files unchanged / not regenerated**; `agent_history` shows 2 entries, `failure_history` has reason; 5. Kanban card never reset to top.

## Phase 3 — Approval gate before submit
Scripted flow: open URL → search → read → fill form; test PASSES only if execution **halts before submit** with an approval request row in `WAITING_FOR_USER`, and resumes after simulated approve. Browser actions each logged (action, target, screenshot ref) in per-action audit log. DOM selectors used; vision-fallback path covered by a second test with DOM disabled.

## Phase 4 — Restart-proof recall
1. session A: create decision + memory write; 2. full restart; 3. ask same question cold → answer contains the decision **with source path + date + confidence**; Obsidian file exists and matches Postgres row (Postgres = truth, vault = mirror).

## Phase 5 — Two-agent workflow
`workflows/youtube_video.yaml` (research→script→storyboard→assets→qa) runs with nodes assigned to different agents; kill node-2 agent → restart picks per fallback; Kanban + pipeline view (API state) consistent at every check.

## Phase 6 — Scheduler survives reboot
Create `daily 08:00 AI news research`; reboot machine; task executes on schedule without re-registration; result lands in artifacts + memory; missed-run policy respected (log `MISSED`, no silent run pile-up).

## Phase 7 — Real MP4, no mocks
One topic → output dir contains: `script.md`, `storyboard.json`, `assets/`, `final.mp4` (ffprobe duration > 0, matches timeline), `thumbnail.png`, `caption.txt`, `metadata.json`. Render was Remotion+FFmpeg with checkpoint per stage (re-run resumes at failed stage). Approval record required before "publish-ready" flag.

## Phase 8 — Publish receipt
Sandbox/draft account: publish via official API → store receipt (URL, timestamp, payload hash) as artifact → analytics row ingested next day. Reject path: publish without approval row returns 403 in API test.

## Phase 9 — Evolution sandbox E2E
Discover a real GitHub tool repo → clone into `sandbox/` → automated smoke tests in isolated env → verdict report (capabilities/license/health vs current stack) → **no production import until human APPROVE**. Test PASSES also on the REJECT branch (must be able to reject).

## Phase 10 — No fake UI
Every interactive dashboard element maps to a live endpoint; test iterates UI and asserts a network call (or WebSocket event) per action. Any button without a call = Law 10 violation = phase fail.

## Phase 11 — Final suite = blueprint §9 Tests 1–10
All ten scenarios from `docs/MASTER_BLUEPRINT.md` §9 executed end-to-end with output logs attached to PROGRESS.md. Plus secret scan (git history + logs: zero key material), and offline test: internet cut → `local` group answers simple tasks, critical tasks park in `WAITING_FOR_RESOURCE`.

---
### Evidence tags (each PROGRESS entry)
`FACT` (ran it, output attached) · `INFERENCE` (reasoned, not run) · `UNKNOWN` (can't verify here) · `HYPOTHESIS` (design assumption). Agents must never upgrade a tag without new evidence.
