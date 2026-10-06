---
name: wiki-graph
description: Use when the user wants to see, visualise, audit or explain the shape of the wiki - builds an interactive link graph (hubs, orphans, bridges, clusters) and reads it back in plain language.
---

# Wiki Graph

## When to use

"show me the graph", "how is the wiki connected", "what's missing", "which rules are weak",
after a `/build-wiki`, or after every ~10 ingests as a health check.

## Procedure

1. `python scripts/build_graph.py --wiki wiki --out wiki/_graph`
   Outputs: `graph.json` (data), `graph.html` (interactive, vis-network), `graph.md` (Mermaid),
   and prints hubs / orphans / cluster counts to stdout.
2. Serve + screenshot:
   `python -m http.server 8080 --bind 0.0.0.0 --directory wiki/_graph`
   open `http://localhost:8080/graph.html`, screenshot with the browser tool, attach it.
3. Interpret — never just hand over a file path. Report:
   - top 5 **hubs** by in-degree → what the brain is actually about
   - **orphans** → unreachable knowledge; add backlinks or delete
   - **bridges** (nodes whose removal splits a cluster) → the highest-value pages
   - **rule coverage**: every `rules/` node should reach 2+ distinct `sources/` nodes.
     List the rules that don't — those are the weak ones.
   - **lopsided clusters**: a topic with 30 sources and no method page means capture without
     compression; propose the pages to write.
4. End with the 3 most useful next actions (ingest X, link Y to Z, delete orphan W).

## Node colours

`source` grey · `topic` blue · `principle` purple · `rule` red · `method` green · `person` orange.
Node size = in-degree. Edge = `[[wiki-link]]`, direction = citing → cited.

## Notes

- Obsidian's own graph view works on this folder too (`wiki/` is a valid vault) — this skill
  exists so the graph is reproducible from the terminal and screenshotable by the agent.
- Big wiki? `--max-nodes 400 --min-degree 1` keeps it readable.
