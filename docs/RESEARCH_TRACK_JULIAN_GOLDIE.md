# Track 2 — Julian Goldie forensic research (PARALLEL, non-blocking)

**Rules for this track (from blueprint §3/§10 R7):**
- Never blocks Phase -1→11 core build.
- Output is *intelligence*, not code: capabilities/mechanisms only — never blind copying.
- Everything enters production only as `JAG-xxx` backlog items through the Phase 9 Evolution pipeline (sandbox → test → human approval).
- Every claim tagged FACT / INFERENCE / UNKNOWN / HYPOTHESIS. "Julian's Agent OS uses X" is illegal without first-party evidence.
- Transcript analysis ≠ watching the screen. If frames weren't inspected, write `VISUAL INSPECTION: Unavailable`.

## Pass 1 (do this first, one turn) — discovery only
Paste to your deep-research model (e.g. GPT-5.6 Sol):

```text
Pass 1 — DISCOVERY ONLY. Do not design or conclude anything.
From https://www.youtube.com/@JulianGoldieSEO/videos (and site search), list candidate videos
about: Agent OS / AI agents / Claude Code / Codex / Hermes / MCP / n8n / Obsidian memory /
voice / browser automation / content-SEO-video-leadgen automation / dashboard / 24-7 agents.
For each: title · URL · date · one-line why-relevant.
Tier 1 = directly about Agent OS; Tier 2 = components later used in it; Tier 3 = key dependency
tutorials; Tier 4 = skip. Output the tiered list ONLY. Do not analyze further yet.
```

## Pass 2+ (next turns, per Tier-1 video, one batch at a time)

```text
Deep-analyze these Tier-1 videos individually: <paste 3–5 URLs from Pass 1>.
Per video: transcript + description + links + chapters + resources; AND actual visual frames
at key timestamps (never fabricate frames; state availability honestly).
Record an evidence table: video · timestamp · what is visible · apparent function · confidence.
Classify each capability: VERIFIED WORKING / VERIFIED IMPLEMENTED / DEMONSTRATED / CLAIMED /
CONCEPTUAL / INFERRED / UNKNOWN — never silently promote a class.
Also build: feature inventory (core/agents/memory/automation/content/SEO/leadgen/video/voice/UI/
dev/local/tools), repo+resource hunt, third-party trace (for each named tool: which capability
does Julian get from it), UI wireframe reconstruction (ASCII), data-flow + agent-communication
reconstruction (evidence-backed, mark inferred steps), evolution timeline across videos,
reproducibility class per feature, gap analysis vs MY AgenticOS (Hermes Layer-2 + Temporal Layer-1,
LiteLLM Sonnet→MiniMax→local, task-state/checkpoint/failover, 4-layer memory, Playwright+UIA,
video autopilot, SEO/social approval-gated, Evolution engine, Kanban/pipeline/gallery).
Finish with engineering backlog JAG-001… : description · reason · dependency · approach ·
acceptance test. Do NOT propose redesigning my architecture; only mechanisms worth adapting.
```

Anti-disease rule: no "universal truth in 14 seconds." 200 videos ≠ done; discovery → evidence → visual inspection → then reconstruction, batch by batch. Deliverables land in `docs/research/JG/` (01 exec reconstruction … 27 source index), and `workflows/backlog/jag-backlog.yaml` for the pipeline-ready subset.
