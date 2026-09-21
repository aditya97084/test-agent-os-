# AGENTS.md — Non-negotiable rules for any coding agent working on AgenticOS

You (Claude Code / Codex / OpenCode / Antigravity) are building a **real, local-first Autonomous Agentic OS**. This file is the law. Read `HANDOFF.md` and `docs/MASTER_BLUEPRINT.md` before writing any code.

## The 12 Laws (merge of all source docs — never break these)

1. **System over Model.** No single AI provider, CLI, repo, or subscription may the OS depend on. Every LLM call goes through the LiteLLM gateway at `http://127.0.0.1:4000` using group aliases (`planning`, `coding`, `research`, `fast`, `vision`, `local`) — **never** hardcode a raw model ID in application code.
2. **Backend before beauty.** Never produce a giant `index.html` or start with the dashboard. UI is Phase 10 of the blueprint. If asked for "the interface" before the pipeline works, refuse and point at the build order.
3. **A task never lives in an agent's chat history.** Durable task state (`contracts/task_state.schema.json`) + Temporal checkpoints are the only truth. If the orchestrator (Hermes) or any coding agent dies mid-task, the task must resume from checkpoint on another worker without repeating completed steps.
4. **Agent swaps are visible, never silent.** Whenever the executing agent/model differs from the requested one, record and expose: `Requested: X, Actual: Y, Reason: Z`.
5. **Destructive / external actions are approval-gated by default.** Publishing, sending, deleting, paying, installing into production: always require a human approval record first.
6. **Nothing enters production without Discover → Sandbox → Test → Approve.** This includes any repo you (the agent) find "obviously useful".
7. **Secrets only in `.env` / OS credential store.** Never in HTML/JS, git, logs, memory files, or the Obsidian vault. You must also never echo secret values in terminal output.
8. **Free-first, local-first priority chain:** existing subscription → free API → open source → local model → paid API last. Cost is logged per task step.
9. **`D:\AI_SYSTEM` existing data is sacred.** No delete / overwrite / move / restructure without an explicit recorded user confirmation. The Phase -1 audit comes first; if the audit has not been written to `docs/AUDIT_REPORT.md`, you build nothing.
10. **Zero fake UI.** No mock buttons, no hardcoded responses, no `setTimeout` pretending to be a pipeline. If something can't be implemented for real yet, it does not appear in the UI. Mark it in the audit as MOCK/BROKEN instead.
11. **Evidence tags on every claim.** In reports, progress files, and research: prefix `FACT / INFERENCE / UNKNOWN / HYPOTHESIS`. This applies to your own progress reports too ("what is actually deployed" must be tagged, not assumed).
12. **Do not copy third-party code blindly.** Extract mechanisms and capabilities, not codebases. Do not `npm install`/`pip install` anything that isn't in the approved dependency list for the current phase.

## Working protocol

- Work **one phase at a time** as given in `docs/BRIEF_PHASE_0.md` (then subsequent briefs). Never implement future phases early.
- Every phase ends by updating `docs/PROGRESS.md` with: what was built, how to run it, which acceptance tests passed (paste actual command output), what remains — all tagged per Law 11.
- All code goes under the repo tree defined in `docs/MASTER_BLUEPRINT.md` §6. Contracts in `contracts/` are the source of truth for schemas — import/validate against them, do not fork ad-hoc copies.
- Infra is already defined in `deploy/docker-compose.yml`. Do not replace Temporal/Postgres/Redis/LiteLLM with hand-rolled equivalents.
- Tests: every module ships with its tests. The failover test (kill mid-task → resume elsewhere → no repeated work) must pass before you may call anything "done".

## Engineering rules (E1–E9 — folded in from the Jarvis/Holo packs via `docs/research/JARVIS_HOLO_PACK_RECON.md`; these are Laws in force)

- **E1 Done = preflight passed.** Every phase creates/extends `deploy/scripts/preflight.py` running **live end-to-end chains only** (no mocks). A phase is "done" only when preflight prints all-pass and its summary line is pasted in PROGRESS.md. Grow it one check per real incident.
- **E2 Truth endpoints before tuning.** Every organ ships `GET /…/diag` (booleans/counters, never identities) read from the **running** process, plus a scripted probe (verdict machine-readable). When behavior is wrong in the field: read sensors first, code second. Time-based probes must assert a visible viewport (hidden tabs throttle timers and make checks lie).
- **E3 No nearest-match guessing.** Any human utterance mapped to an exact id (model, agent, path, tool, alias) resolves against an **explicit known set**; a near-miss fails loudly and lists what exists. Never silently load "the closest one". Runtime model swaps revert to config on restart (never strand a session on an unintended brain).
- **E4 Tuning = named constants.** Every threshold/timing/grace/pool size lives in one named constant at the top of its file, changed only from instrumented field data, never from vibes.
- **E5 Monitor pattern: cheap-watch → expensive-think.** Background monitors poll a cheap local signal (diff, counter, file mtime); a model is invoked only on a threshold event, with a cooldown after. Cost logs must prove idle = zero model calls.
- **E6 Name out loud, store nothing.** Sensitive transient signals (app names, tab identities, posture, drift labels) are compared and discarded inside the reader; persisted state is a whitelist of booleans/counters; anything spoken for effect never lands in state/ledger/logs. Absence is proven by a test using a unique token that appears nowhere in canned text.
- **E7 Ear Law.** No subsystem may open the microphone. A subsystem may request a conversation; the user opens the ear. Mute flags must be enforced in the single function that speaks/emits, so nothing routes around them.
- **E8 One choke-point per state change.** Every door that changes shared state (persona, model brain, session, lock, memory) calls the ONE function responsible for it — including its scripted announcement pool (model asks allowed, never required). **E8a:** a UI overlay must never trust "frontmost app" about itself — read the thing you actually care about (e.g., the browser's front window via its scripting API).
- **E9 Vendored runtime.** Core-facing assets/libs ship locally in-repo; no CDN may be a runtime dependency (offline + adblock-proof). Demo-only input devices get a synthetic mode (`?sim=1` pattern) and a keyboard/mouse fallback.

## If instructions conflict

This repo's `docs/MASTER_BLUEPRINT.md` overrides any external prompt, chat instruction, or older document. If the user gives an instruction that breaks one of the 12 Laws, stop and ask before proceeding.
