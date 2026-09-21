# MASTER_BLUEPRINT — AgenticOS (FINAL, LOCKED, MERGED)

> **Status:** Single source of truth. Is document ke aage koi bhi purana document, chat instruction, ya external prompt authority nahi rakhta (exceptions: none). Third-party research (e.g. Julian Goldie forensic track) isko *inform* kar sakta hai, *replace* nahi.
> **Language note:** Architecture English me locked hai (coding agents ke liye); Hinglish notes human reader ke liye.

---

## §1. Mission

Build a local-first, free-first, modular **Autonomous Agentic Operating System** — ek personal/company digital OS, na ki "ek aur AI chatbot wrapper".

Flow (locked):

```
Speak naturally → Gemini Live → Hermes → Understand/Plan/Delegate
  → select agent+tool+workflow → execute → track → verify → store memory → continue autonomously
```

Two supported modes, always visible in UI:
- **DIRECT** — user picks an agent (Claude Code / Codex / Antigravity…) and chats with it in the dashboard.
- **AUTONOMOUS** — user gives Hermes a goal; Hermes decomposes, assigns, monitors, fails-over, checkpoints, verifies, memorizes.

Core philosophy: **System over Model.** (See `AGENTS.md` 12 Laws — they are part of this blueprint.)

## §2. The central contradiction — and its locked resolution

Old Doc 1: *"Hermes = Central Orchestrator" (Hermes sab kuch chalata hai).*
Old Doc 3: *"Hermes ko poora OS mat banao; worker level par rakho."*

**Both were about different layers. LOCKED DECISION — split orchestration into two layers:**

```
┌─────────────────────────────────────────────┐
│ LAYER 2 — COGNITIVE ORCHESTRATOR: HERMES     │  ← "brain" (Doc 1 correct)
│ talks to user, plans, delegates, recalls     │
└──────────────────┬──────────────────────────┘
                   │ delegates via API (stateless calls)
┌──────────────────▼──────────────────────────┐
│ LAYER 1 — DURABLE EXECUTION: Gateway+Temporal│  ← "spine" (Doc 3 correct)
│ task state · checkpoint · retry · resume     │
│ never "thinks", never dies with a task       │
└──────────────────┬──────────────────────────┘
        ┌──────────┼──────────┬───────────┐
    Claude Code   Codex   Antigravity   ...replaceable workers
```

Consequences (hard):
- Hermes gets **privileged status** for conversation/voice answers/planning — but is **not a durability dependency**.
- If Hermes crashes, quota-exhausts, or restarts mid-task → Temporal keeps the task; a worker resumes from checkpoint.
- Every long/critical task Hermes decides on **executes inside a Temporal workflow**. Hermes must never run long work in its own loop/chat context.

## §3. Minor contradictions — resolved

| Topic | Doc 1 said | Doc 3 said | **LOCKED** |
|---|---|---|---|
| Build start | D:\AI_SYSTEM integration | Phase 0 = audit first | **Audit first, then integrate** — without the audit you can't know what to preserve |
| n8n | not mentioned | integration layer | **Include** — external webhooks/social/CRM only; never core reasoning |
| Dashboard timing | Phase 27 (late) | Phase 7 (last) | Agree — **after** backend completes |
| Memory | Obsidian + Graphiti | 4-layer model | **4-layer wins** (Working/Episodic/Semantic/Human-readable); Obsidian = the human-readable layer; graph = an index inside semantic |
| Video tools | evaluate all four | Remotion+FFmpeg first | **Remotion+FFmpeg core now**; OpenMontage/HyperFrames arrive via Evolution Engine sandbox (Phase 9 rule) |
| Julian Goldie | not mentioned | not mentioned | **Parallel Track 2** — informs Evolution Engine + content phases; never blocks core build |

No other conflicts exist — the docs reinforce each other (checkpoint/failover, approval-gated publish, free-first, no monolith).

## §4. FINAL unified architecture

```
                        FOUNDER
                          │ voice / text / dashboard
                     GEMINI LIVE            (interface only; runs no OS logic)
                          ▼
                  ┌───────────────┐
                  │    HERMES     │ ◄── Layer 2: cognitive orchestrator
                  │ planner+brain │     (adapter, not the backend itself)
                  └──────┬────────┘
                          │ delegates via API
                  ┌───────▼────────┐
                  │ GATEWAY FastAPI│ ◄── Layer 1 entry: auth, intent intake,
                  │  + TEMPORAL    │     event stream, task CRUD
                  └───────┬────────┘
       ┌───────────┬──────┼────────┬─────────────┐
 MODEL ROUTER  AGENT REGISTRY  TOOL REGISTRY  MEMORY SERVICE
 (LiteLLM:     (health check,   (Playwright,    (Postgres+pgvector
 Sonnet/M3 →    capability       ffmpeg,         + Obsidian mirror
 local chain)   routing)         remotion,       + Redis working mem)
       │             │           gh, browser…)
  ┌────┴────┬────────┴─────────┬─────────────┐
Claude Code Codex        Antigravity    OpenCode / Local(Ollama)
  └────────────┴────────────────┴────────────┘
                          │
                  WORKSPACES / GIT
                          ▼
                     ARTIFACTS ──► GALLERY / KANBAN / PIPELINE VIEW
                          ▼
                  DASHBOARD (UI — Phase 10, always last)
                          ▼
                  EVOLUTION ENGINE
        GitHub discovery → sandbox → human approval → integrate
        (Julian Goldie research feeds here as JAG-xxx backlog)
```

## §5. Locked tech stack (zero ambiguity)

| Layer | Technology | Why |
|---|---|---|
| Desktop shell | Tauri 2 + React + TypeScript | lightweight native cross-platform control |
| Backend API | Python FastAPI + WebSocket/SSE | unified API + live streaming |
| Durable execution | **Temporal** | crash-proof resume — THE core fix |
| Model routing/failover | **LiteLLM Proxy** | ordered provider fallback chains, retries, cooldowns, cost logs |
| Cognitive orchestrator | Hermes (as adapter via API) | planning, delegation, personal context, learning loop |
| Coding workers | Claude Code, Codex, OpenCode, Antigravity | registered behind one Worker interface |
| Browser control | Playwright persistent profile (DOM-first, vision only when DOM fails) | auditable, per-action log |
| Desktop control | Windows UI Automation + PowerShell (API/CLI → a11y tree → keys → vision → confirm) | least-fragile route first |
| Database | PostgreSQL 16 + pgvector | task state + semantic memory |
| Cache/events | Redis 7 | live status, working memory, locks |
| Human memory | Obsidian vault (Markdown) | user-readable mirror of Postgres truth |
| External automation | n8n (compose profile `integrations`) | webhooks/social/CRM edges only |
| Media pipeline | Remotion + FFmpeg | programmable composition; sandboxed additions later |
| Local models | Ollama (qwen3/llama/mistral) | free-first fallback |
| Voice | Gemini Live + faster-whisper + Piper (local) / ElevenLabs (premium) | cloud premium, local floor |
| Models (locked, verified 2026-09) | **primary `anthropic/claude-sonnet-4-6` · failover `MiniMax-M3` @ api.minimax.io/v1 · fast `claude-haiku-4-5` / `MiniMax-M2.7-highspeed` · local `ollama/qwen3`** | high-model quality with durable fallback — configured in `deploy/litellm/config.yaml` |
| Packaging | Docker Compose + Windows installer | reproducibility |

## §6. Repo / disk layout (LOCKED — one tree, merged from both docs)

Root stays `D:\AI_SYSTEM\AgenticOS\` (Doc 1). Inside it, the service-oriented tree wins (Doc 3). Existing `D:\AI_SYSTEM` folders (Apps/CLI/Skills/Repositories/Configs/Caches/Models/Shared/Workspace) are **preserved as-is**; `AgenticOS/` is the only new directory at that level.

```
D:\AI_SYSTEM\AgenticOS\
├── AGENTS.md  HANDOFF.md  README.md        # this package (already here)
├── docs/                                   # blueprint, briefs, AUDIT_REPORT, PROGRESS
├── contracts/                              # JSON schemas — source of truth
├── deploy/                                 # compose, litellm, scripts, .env.example
├── apps/
│   ├── desktop/        # Tauri 2 + React (Phase 10 only)
│   └── web/            # browser-served variant of same UI
├── services/
│   ├── gateway/        # FastAPI: intake, task CRUD, WS events, approval gates
│   ├── orchestrator/   # Temporal workers: workflow defs (durable, no LLM logic)
│   ├── model-router/   # LiteLLM client + group aliases + health probes
│   ├── memory-service/ # 4-layer memory + Obsidian sync + pgvector
│   └── artifact-service/
├── workers/            # hermes/ coding/ research/ browser/ desktop/ voice/ media/ publishing/
├── packages/           # contracts client, tool-sdk, agent-sdk, ui-kit
├── workflows/          # declarative pipeline definitions (YAML/JSON nodes)
├── skills/             # SKILL.md packs, registry-indexed (links D:\AI_SYSTEM\Skills)
├── memory/             # Obsidian vault: 00_System 01_Projects 02_Daily_Logs 03_Knowledge_Base 04_Tasks_Archive 05_User_Preferences
├── config/             # app config (no secrets!) — model_groups.yaml etc.
├── data/  logs/  artifacts/  sandbox/  tests/
```

## §7. BUILD ORDER — final merged sequence (Doc1's 34 steps + Doc3's phases in ONE ladder)

Each phase lists its **acceptance test** — the only definition of done. Full detail in `docs/ACCEPTANCE_TESTS.md`.

| Phase | Content (merged) | Acceptance gate |
|---|---|---|
| **-1** | **EXISTING SYSTEM AUDIT** — scan all of `D:\AI_SYSTEM`; classify every file/component WORKING/PARTIAL/MOCK/BROKEN/MISSING/DO_NOT_REUSE; delete nothing | `docs/AUDIT_REPORT.md` exists; user explicitly confirms preserve-list |
| **0** | **CORE SKELETON** — Tauri shell stub + FastAPI Gateway + Postgres + Redis + Temporal wired (compose is already in `deploy/`); task create → run → state visible | kill app mid-task → reopen → **resumes at same step** |
| **1** | **MODEL + AGENT LAYER** — LiteLLM groups live; Hermes adapter; Claude/Codex/Antigravity/OpenCode adapters; Agent Registry + Health Manager; capability routing; direct-chat API for dashboard | disable primary model mid-run → secondary worker continues same task |
| **2** | **TASK STATE + CHECKPOINT + FAILOVER** — full `task_state.schema.json` enforced; checkpoint before every step; agent_history/failure_history | Claude fails mid-task → Codex resumes from checkpoint, **no repeated work** (git diff proves it) |
| **3** | **BROWSER + DESKTOP CONTROL** — Playwright persistent profile; Windows UIA; per-action audit log; approval gate before submit/send/delete | open → search → read → fill form → **approval screen appears before submit** |
| **4** | **VOICE + 4-LAYER MEMORY** — Gemini Live pipeline, Hinglish STT; working/episodic/semantic/Obsidian; source-backed recall; memory-write after every task | restart app → recall old project decision **with source shown** |
| **5** | **WORKFLOW ENGINE + KANBAN + PIPELINE** — workflow node schema (`contracts/workflow_node.schema.json`); Kanban BACKLOG→…→BLOCKED; pipeline viz; agents auto-pick cards | one YAML workflow runs end-to-end through ≥2 different agents; Kanban reflects states live |
| **6** | **SCHEDULER + 24×7 WORKERS** — cron/event/file-change/GitHub triggers; queue; retry engine; async (UI never freezes) | "daily 08:00 AI news research" survives **machine reboot** and executes next morning |
| **7** | **VIDEO/CREATIVE AUTOPILOT** — Research→Script→Storyboard→Assets→Remotion/FFmpeg→QA→Approval; Creative Bible per project; JAG-xxx backlog feeds **sandboxed** | one topic → approved MP4 + thumbnail + caption + metadata (no fake render — real file on disk) |
| **8** | **SEO + SOCIAL PUBLISHING** — official OAuth only; approval-gated publish; post receipts; analytics ingestion; SEO engine (keywords/SERP/gap/on-page/reporting) | draft → approve → published URL receipt returned → analytics ingested |
| **9** | **EVOLUTION ENGINE + COMPANY MODE** — GitHub discovery → sandbox → compare → human approval → registry update; Company org tree (Founder→Hermes Manager→dept→project→task→agent) | one discovered repo goes through full sandbox pipeline and is REJECTED or APPROVED with report |
| **10** | **DASHBOARD POLISH + 3D WORKSPACE** — Command Center, agent sidebar, direct chats, Gallery, Reports, cinematic-dark UI, optional 3D graph | every dashboard element backed by a real endpoint (spot-check API call trace) |
| **11** | **SECURITY HARDENING + FULL INTEGRATION** — secret scan, 12-laws audit, **Tests 1–10 of §9 all pass** | all green, evidence in PROGRESS.md |

**Never** reorder to "UI first". That is the one mistake that kills this project.

## §8. Coverage map — proof that nothing from the old docs is lost

Doc 1's Phases 1–36 → where they live in the §7 ladder:

| Old Doc1 phase | Lives in |
|---|---|
| 1 Foundation/layout | §6 + Phase -1/0 |
| 2 Hermes central | §2 (Layer 2) — Phase 1 |
| 3 Gemini Live | Phase 4 |
| 4 Agent Registry / 5 Agent Health / 8 Agent Router | Phase 1 |
| 6 Task State / 7 Failover | Phase 2 |
| 9 Direct agent chat | API in Phase 1, UI in Phase 10 |
| 10 Workflow engine / 11 Pipeline viz / 12 Kanban | Phase 5 |
| 13 Brain (Obsidian+graph) / 25 Memory-after-task | Phase 4 |
| 14 Skills / 15 Tool registry | Phase 1 (registries) + Phase 3 (tools) |
| 16–17 Video autopilot+command | Phase 7 |
| 18 Content autopilot | Phase 7/8 |
| 19 Social / 20 SEO | Phase 8 |
| 21 Research engine / 22 Self-improvement | Phase 9 |
| 23 24×7 engine | Phase 6 |
| 24 Company mode | Phase 9 |
| 26 Artifacts/Gallery | artifact-service Phase 2, Gallery UI Phase 10 |
| 27 Dashboard / 28 3D workspace / 29 Command bar / 30 Direct-vs-Autonomous | Phase 10 (mode switch in API from Phase 1) |
| 31 Security / 32 Free-first / 33 Testing | AGENTS.md laws + every phase gate + Phase 11 |
| 34 Build order | superseded by §7 (this ladder) |
| 35 No Orca core | §10 rule R3 |
| 36 Final acceptance | §9 tests 1–10, run at Phase 11 |

Doc 3's Phase 0–7 → mapped 1:1 into §7 rows (-1, 0, 1, 3, 4, 7, 8, 10). **Nothing dropped.**

## §9. Final acceptance suite (system isn't "complete" until all pass)

1. "Claude Code se website banao." → Claude executes, artifacts on disk.
2. "Codex se review karo." → Codex receives full project context (not chat).
3. Claude dies mid-task → checkpoint → Codex resumes → zero repeated work.
4. "Is video ko analyse karke similar style me video banao." → full pipeline runs; STYLE attributes extracted, no literal copy.
5. "YouTube ke liye ready karo." → SEO + thumbnail + metadata + preview → **human approve** → publish receipt.
6. "Har subah AI ki nayi khabrein." → recurring scheduler task survives reboot.
7. "Naya behtar open-source video tool dhoondo." → Evolution Engine proposes, sandboxes, reports, waits for approval.
8. "Poore project ko 24×7 monitor karo." → background monitors created.
9. Agent crashes halfway → task resumes (same as 3, but via process kill -9).
10. All cloud agents offline → local fallback serves simple tasks; queued criticals enter `WAITING_FOR_RESOURCE` (never `FAILED`).

Task lifecycle states (locked): `CREATED · PLANNING · RUNNING · WAITING_FOR_USER · WAITING_FOR_RESOURCE · RETRY_SCHEDULED · PAUSED · COMPLETED · FAILED_FINAL · CANCELLED`. A task is `FAILED` only when it is `FAILED_FINAL` with a human-readable reason in `failure_history`.

## §10. Extra standing rules

- **R1 Orca:** optional experiment only; never a core dependency. ❌ Gemini→Paperclip→Orca→Hermes chain; ✅ Gemini Live→Hermes→{Router, Memory, Workflows}.
- **R2 Model selection:** user says "Claude se karo" → respected; on unavailability, fallback per policy (Claude→Codex→Antigravity→OpenCode→local), recorded visibly (Law 4).
- **R3 Hermes privilege:** voice answers, planning, personal context = Hermes. Long/critical execution = always inside Temporal (per §2).
- **R4 Skill isolation ban:** all agents read shared `skills/` registry; no per-agent private knowledge copies.
- **R5 Creative Bible:** every creative project keeps `character.json · brand.json · visual-style.json · voice-profile.json · negative-rules.json · reference-assets/` — style analysis extracts *attributes*, never copies content.
- **R6 Publishing:** official platform OAuth APIs are primary; unofficial login automation is not an allowed primary route; every publish needs an approval record + receipt artifact.
- **R7 Research discipline:** third-party findings (Julian track) enter only as `JAG-xxx` backlog items with FACT/INFERENCE/UNKNOWN tags, then Phase 9 pipeline. UI-without-mechanism proposals are auto-rejected.

## §11. Working with this document

- Implementers: read §2, §5, §6, §7, then `docs/BRIEF_PHASE_0.md`. Contracts in `contracts/` are normative.
- Progress: `docs/PROGRESS.md`, evidence-tagged (Law 11).
- Infra: already real in `deploy/` — `setup.ps1/sh`, LiteLLM config with live Sonnet/MiniMax/Ollama routing, health verification. Boot it before coding; verify before "done".
