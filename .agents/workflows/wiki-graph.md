---
description: Build and serve the visual graph of the wiki (the Obsidian graph-view equivalent).
---

# /wiki-graph

## Steps

1. Build: `python scripts/build_graph.py --wiki wiki --out wiki/_graph`
   → writes `graph.json`, `graph.html` (interactive) and `graph.md` (Mermaid fallback).
2. Serve it so the human can actually click it:
   `python -m http.server 8080 --bind 0.0.0.0 --directory wiki/_graph`
   then open `http://localhost:8080/graph.html` in the Antigravity browser tool.
3. Take a screenshot of the graph with the browser tool and attach it to the walkthrough /
   artifact. The picture is the deliverable, not the file path.
4. Read the graph out loud for the human:
   - **hubs** (highest in-degree) — the real centre of gravity of the brain
   - **orphans** (0 links) — knowledge that will never be retrieved; fix or delete
   - **bridges** — pages connecting two otherwise separate clusters; these are the valuable ones
   - **clusters** — colour = page type (source / topic / principle / rule / method / person).
     A healthy brain has every `rules/` node connected to 2+ `sources/` nodes.
5. If `rules/` nodes hang off a single source, say so and recommend what to ingest next.

## Options

- `--min-degree 1` hide orphans · `--type rules,sources` filter · `--max-nodes 400` for big wikis
- Prefer Obsidian? Just open the `wiki/` folder as a vault — the `[[links]]` are compatible and
  its graph view works out of the box. The script exists so you don't *need* Obsidian.
