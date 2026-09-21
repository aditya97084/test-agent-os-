# AgenticOS — Deployment Handoff Package

> Ye ek **self-contained handoff package** hai. Is repo ko laptop pe le jao, coding agent (Claude Code / Codex / Antigravity) ko `docs/BRIEF_PHASE_0.md` paste karo — agent audit + infra + Phase 0 skeleton turant deploy karega. Koi bhi doc alag se match karne ki zaroorat nahi; ye package hi **single source of truth** hai.

## Kya-kya hai isme

| File | Kaam |
|---|---|
| `HANDOFF.md` | **Pehle ye padho.** Step-by-step: laptop pe kaise le jana hai, kya install karna hai, agent ko exactly kya bolna hai |
| `AGENTS.md` | Rules jo coding agent ke liye non-negotiable hain (Claude Code / Codex ise auto-read karte hain) |
| `docs/MASTER_BLUEPRINT.md` | Final locked architecture — dono documents ka merged, zero-contradiction blueprint + coverage map (ek bhi purana phase miss nahi hoga) |
| `docs/BRIEF_PHASE_0.md` | Agent ko abhi paste karne layak brief — Phase -1 (audit) + Phase 0 (core skeleton) only |
| `docs/AUDIT_PROMPT.md` | `D:\AI_SYSTEM` audit ka exact prompt (WORKING/PARTIAL/MOCK/BROKEN/MISSING/DO_NOT_REUSE) |
| `docs/ACCEPTANCE_TESTS.md` | Har phase ka pass/fail gate + final Tests 1–10 |
| `docs/RESEARCH_TRACK_JULIAN_GOLDIE.md` | Parallel research track (Track 2) — forensic prompt, core build ko block nahi karta |
| `contracts/*.json` | Task state / Agent registry / Workflow node — machine-readable schemas (agent inhi ko implement karega) |
| `contracts/worker_contract.md` | Worker interface (Python + TypeScript dono) |
| `deploy/` | **Real, runnable** infra: docker-compose (Temporal + Postgres/pgvector + Redis + LiteLLM), LiteLLM config with actual model routing (Sonnet 4.6 primary → MiniMax-M3 fallback → Ollama local), `.env.example`, setup/verify scripts |

## Locked model stack (real, verified IDs — Sept 2026)

| Role | Model | Provider |
|---|---|---|
| Planning / orchestration primary | `claude-sonnet-4-6` | Anthropic |
| Planning / coding secondary + fallback | `MiniMax-M3` (1M ctx) | MiniMax — `https://api.minimax.io/v1` |
| Fast/cheap calls | `claude-haiku-4-5-20251001`, `MiniMax-M2.7-highspeed` | — |
| Vision | `gemini/gemini-2.5-flash` (verify current ID) | Google |
| Local free fallback | `ollama` (qwen3 / llama3.x) | Ollama |

Routing is done by **LiteLLM Proxy** (`deploy/litellm/config.yaml`) — app code kabhi model ID hardcode nahi karega, sirf group alias bhejega: `planning`, `coding`, `research`, `fast`, `vision`, `local`.

## Golden rule (sab kuch yaad na rahe to bas ye)

**Hermes = dimaag (Layer 2). Temporal + Gateway = reedh ki haddi (Layer 1, durable). LiteLLM = haath-pair chunne wala. Claude/Codex/Antigravity = replaceable workers. Obsidian + Postgres = yaad. Dashboard = sabse aakhri chehra.** Is order ko kabhi ulta mat karna — warna 3D spaceship without engine.

## Quick start (human)

```bash
git clone <this-repo> && cd test-agent-os-
cp deploy/.env.example deploy/.env    # keys bharo (Anthropic, MiniMax)
pwsh deploy/scripts/setup.ps1         # (Windows) — Linux/mac: deploy/scripts/setup.sh
pwsh deploy/scripts/verify.ps1        # saare services + Sonnet + MiniMax live ping
```

Phir `docs/BRIEF_PHASE_0.md` ko Claude Code/Codex me paste karo. Bas.

> ⚠️ `.env` kabhi commit mat karna (`.gitignore` already handles it). Rule #7.
