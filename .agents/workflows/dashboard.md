---
description: Open the Karpathy Brain dashboard - health score, rule coverage, corpus stats, activity, run-gate log and the graph in one page.
---

# /dashboard

## Steps

1. Refresh the underlying data first: `python scripts/build_graph.py --wiki wiki --out wiki/_graph`
   and `python scripts/wiki_lint.py` (fix anything cheap it reports).
2. Start it (background, keep it running):
   `python scripts/dashboard.py --wiki wiki --raw raw --host 0.0.0.0 --port 8081`
3. Open `http://localhost:8081` in the browser tool, screenshot it, attach the screenshot.
4. **Read it back to the human** — never just give the URL:
   - health score + which checks fail
   - rule coverage: how many rules sit on 2+ independent sources (the rest are guesses)
   - raw corpus: words per source type, and which type is thin
   - orphans / broken links
   - run gate: total runs, failures, and whether any code was answered without a run
5. End with the 3 highest-leverage next actions, e.g. "ingest 2 more sources for rule X",
   "write methods/how-he-teaches", "fix 4 broken links".

## Notes

- Need just the numbers, no server? `python scripts/dashboard.py --once` prints the JSON.
- Demo data (28 pages, no real quotes): `--wiki docs/example-wiki`.
- The dashboard is read-only. It never writes to `wiki/` except regenerating `wiki/_graph/`.
