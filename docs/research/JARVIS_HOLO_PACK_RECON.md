# JARVIS + HOLO PACK — Forensic Recon & Integration Map

Source: "Build Your Own Jarvis with GPT-6 Astra" (16 prompts) + "The Bare-Hands Holo Pack" (Zubair Trabzada AI Workshop, 2026). User-provided text; no videos inspected.
Source credibility: Zubair Trabzada is a real public builder (n8n ambassador, @AI-GPTWorkshop) — FACT (search-verified). Model-specific performance/price claims inside the pack (`gpt-6-astra` latency/$10-M in) — **CLAIMED, unverified; not adopted anywhere**. All *mechanisms* below were extracted from the engineering rules embedded in the prompts, which is exactly what this OS is allowed to absorb (Rule: mechanism over code).

**Pipeline rule respected:** nothing here touches production directly. Each verdict below became a `JAR-xxx` item in `workflows/backlog/jar-backlog.yaml`; items marked FOLDED are already assigned into blueprint phases; SANDBOX items route through Phase 9 like everything else.

---

## A. Part One — verdicts

| # | Feature (their mechanism) | Verdict | Lands in our OS as |
|---|---|---|---|
| P01 | 3D galaxy indexer (build.py → graph-data.js, numeric node ids, wikilink/title edges) + keyword-overlap RAG-lite with title weighting | **ADAPT** | Phase 4: Tier-0 retrieval — cheap keyword+title scoring runs *before/without embeddings*; when local model down, search still works (free-first). Numeric node-id = provenance contract: every answer returns node ids. Wikilink/title edges = cheap auto-link layer beside semantic graph. Their no-persistence `server.py` NOT adopted (we have Temporal/Postgres). |
| P02 | Web Speech voice: `FINISH_MS=900` buffer (pause finalizes only the real end-of-thought; mid-sentence pauses accumulate), interrupt words ("stop","wait") bypass buffer, `?mute=1` per-tab silence checked in the ONE speak function, listening/thinking/speaking status line | **ADOPT** | Phase 4: "web-lite" voice channel (zero-setup fallback when Gemini Live unavailable) + interaction laws: one named constant for finish window; barge-in words bypass buffering; mute flag unroutable; state always visible. |
| P03 | Provenance dive: fly to source note; **≥4 sources → light the whole cluster, never fly to one (flying to one arbitrary source is a lie)**; never read on-screen text aloud; small talk must not move the camera | **ADOPT** | Phase 4+10: UI-honesty rules U1–U3 (see §C). Provenance visualization must match the actual evidence set. |
| P04 | Persona = ONE commented block at top of file; boot greeting reads **real indexed counts**, never hardcoded; "sir" occasionally not every sentence | **ADAPT** | Phase 4/10: `config/persona.md` — Hermes persona is a single file, swappable in 30s; dashboard greetings read live counters (Law 10's "no hardcoded" made concrete). |
| P05 | "remember that…" → `POST /remember` writes real .md into captures/, node appears in live graph at its most-related neighbour, immediately retrievable **without re-indexing**, failure spoken out loud | **ADOPT** | Phase 4: `POST /memory/capture` — write+index is ATOMIC (a file that isn't searchable is a failed capture); trigger phrases user-configurable; silent memory loss is a P0 bug class. |
| P06 | `/see`: getDisplayMedia held; frame grabbed **at question time, never cached from share start**; if share ended → say so, never answer from memory of an old frame; media type must match actual encoding | **ADAPT** | Phase 3: vision-capture contract for ALL screenshot/frame tools: timestamp+staleness check, "source is gone" honest error, MIME-match enforcement (a wrong content-type can look like a dead feature). |
| P07 | `preflight.py`: live end-to-end chain checks, no mocks/unit substitute; incl. "served files == disk files" (stale-serving is the #1 ghost bug), "config.json unreachable from browser" (must fail LOUD), "model in config reachable by this key" | **ADOPT (whole)** | AGENTS.md **E1** + Phase 0 deliverable + every phase gate. "Done = preflight passes; paste the summary line." |
| P08 | Voice brain-swap: spoken-name dict → exact id; **explicit known-real-ids set; near-miss → REFUSE loudly with what's available; NEVER nearest-match fallback** ("opus 5" silently becoming old Opus wastes an hour); swap runtime-only, restart returns to config | **ADOPT (whole)** | AGENTS.md **E3** + Phase 1: model/agent/path name resolution everywhere uses an explicit registry; near-miss = refusal. Runtime override via LiteLLM (block/override + cost-safe), swap logged in `agent_history` per Law 4. |

## B. Part Two — verdicts (the "organs")

| # | Feature | Verdict | Lands in our OS as |
|---|---|---|---|
| P09 | Focus sessions: server-side session w/ 1s tick (tab reload rejoins — countdown never dies); frontmost app read FRESH per tick from CLI (cached notification APIs freeze in long-lived servers — "reports the first app forever"); tab lock = **hash of HOST only** (SPA paths change per click; site-level is the honest granularity); PRIVACY BY STRUCTURE: identities compared+discarded inside the reader, client sees whitelist of booleans/counters, a test proves nothing else leaks; 800ms grace; 3-tier escalating callouts from pools; nag cadence settable by voice; snooze; **excuse = refund excursion + quiet until back**; home-base (the assistant tab) is never drift; report card + ≥85%-clean streak in an **aggregates-only ledger** | **ADAPT** | Phase 6: **FOCUS/ACCOUNTABILITY engine** as a Temporal-scheduled monitor (ours survives reboot — theirs didn't). Same engine is the template for every "is project ko 24×7 monitor karo" task. Fresh-query-per-tick and host-hash-granularity become general tool rules. |
| P10 | Deferred lock: never lock the tab you're guaranteed to leave; wait for **settle = 2 consecutive ticks on first non-Jarvis surface**; announce "Locked on" (a wrong lock must be AUDIBLE); never guess from background window/second monitor; if user never leaves Jarvis tab → app-only fallback ~45s; deferred state is a visible boolean | **ADAPT** | Phase 6 + E-rules: general "settle → announce → fallback" law for ANY target attach (watch, share, record, lock): **a wrong lock is worse than no lock.** |
| P11 | Re-target by voice+card button; **card trap**: clicking your own overlay makes YOUR process frontmost — read the browser's FRONT WINDOW via scripting instead; never trust "frontmost" from inside your own window; voice-route ordering: explicit "lock this tab" beats pixel-share interpretation; teach the chat brain the recovery in its system prompt so it never invents restart-the-session advice | **ADOPT** | AGENTS.md **E8a** (read the thing you actually care about; overlays never trust frontmost) + Phase 1 persona rule: system prompt must state the real recovery paths, so the LLM can't hallucinate workarounds for features that exist. |
| P12 | "Sir, Instagram can wait": host→label map + bare-domain fallback; ≥4 lines per tier so long drift doesn't loop 3 phrases; nameless fallback pool; **label rides ONE tick into the spoken line and is stored NOWHERE** (not state/ledger/log/notes); the privacy test uses a MADE-UP label that appears in no canned text (grepping for "Instagram" is fooled by your own examples); a flag turns naming off | **ADOPT** | AGENTS.md **E6**: "name out loud, store nothing" — the general pattern for every transient sensitive signal (callouts, analytics of personal behavior). Fake-unique-token test = the only valid absence-proof. |
| P13 | Eyes: MediaPipe face/pose **in-browser only — booleans published, frames never leave the machine**; 700ms sustained bad posture → one dry nudge + 30s cooldown; absence grace 12s (glancing ≠ leaving); "give me a minute" relief valve = 3-min silence; **EAR LAW: no organ may turn the mic on — an organ may open a conversation, never a capture device**; mis-route guard (screen question ≠ eyes question) | **ADAPT** | Phase 6: optional `sense.pose` organ — opt-in, approval-gated, local-only. **E7 (Ear Law)** applies to the whole voice system: auto-open mic is illegal everywhere in AgenticOS. |
| P14 | Screen watch: 5s thumbnail diff **locally** = zero cost while nothing changes; stillness clock; model call only on threshold breach, 3-min cooldown; while watching, screen questions reuse the SAME share (never 2 shares); **tab-share trap**: a captured tab can't police tabs (renders itself; scroll ≠ new content) → force entire-screen, say so honestly | **ADOPT** | AGENTS.md **E5 — Monitor Pattern**: *cheap-watch → expensive-think*. This is the cost-architecture for ALL our Phase 6 background monitors (file-watch, GitHub-watch, SEO-watch, posture-watch): poll cheap local signal, escalate to model only on change, cooldown after escalate. |
| P15 | Swap announcements from CURATED scripted pools per model-family that rotate (asking a reasoning model to "introduce yourself" returns nothing → worst fallback = funniest sentence); ONE function for all swap doors; pretty names never raw slugs; pinned spoken aliases so a catalogue change can't swap you to "-mini" mid-demo | **ADAPT** | Phase 1+4: user-perceivable state changes get scripted line-pools (deterministic, fast, on-brand), model only if persona asked; alias→id map pinned in config (`config/model_aliases.yaml`), all entry points share one setter (E8). |
| P16 | Field tooling: `GET /…/diag` booleans-only (no identities) read from the RUNNING server (a fresh process can pass while the long-lived one is frozen); `?focusdebug=1` overlay; probe page writing PASS/FAIL into document.title for scripted driving; **viewport asserted — hidden tabs throttle timers so time-based checks LIE**; ledger whitelist-keys test; **THE LAW: when it fails in the field, read the sensors before touching code** | **ADOPT** | AGENTS.md **E2** + acceptance suite: every organ ships /diag + probe from day one; debug reads target the live process; time-based probes assert viewport visibility. This is Law 11 made operational. |

## C. Holo pack — verdicts

| Item | Verdict | Notes |
|---|---|---|
| Bare-hand gesture deck (pinch/drag/fly with momentum, 3D props, Jarvis voice mode) | **DEFER → Phase 10 optional experiment, via Phase 9 gate** | Hand tracking was already in our blueprint's Phase 10 polish list ("hand/gesture control"); the *right* entry is: 3D workspace may accept pointer→gesture input later. Nothing core depends on it. |
| "Held pose not motion" law — every motion gesture in their build was replaced by a static pose because cameras read poses reliably, movements twitchily | **ADOPT as U5** | Applies to ANY future gesture/pose input. |
| `?sim=1` synthetic-hands demo mode + mouse fallback everywhere | **ADOPT as U4** | Every input device needs a scripted-synthetic mode for testing + a degraded human fallback. Maps to our acceptance-probe philosophy. |
| Vendored tracking libs (shipped in-folder, not CDN) — "offline and ad-blockers cannot break it" | **ADOPT as E9 (packaging)** | Runtime-critical assets vendored locally; no CDN dependency for core features (mirrors their 3d-force-graph-CDN weakness in Jarvis P01 — we vendor). |
| .glb props pipeline, Draco re-compress tip, license-check-before-selling note | **REJECT (core)** / note-only | Demo garnish; keep the license-check habit (already Phase 9 discovery rule). |
| Paid-community upsell, "GPT-6 Astra best brain" framing | **REJECT** | Marketing. Our stack §5 stays locked (Sonnet-4.6 → MiniMax-M3 → local); their latency/price table: CLAIMED, unverified, unused. |

## D. UI-honesty rules distilled (U1–U5) — bind at Phase 10, enforce from Phase 4

- **U1 Provenance must match evidence:** one source → point at it; multiple sources → show the whole set. Pointing at one of six is a lie.
- **U2 Never narrate what's on screen** (voice adds, doesn't repeat).
- **U3 Small talk has no side-effects on data views** — decide "is this about my data?" before animating anything.
- **U4 Every exotic input ships with a synthetic mode + mouse/keyboard fallback** (`?sim=1` pattern).
- **U5 Held poses over motions** for camera input.

## E. Conflicts with our locked blueprint — resolutions

| Their way | Our way | Resolution |
|---|---|---|
| State lives in a long-lived server.py loop (reloaded tab rejoins, but *machine* reboot loses it) | Temporal-durable + Postgres truth | All focus/session state → Temporal workflow state; reboot survives (better than source, FACT-by-design) |
| OpenRouter one-key brain swap | Self-hosted LiteLLM (already §5) | Keep LiteLLM; adopt only their **known-ids-refusal** guard + alias map |
| Browser Web Speech only | Gemini Live + whisper + Piper | Web-lite becomes the third, zero-setup channel — never the primary |
| "No npm, no framework, single HTML" viewer | Tauri + React (§5) | Adopt their DATA CONTRACT (numeric node ids / graph-data json), render it in our stack |
| `gpt-6-astra` as brain | `claude-sonnet-4-6` primary / `MiniMax-M3` failover (locked, §5) | No change. Their model choice = one config line in their packs; our model routing is a governance decision (already locked) |
| Voice commands run without approval (locks, posts, reads) | Law 5 approval gates | Focus/eyes/watch are read-mostly; the ONLY destructive surface they can touch = nudge/lock UX, which is reversible — still: enabling `sense.*` organs requires a recorded approval |

## F. What this pack proves about us (FACT-grade corroboration)

Their five closing lessons independently validate our locked decisions: *brain is the easy part / the organs are the system* = our **System over Model**; *"longer prompts beat more prompts"* = why our phase briefs are single complete briefs; *"wrong lock > no lock"* and *"truth endpoints first"* = Laws 4 + 10 + the new E-rules. The packs are a good third-party sign that the blueprint's priorities (backend + honesty + sensors first, UI last) are correct.

## G. Net effect on the build

Nothing new at Phase 0 except `preflight.py` (E1) — which makes every later phase cheaper. Real added surface: Phase 1 (+model-swap guard), Phase 3 (+vision freshness contract), Phase 4 (+web-lite voice, capture endpoint, tier-0 retrieval, U-rules data side), Phase 6 (+focus engine as first personal organ, E5 monitor pattern), Phase 10 (+persona/announce polish, optional gestures). Estimated: ~1.5 extra phase-weeks total, no architecture change, no new infra services. **Verdict: worth it — mostly because 8 of the rules (E1–E9) are anti-lie engineering, which is this OS's whole differentiator.**
