# PHASE_BRIEFS — how every remaining phase gets built (paste-ready)

> **Kaise chalta hai ye poora (operating loop — har phase pe exactly ye 6 steps):**
> 1. Infra verify: `pwsh deploy/scripts/verify.ps1` (ya `verify.sh`) → PASS hona chahiye.
> 2. Us phase ka brief paste karo (neeche har phase ka ek chhota block hai — poora paste karo, edit mat karo).
> 3. Agent build karta hai; tum interrupt mat karo (long multi-step work ke liye bana hai).
> 4. Agent `preflight.py` chalata hai + phase acceptance test → real output `docs/PROGRESS.md` me paste karta hai (E1).
> 5. Tum PROGRESS.md padho — jo FACT-tagged output ke saath hai wahi maano, baki sab hawa hai (Law 11).
> 6. Commit tag `agentos-phi{N}` → agli phase. **Ek time pe ek phase.**

Effort estimates (INFERENCE — field data se tune karna, vibes se nahi, E4): Phase 0–2 = 3–5 din, Phase 3–6 = ek hafta, Phase 7–9 = hafta-dedai, Phase 10–11 = hafta. Total ~4–6 weeks, agent-assisted, roz 2–4 ghante tumhari review + approval gates.

Jo cheezein har phase me **already fixed** hain aur agent unhe dobara design nahi karega: architecture/contradiction-resolution (§BLUEPRINT), tree layout, contracts, model routing (`deploy/litellm/config.yaml`), E1–E9 rules, JAR/JAG backlog assignments. Agent sirf **us phase ka slice** implement karta hai.

---

## Phase 0 → already covered by `docs/BRIEF_PHASE_0.md` (audit + skeleton + preflight). Skip here.

## PHASE 1 — Model + Agent layer
```text
Execute Phase 1 from docs/MASTER_BLUEPRINT.md §7 + docs/PHASE_BRIEFS.md §"PHASE 1". Read AGENTS.md first.

Build:
1. packages/model-router — single LiteLLM client for ALL model calls. Group aliases only (planning/coding/research/fast/vision/local). Reads LITELLM_MASTER_KEY from env. Per-call cost/token log into task cost fields. No raw model id anywhere outside config (Law 1).
2. Agent Registry service — Postgres table from contracts/agent_registry.schema.json, CRUD + GET /v1/agents. Seed entries: claude-code, codex, opencode, antigravity, hermes, local-ollama (GUI-only flags honestly marked; no fake adapters — Law 10).
3. Health Manager — prober per registry entry every 30 s: CLI present? auth valid? provider reachable? last_ok/last_fail. States strictly from the 10-value enum. /v1/agents drives health dots.
4. Worker adapter base implementing contracts/worker_contract.md (Python). Ship REAL adapters for Claude Code (`claude -p` stream-json), Codex (`codex exec`), OpenCode; Antigravity = GUI-launch wrapper marked PARTIAL until a headless API exists; Hermes adapter = planning/delegation API client (Layer 2, per blueprint §2 — no long-running logic inside it).
5. Capability router — picks agent by capability + fallback_order, appends agent_history + failure_history + Requested/Actual/Reason on any swap.
6. Brain swap (E3 + JAR-008/015): explicit known-id registry (config/model_aliases.yaml: astra/sonnet/minimax/haiku… → exact LiteLLM deployment ids). POST /v1/model swap: near-miss → refuse + list what exists; runtime-only (restart reverts to config); every door (voice/API/UI) calls ONE swap function with rotating scripted announcement pools.
7. Update preflight.py: new checks — registry seeded, health probes running, each group answers, swap refusal path returns 4xx with list.

Acceptance (run + paste output): kill/invalid primary deployment mid-run → task continues via MiniMax failover with swap recorded; "switch to sonnet 99" → refusal listing real ids; restart → config brain restored; /v1/agents matches reality (try removing a CLI from PATH). Preflight all-pass. Update PROGRESS.md with tags.
```

## PHASE 2 — Durable task state + failover
```text
Execute Phase 2 per MASTER_BLUEPRINT §7 + PHASE_BRIEFS §"PHASE 2".

Build:
1. Enforce task_state schema on EVERY write (pydantic models generated from contracts/) — malformed state = reject loudly, never coerce.
2. Checkpoint-before-step in orchestrator: Temporal upsert Search Attribute + Postgres checkpoint row (step, attempt, artifacts, selected group, git commit) BEFORE invoking any activity.
3. Full lifecycle states from §9 enum; WAITING_FOR_RESOURCE + RETRY_SCHEDULED paths real (scheduler re-arms; no silent FAILED).
4. artifact-service skeleton: content-addressed store under artifacts/, versions, task linkage; workers return artifact refs only.
5. /v1/tasks complete: create/update-pause/resume/cancel/depend, agent_history + failure_history writers, swap recorder for UI chip.
6. Orchestrator GET /diag (E2): booleans/counters only — queue depth, active steps, workers alive, last checkpoint age; read from RUNNING process.
7. preflight.py += checkpoint-freshness check + lifecycle-state reachability.

Acceptance: real coding-ish task on Claude-adapter worker → SIGKILL worker at step 3 → Temporal reschedules to Codex adapter → resumes from checkpoint; git diff proves zero repeated work; /diag shows the swap; preflight all-pass; PROGRESS.md updated.
```

## PHASE 3 — Browser + desktop control
```text
Execute Phase 3 per blueprint §7. Build:
1. Playwright persistent-profile service (tool registry entry `browser.playwright`): own profile dir under data/, DOM-first actions (navigate/click/read/fill/extract), screenshot-on-error, downloads tracked into artifacts/.
2. Per-action audit log: every action row {task_id, ts, action, target-selector/url-host, result, screenshot-ref} in Postgres. Vision-based clicking ONLY when DOM fails, and logged as mode=vision.
3. Windows/desktop: UIA + PowerShell runners behind same Worker contract; API/CLI route preferred when target app has one (registry field invocation).
4. Approval-gate middleware: mutating/submitting/publishing/deleting actions → task enters WAITING_FOR_USER with an approval request (payload preview + approve/reject endpoints). Deny path tested. Default ON per Law 5; per-workflow overrides require recorded user decision.
5. JAR-006 vision freshness contract: any frame/screenshot passed to a model carries {captured_at, source_alive}; stale/ended-source = honest error, never answer from memory. MIME from actual bytes.
6. "Take control" API: pauses the browser worker instantly, handoff event to UI.
7. preflight += real navigation probe (example.com), audit-row check, approval path check.

Acceptance: scripted flow open→search→fill→[HALTS at approval]→approve→submit; kill browser mid-flow → task WAITING_FOR_RESOURCE, resumes; share/stale tests per JAR-006; all actions visible in audit log; preflight all-pass.
```

## PHASE 4 — Voice + 4-layer memory
```text
Execute Phase 4 per blueprint §7. Build:
VOICE (3 channels, one pipeline):
1. Channel registry: gemini-live (cloud, GEMINI_API_KEY), local (faster-whisper STT + Piper TTS, Ollama-side optional), web-lite (browser Web Speech — FINISH_MS=900 single named constant; interrupt words 'stop'/'wait' bypass buffer; ?mute=1 enforced in the ONE speak() function; listening/thinking/speaking state stream over WS; E7: no server-side code path may open a mic).
2. Hinglish normalizer; transcript shown as text before executing anything risky.
3. Voice intents map to existing task API (voice = channel, never its own brain).
MEMORY (4 layers, Postgres truth, Obsidian mirror):
4. Working: Redis TTL context per task; Episodic: episodes table (task outcome, decisions, discoveries, files, lessons, errors — written by a memory-writer activity at task end, Doc1 P25); Semantic: pgvector embeddings + Tier-0 keyword+title scorer as fallback/first tier (JAR-001); Human: Obsidian vault under memory/ with 00–05 folders, write-through sync, vault edits on disk indexed back within 60 s (watcher).
5. /v1/memory/capture (JAR-005): phrase triggers configurable; write .md + embed + graph-insert ATOMICALLY; immediately retrievable; failure → loud response, never silent forget. Live graph node birth event over WS for UI.
6. Recall API returns {answer_basis, sources:[{id,path,date,confidence}]} — source shown always (U1 data side).
7. Persona: config/persona.md = single block injected as Hermes system prompt (JAR-004); greetings read live counts from /diag, never hardcoded.
8. preflight += voice pipeline probe (STT of a generated wav, TTS roundtrip, web-lite config), capture→immediate-query E2E, embedder-off fallback test.

Acceptance: restart → yesterday's decision recalled with correct source; pause-timing voice test; capture test; embedding-down search still ranks (FACT: log shows tier-0); mute test silent; preflight all-pass.
```

## PHASE 5 — Workflow engine + Kanban + pipeline
```text
Execute Phase 5. Build:
1. workflows/*.yaml loader validating EVERY node against contracts/workflow_node.schema.json; workflow versioning (immutable @n, task pins version).
2. Node executor as Temporal child workflows: inputs resolution (node:/task:/memory: refs), validation checks (file_exists/json_valid/tests_pass/human_approval/…), per-node retry+fallback to next agent, checkpoint per node.
3. /workflows engine API + GET /v1/pipeline/{task_id} stage-states stream (drives future viz UI; no UI now).
4. Kanban: DB-backed columns BACKLOG/IN_PROGRESS/REVIEW/APPROVED/DONE/FAILED/BLOCKED, card = task projection; workers CLAIM cards (atomic lease via Redis lock, prevents double-pick).
5. Manual→Assisted→Automated promotion: completed ad-hoc task traces can be distilled into a workflow draft via a `promote-task` command — always lands as REVIEW card, human approves before it becomes an executable workflow (Law 5/6).
6. preflight += sample two-node workflow dry-run + kanban claim/lease check.

Acceptance: youtube_video.yaml (research→script→storyboard→qa) runs E2E across ≥2 agents; kill at node-2 → fallback agent continues same node attempt count preserved; lease test proves no double-execution; promote draft appears as REVIEW card; preflight all-pass.
```

## PHASE 6 — Scheduler + 24×7 + personal organs
```text
Execute Phase 6. Build:
1. Schedule service on Temporal schedules (durable, survives reboot): cron/interval/event/file-watch/GitHub-watch triggers; missed-run policy = log MISSED, no pile-up.
2. E5 Monitor base class for ALL watchers: cheap local poll (diff/mtime/counter) → threshold event → ONE model escalation + cooldown + per-monitor cost ceiling; idle = zero calls (cost log proves it).
3. FOCUS engine (JAR-009…013) as durable workflow: 1 s tick loop; frontmost read via OS adapter FRESH each tick (no cached APIs); target attach = settle-announce-fallback (2-tick settle, audible 'Locked on', 45 s app-only fallback, never guess background/2nd monitor); tab lane = host-hash only; grace 800 ms; 3-tier escalating callout pools (≥4 lines/tier), nag cadence voice-settable, snooze, excuse=refund+quiet-until-back, Jarvis tab = home base; report card minutes-on-target + ≥85 % streak; ledger: aggregates-only whitelist keys (schema-enforced + test).
4. Identity privacy by structure (E6): reader compares names and DISCARDS; state/ledger/logs carry only booleans/counters; spoken labels one tick, stored nowhere; unique-token test. sense.pose organ: local landmarks→booleans, sustain 700 ms/cooldown 30 s/absence 12 s, relief valve 180 s; enable = recorded approval; E7 mic law enforced.
5. GET /focus/diag + probe harness (E2): booleans-only from live process; viewport assertion.
6. preflight += schedule-fire test + focus diag + ledger rejection test.

Acceptance: reboot-machine test (session + schedule survive); idle watch = 0 cost; drift → callout ≤3 s with host-name label, then grep-everything proves label absent (unique token); deferred-lock flow audible; ear-law test; preflight all-pass.
```

## PHASE 7 — Creative/Video studio
```text
Execute Phase 7. Build (as workflow + workers, blueprint §7):
1. Pipeline nodes: topic/url → research (evidence + source list) → content strategy → script → storyboard → assets (image/TTS voice via Piper/ElevenLabs-from-config, local-first per Law 8) → assemble (Remotion project + FFmpeg: encode/captions via whisper alignment/loudness) → QA (ffprobe + subtitle-overflow + duration checks) → approval card → publish-ready.
2. Reference-style analysis mode (Doc1 P17): from a YouTube URL take metadata + permitted transcript → extract STYLE ATTRIBUTES (hook type, pacing, shot-length distribution, text density, transitions) — never copy content; brief includes originality note (R5).
3. Creative Bible per project (character/brand/visual-style/voice-profile/negative-rules/reference-assets) injected into every creative step; versioned.
4. Every stage = checkpointed workflow node; re-run resumes at failed stage (no re-render of completed assets; content-hash reuse).
5. JAR/backlog intake: research tracks (JAG-*, approved subset) appear as optional node presets — never auto-enable.
6. Approval-gated completion → flags publish-ready for Phase 8.
7. preflight += tiny render E2E (10 s clip) in CI sandbox.

Acceptance: one topic → real final.mp4 (ffprobe>0), thumbnail, caption.txt, metadata.json on disk; kill mid-render → resume; QA failure path produces actionable error not silent pass; approval record required; preflight all-pass.
```

## PHASE 8 — SEO + social publishing
```text
Execute Phase 8. Build:
1. SEO engine worker: keyword research + intent classification + SERP analysis (approved source per config: Search Console API > official APIs > approval-gated scraping) + content-gap vs owned inventory + on-page audit (headings/schema/links/meta) + YouTube SEO (title/desc/tags/chapters) + reports into artifacts.
2. Social adapters: YouTube Data API, LinkedIn API, Meta Graph (FB/IG), X API — official OAuth only (R6); credential flow via deploy/.env + OS keychain; per-platform capability table honest (what their API actually allows; missing = feature absent, no UI lie).
3. Draft→schedule→PUBLISH only after approval record → post receipt {url, id, ts, payload-hash} artifact → analytics ingest monitor (E5: cheap poll, report on change) → memory episode.
4. n8n (integrations profile) for webhook edges/CRM only; Temporal stays core (no reasoning there).
5. preflight += dry-run publish to sandbox channel + receipt check.

Acceptance: publish without approval row → API 403 (test); full loop draft→approve→receipt→analytics on a sandbox/own account; unpermitted action (comment automation etc.) refused with policy reason; preflight all-pass.
```

## PHASE 9 — Evolution engine + company mode
```text
Execute Phase 9. Build:
1. Discovery: scheduled GitHub/HN/docs scan per categories (video, agents, SEO, memory, MCP); scoring = license + activity + stars-trend + overlap-with-current-stack; shortlist cards only (never auto-clone into prod).
2. Sandbox runner: isolated container profile, pinned version, smoke-test suite generated per category, network egress policy, resource caps; verdict report {capabilities, risks, compatibility, replace-vs-coexist}.
3. Approve→integrate pipeline: human approval card → registry entry (agent/tool/skill) with version pin; skill packs into skills/ with SKILL.md contract; rollback = one command, tested.
4. Backlog processor: pulls JAG-*/JAR-* items marked sandbox (JAR-H1 hands experiment goes through here); status flips in yaml via PR only.
5. Company Mode: org tree (Founder→Hermes Manager→departments→projects→tasks), goals cascade downward with roll-up progress upward; per-dept Kanban = existing Kanban + owner field; department "bots" are capability groups + prompts, not new processes.
6. preflight += sandbox smoke E2E on a real tiny MIT repo.

Acceptance: one discovered repo completes discover→sandbox→verdict→REJECT path (with reasons) AND on approval integrates + rollback works; experiment flag off by default; company tree renders from real task data (no mock orgs); preflight all-pass.
```

## PHASE 10 — Dashboard (finally — the face, not the brain)
```text
Execute Phase 10. Build (Tauri + React, everything from live APIs; no new backend features — if UI needs data that doesn't exist, that's a bug in a previous phase, report it):
1. Command Center: mode switch DIRECT/AUTONOMOUS, active project, pipeline rail (live stage states), LIVE activity feed, agent health chips, cost/queue widgets.
2. Direct chats: per-agent panel (chat/files/terminal-bridge/git/logs/status) hitting adapters + events over WS; autonomous tasks: goal box → plan view with checkpoints and history.
3. Kanban board + drag with lease API; pipeline graph view (React Flow) reading /v1/pipeline; node inspector = agent/prompt/io/logs/duration/retries/checkpoint.
4. Gallery (artifacts: image/video/doc/code/report/data — approve/edit/reject wired to real endpoints), Memory browser (4 layers, sources visible, forget/edit → memory API), Reports (tasks, cost, streak, SEO analytics).
5. Honesty rules: U1 provenance viz (single source → focus it; ≥4 → light set; small talk → camera frozen), U2 no narrating on-screen text, live counters only, no decorative fake activity.
6. 3D workspace optional flag: notes graph (build-index equivalent from memory service, numeric node-id contract per JAR-P01 adaptation) with slow idle rotation, click-fly. Gesture hands ONLY if JAR-H1 passed Phase 9 (default OFF, ?sim=1 test mode + mouse fallback, vendored libs — E9/U4/U5).
7. Persona greeting block (config/persona.md) with real counts + time of day.
8. preflight += every UI control's endpoint trace + vendored-assets offline boot check.

Acceptance: network-trace audit: zero dead buttons; disconnect API → UI shows honest OFFLINE not fake data; preflight all-pass; PROGRESS.md.
```

## PHASE 11 — Security hardening + full integration
```text
Execute Phase 11. Build/verify:
1. Secret hygiene: gitleaks full-history scan clean; log redaction proof (grep capture test); .env perms; key rotation runbook doc; anything browser-side scanned for key material = zero hits (hard-fail check in preflight).
2. Network: compose ports all 127.0.0.1 (assertion test), CORS pinned, gateway bearer check, WS auth; optional Tailscale doc for remote (never LAN-expose).
3. Policies: approval-gate coverage map (every mutating tool listed + gated); Law 5 defaults not overridable by workflow yaml without recorded user decision; destructive-op dry-run default.
4. Supply chain: deps pinned+hashes, vendor dir checksum manifest, Phase 9 process documented as the only import path.
5. Resilience drill: full §9 Tests 1–10 incl. machine-reboot and offline runs (document results in PROGRESS.md, evidence-tagged).
6. Windows installer: Tauri bundle + compose sidecar bootstrap + first-run wizard (keys, vault path, agent CLIs detected) — runs on a CLEAN profile test.
7. Final preflight = every accumulated check green, N warn max on missing optional keys.

Acceptance: all §9 tests pass with pasted outputs; installer works on clean machine; secret scan zero hits; this doc's preflight count printed. Only THEN may any file call the system "v1".
```

---

**Track 2 (Julian) + koi bhi naya external pack:** build ko block nahi karta — `docs/RESEARCH_TRACK_JULIAN_GOLDIE.md` ke rules se recon → JAG/JAR backlog → Phase 9 gate. (JAR packs ka full pass ho chuka hai: `docs/research/JARVIS_HOLO_PACK_RECON.md` + `workflows/backlog/jar-backlog.yaml`.)
