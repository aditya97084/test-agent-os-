# HANDOFF.md — Laptop pe le jaane aur turant deploy karne ka exact process

Ye package isliye bana hai ki tumhe **kuch bhi khud assemble na karna pade**. Repo hi deployment unit hai.

---

## 0. Laptop pe kaise laana hai (choose one)

```bash
# Option A — git (recommended)
git clone <this-repo-url> agenticos-handoff && cd agenticos-handoff

# Option B — zip
# is repo ka zip download karo, extract karo. Koi build step nahi chahiye —
# deploy/ ke andar sab plain files hain.
```

**Target placement:** repo ko copy karo → `D:\AI_SYSTEM\AgenticOS\`
(repo ke andar ki structure hi final layout hai; Phase 0 me agent isi ke hisaab se code isi tree me likhega — `docs/MASTER_BLUEPRINT.md` §6 dekho.)

## 1. Laptop prerequisites (ek baar)

| Chahiye | Kyun | Install |
|---|---|---|
| Docker Desktop (WSL2 backend) | Temporal, Postgres, Redis, LiteLLM chalane ke liye | docker.com/products/docker-desktop |
| Python 3.12+ | FastAPI gateway + workers | winget install Python.Python.3.12 |
| Node 22+ + git | Tauri/React UI (baad me) + repo | winget install OpenJS.NodeJS.LTS ; Git for Windows |
| Claude Code **ya** Codex CLI | Build agent | `npm i -g @anthropic-ai/claude-code` (ya `npm i -g @openai/codex`) |
| API keys | Model access | neeche step 2 |

> Free-first note: agar MiniMax/Anthropic keys abhi nahi hain, infra **phir bhi** boot hoga — LiteLLM local Ollama fallback ke saath `local` group always answer karega. Premium models keys aate hi active ho jayenge (reload compose).

## 2. Secrets setup

```bash
copy deploy\.env.example deploy\.env      # Windows
# nano/vim: deploy/.env pe jaake bharo:
#   ANTHROPIC_API_KEY=...   → console.anthropic.com (Settings → API Keys)
#   MINIMAX_API_KEY=...     → platform.minimax.io  (OpenAI-compatible endpoint use karte hain)
#   GEMINI_API_KEY=...      → optional, abhi sirf vision group ke liye
#   LITELLM_MASTER_KEY=...  → koi bhi strong random string (khud ka gateway key)
```

`.gitignore` already excludes `deploy/.env`. **Commit mat karna. Kisi agent ko .env ka content kabhi mat dikhana** — agent sirf variable names se kaam karega (Law 7).

## 3. Infra deploy (30 second)

```powershell
# Windows (PowerShell 7)
pwsh deploy/scripts/setup.ps1      # .env check → docker compose up → health wait
pwsh deploy/scripts/verify.ps1     # Postgres/Redis/Temporal/LiteLLM + LIVE Sonnet/MiniMax ping
```
```bash
# Linux/macOS
bash deploy/scripts/setup.sh && bash deploy/scripts/verify.sh
```

`verify` me `PLANNING: ✓ ...` aur `FAILOVER: ✓ ...` lines dikhni chahiye — iska matlab Sonnet `claude-sonnet-4-6` aur MiniMax `MiniMax-M3` **live** respond kar rahe hain gateway ke through. Ye fake test nahi hai — ye actual chat completion hai.

Services (sab 127.0.0.1 pe bound, LAN pe open nahi):

| Service | Port | Kya |
|---|---|---|
| Temporal | 7233 | Durable execution — task state, retries, resume |
| Temporal UI | 8080 | workflows ka live view |
| PostgreSQL | 5432 | pgvector + task/memory DB |
| Redis | 6379 | working memory, locks, live events |
| LiteLLM | 4000 | model router: Sonnet → MiniMax → Ollama fallback chain |
| Ollama (profile `local`) | 11434 | free local fallback models |
| n8n (profile `integrations`) | 5678 | external webhooks/social — optional, baad me |

## 4. Coding agent ko launch karo

Repo root me terminal kholo (`D:\AI_SYSTEM\AgenticOS`):

```bash
claude      # ya: codex
```

Aur ye **paste karo** (bas 2 line — sab rules AGENTS.md me already hain jo agents auto-read karte hain):

```text
Read AGENTS.md and docs/MASTER_BLUEPRINT.md first.
Now execute docs/BRIEF_PHASE_0.md completely, in order: Phase -1 audit, wait for my confirmation, then Phase 0 skeleton until its acceptance test passes. Do not start any other phase.
```

- Phase -1 ke baad agent tumhe `docs/AUDIT_REPORT.md` dega → **tum confirm karo**, tabhi aage badhega (Law 9).
- Phase 0 ka acceptance test (`kill app mid-task → reopen → resume from same step`) agent ko **apne haath se chalakar output paste karna hoga** PROGRESS.md me. Test output ke bina "done" = not done (Law 11).
- Uske baad har phase: `docs/PHASE_BRIEFS.md` me us phase ka exact block paste karo (Phase 1 se Phase 11 tak sab ready hain). **Ek phase baar me.** Beech me kabhi "baaki sab bana do" mat bolo.

## 5. Kya kabhi nahi karna (common disasters)

- ❌ Dashboard/UI pehle maangna → engine-less spaceship.
- ❌ Ek message me saare 12 phases dena.
- ❌ Agent ko `D:\AI_SYSTEM` me delete/rename permission dena before audit.
- ❌ `.env` ko chat me paste karna (agent ko bhi nahi).
- ❌ Bina `verify.ps1` pass kiye agent ko build shuru karwana (gateway down hoga to sab mock ban jayega).
- ❌ Julian Goldie research ka output seedha production code me dalwana — wo `docs/RESEARCH_TRACK_JULIAN_GOLDIE.md` ke rule se sirf Evolution Engine (Phase 9) ke sandbox me jayega.

## 6. Status check (hamesha)

`docs/PROGRESS.md` hi asli status hai. Repo me har phase ke baad: kya bana (FACT), kya chalta hai (command output ke saath), kya nahi bana (UNKNOWN/next). Jo cheez PROGRESS.md me tagged output ke saath nahi hai — wo exists nahi karti.
