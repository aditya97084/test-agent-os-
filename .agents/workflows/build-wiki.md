---
description: Step 2 - compile raw/ into the interlinked wiki (Karpathy's LLM Wiki pattern).
---

# /build-wiki

Compile everything in `raw/` into `wiki/` following `AGENTS.md` (§3 page format, §4 ingest).
Reference idea file: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## Steps

1. Inventory `raw/` (`python scripts/crawl_report.py`). Report counts before writing anything.
2. **Pass 1 — source pages.** One `wiki/sources/<date>-<slug>.md` per raw artifact: 150-word
   summary, 3–8 verbatim pull-quotes with timestamps/anchors, topics touched, link back to the
   raw path and original URL. Batch 10 sources at a time; after each batch update `index.md`
   and append to `log.md` so progress survives a crash.
3. **Pass 2 — entity & topic pages.** `wiki/topics/`, `wiki/people/` for everything that appears
   in 2+ sources. Each page cites the sources it came from.
4. **Pass 3 — behavioural pages.** `wiki/principles/` (durable beliefs), `wiki/methods/`
   (how-he-explains, how-he-debugs, how-he-builds, how-he-teaches, how-he-uses-llms).
   This is the layer that makes the agent *think* like him rather than quote him.
5. **Pass 4 — synthesis.** `wiki/overview.md`: the 10 things that matter most, with links.
   Note every contradiction you found instead of smoothing it over.
6. **Pass 5 — wiring.** Backlinks both ways, full `index.md` grouped by folder with one-line
   summaries, then `python scripts/wiki_lint.py` until orphans and broken links are zero.
7. Run `/wiki-graph` and show the human the graph.
8. Append to `log.md`: `## [YYYY-MM-DD] build-wiki | <n> sources -> <m> pages`.

## Guardrails

- Never delete a `raw/` file, never "fix" a transcript typo inside a quote (use `[sic]`).
- Confidence field is honest: 2+ independent sources = high, 1 = medium, no quote = inferred.
- If a pass would exceed your context, checkpoint to `log.md` and continue in the next turn.
