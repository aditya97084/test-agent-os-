#!/usr/bin/env python3
"""Build a visual link-graph of the wiki.

Parses [[wiki-links]] out of every markdown page under --wiki and emits:
  graph.json  nodes + edges + metrics
  graph.html  interactive graph (vis-network via CDN, no build step)
  graph.md    Mermaid fallback that renders in GitHub / Obsidian / Antigravity preview

Usage:
  python scripts/build_graph.py --wiki wiki --out wiki/_graph
  python scripts/build_graph.py --min-degree 1 --type rules,sources --max-nodes 400
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)

TYPE_COLORS = {
    "source": "#9aa0a6",
    "topic": "#4285f4",
    "principle": "#a142f4",
    "rule": "#ea4335",
    "method": "#34a853",
    "person": "#fa7b17",
    "index": "#202124",
    "other": "#5f6368",
}
# folder name -> node type
FOLDER_TYPE = {
    "sources": "source",
    "topics": "topic",
    "principles": "principle",
    "rules": "rule",
    "methods": "method",
    "people": "person",
}


def parse_frontmatter(text: str) -> dict:
    """Minimal YAML-ish frontmatter reader (no pyyaml dependency)."""
    m = FM_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.strip().startswith("-"):
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def node_id(path: Path, root: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix()


def resolve(target: str, ids: set[str]) -> str | None:
    """Resolve a [[link]] against known page ids, tolerating partial paths."""
    t = target.strip().strip("/")
    if t in ids:
        return t
    t_noext = t[:-3] if t.endswith(".md") else t
    if t_noext in ids:
        return t_noext
    tail = t_noext.split("/")[-1]
    hits = [i for i in ids if i.split("/")[-1] == tail]
    return hits[0] if len(hits) == 1 else None


def build(wiki: Path, max_nodes: int, min_degree: int, types: list[str] | None):
    pages = sorted(p for p in wiki.rglob("*.md")
                   if "_graph" not in p.parts and p.name.lower() != "readme.md")
    ids = {node_id(p, wiki) for p in pages}

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    broken: list[tuple[str, str]] = []

    for p in pages:
        text = p.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        nid = node_id(p, wiki)
        folder = nid.split("/")[0] if "/" in nid else "index"
        ntype = fm.get("type") or FOLDER_TYPE.get(folder, "other" if folder != "index" else "index")
        nodes[nid] = {
            "id": nid,
            "label": fm.get("title") or nid.split("/")[-1].replace("-", " "),
            "type": ntype,
            "confidence": fm.get("confidence", ""),
            "last_updated": fm.get("last_updated", ""),
            "words": len(text.split()),
            "in": 0,
            "out": 0,
        }
        body = FM_RE.sub("", text)
        for raw_link in LINK_RE.findall(body):
            tgt = resolve(raw_link, ids)
            if tgt is None:
                broken.append((nid, raw_link.strip()))
            elif tgt != nid:
                edges.append({"from": nid, "to": tgt})

    seen = set()
    uniq = []
    for e in edges:
        key = (e["from"], e["to"])
        if key not in seen:
            seen.add(key)
            uniq.append(e)
    edges = uniq

    for e in edges:
        nodes[e["from"]]["out"] += 1
        nodes[e["to"]]["in"] += 1

    if types:
        keep = {n["id"] for n in nodes.values() if n["type"] in types}
        nodes = {k: v for k, v in nodes.items() if k in keep}
        edges = [e for e in edges if e["from"] in keep and e["to"] in keep]

    if min_degree > 0:
        keep = {n["id"] for n in nodes.values() if n["in"] + n["out"] >= min_degree}
        nodes = {k: v for k, v in nodes.items() if k in keep}
        edges = [e for e in edges if e["from"] in keep and e["to"] in keep]

    if len(nodes) > max_nodes:
        ranked = sorted(nodes.values(), key=lambda n: -(n["in"] * 2 + n["out"]))[:max_nodes]
        keep = {n["id"] for n in ranked}
        nodes = {k: v for k, v in nodes.items() if k in keep}
        edges = [e for e in edges if e["from"] in keep and e["to"] in keep]

    orphans = sorted(n["id"] for n in nodes.values() if n["in"] + n["out"] == 0)
    hubs = sorted(nodes.values(), key=lambda n: -n["in"])[:10]

    # rules that do not reach any source page (weak rules)
    out_adj = defaultdict(set)
    for e in edges:
        out_adj[e["from"]].add(e["to"])
    weak_rules = []
    for n in nodes.values():
        if n["type"] != "rule":
            continue
        srcs = {t for t in out_adj[n["id"]] if nodes.get(t, {}).get("type") == "source"}
        if len(srcs) < 2:
            weak_rules.append({"id": n["id"], "sources": len(srcs)})

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "metrics": {
            "page_count": len(nodes),
            "link_count": len(edges),
            "by_type": dict(Counter(n["type"] for n in nodes.values())),
            "orphans": orphans,
            "hubs": [{"id": h["id"], "in": h["in"]} for h in hubs],
            "weak_rules": weak_rules,
            "broken_links": [{"from": a, "target": b} for a, b in broken],
        },
    }


HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Karpathy Brain - wiki graph</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
 html,body{margin:0;height:100%%;background:#0f1115;color:#e8eaed;font:14px/1.5 ui-sans-serif,system-ui,sans-serif}
 #net{position:absolute;inset:0}
 #panel{position:absolute;top:12px;left:12px;z-index:9;background:#191c22e6;border:1px solid #2b2f36;
        border-radius:10px;padding:12px 14px;max-width:330px;backdrop-filter:blur(6px)}
 h1{font-size:14px;margin:0 0 8px} .m{color:#9aa0a6;font-size:12px}
 .k{display:inline-block;margin:2px 6px 2px 0;font-size:11px}
 .dot{display:inline-block;width:9px;height:9px;border-radius:50%%;margin-right:4px}
 input{width:100%%;margin-top:8px;padding:5px 7px;border-radius:6px;border:1px solid #2b2f36;
       background:#0f1115;color:#e8eaed}
</style></head><body>
<div id="panel">
  <h1>Karpathy Brain — wiki graph</h1>
  <div class="m" id="stats"></div>
  <div id="legend" style="margin-top:8px"></div>
  <input id="q" placeholder="search a page…">
  <div class="m" id="sel" style="margin-top:8px"></div>
</div>
<div id="net"></div>
<script>
const DATA = %%DATA%%;
const COLORS = %%COLORS%%;
const nodes = new vis.DataSet(DATA.nodes.map(n => ({
  id: n.id, label: n.label, title: `${n.id}\\nin:${n.in} out:${n.out} ${n.confidence||''}`,
  value: 1 + n.in * 2, group: n.type,
  color: {background: COLORS[n.type]||'#5f6368', border:'#11131a',
          highlight:{background:COLORS[n.type]||'#5f6368', border:'#fff'}},
  font: {color: '#e8eaed', size: 12}
})));
const edges = new vis.DataSet(DATA.edges.map((e,i) => ({
  id:i, from:e.from, to:e.to, arrows:{to:{enabled:true,scaleFactor:.4}},
  color:{color:'#3a3f49',highlight:'#8ab4f8',opacity:.8}, smooth:{type:'continuous'}
})));
const net = new vis.Network(document.getElementById('net'), {nodes, edges}, {
  nodes:{shape:'dot', scaling:{min:6,max:36}},
  physics:{barnesHut:{gravitationalConstant:-9000, springLength:130, avoidOverlap:.25},
           stabilization:{iterations:300}},
  interaction:{hover:true, tooltipDelay:120}
});
const m = DATA.metrics;
document.getElementById('stats').textContent =
  `${m.page_count} pages · ${m.link_count} links · ${m.orphans.length} orphans · ${m.broken_links.length} broken`;
document.getElementById('legend').innerHTML = Object.entries(COLORS)
  .map(([t,c]) => `<span class="k"><span class="dot" style="background:${c}"></span>${t}</span>`).join('');
document.getElementById('q').addEventListener('input', e => {
  const v = e.target.value.toLowerCase();
  if(!v) return;
  const hit = DATA.nodes.find(n => n.id.toLowerCase().includes(v));
  if(hit){ net.selectNodes([hit.id]); net.focus(hit.id, {scale:1.3, animation:true}); }
});
net.on('selectNode', p => {
  const id = p.nodes[0];
  const ins = DATA.edges.filter(e=>e.to===id).map(e=>e.from);
  const outs = DATA.edges.filter(e=>e.from===id).map(e=>e.to);
  document.getElementById('sel').innerHTML =
    `<b>${id}</b><br>cited by ${ins.length}: ${ins.slice(0,6).join(', ')||'—'}<br>cites ${outs.length}: ${outs.slice(0,6).join(', ')||'—'}`;
});
</script></body></html>
"""


def write_outputs(graph: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")
    html = (
        HTML.replace("%%DATA%%", json.dumps(graph))
        .replace("%%COLORS%%", json.dumps(TYPE_COLORS))
        .replace("%%", "%")
    )
    (out / "graph.html").write_text(html, encoding="utf-8")

    # Mermaid fallback: top 60 nodes by degree
    deg = {n["id"]: n["in"] * 2 + n["out"] for n in graph["nodes"]}
    keep = {k for k, _ in sorted(deg.items(), key=lambda kv: -kv[1])[:60]}
    safe = lambda s: re.sub(r"[^a-zA-Z0-9]", "_", s)  # noqa: E731
    lines = ["# Wiki graph (fallback view)", "", "```mermaid", "graph LR"]
    for n in graph["nodes"]:
        if n["id"] in keep:
            lines.append(f'  {safe(n["id"])}["{n["label"]}"]')
    for e in graph["edges"]:
        if e["from"] in keep and e["to"] in keep:
            lines.append(f'  {safe(e["from"])} --> {safe(e["to"])}')
    lines += ["```", ""]
    m = graph["metrics"]
    lines += [
        f'- pages: {m["page_count"]} · links: {m["link_count"]}',
        f'- hubs: {", ".join(h["id"] for h in m["hubs"][:5]) or "—"}',
        f'- orphans: {", ".join(m["orphans"][:10]) or "—"}',
        f'- weak rules (<2 source links): {", ".join(w["id"] for w in m["weak_rules"]) or "—"}',
    ]
    (out / "graph.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", default="wiki")
    ap.add_argument("--out", default="wiki/_graph")
    ap.add_argument("--min-degree", type=int, default=0)
    ap.add_argument("--max-nodes", type=int, default=800)
    ap.add_argument("--type", default="", help="comma separated: source,topic,rule,method,...")
    a = ap.parse_args()

    wiki = Path(a.wiki)
    if not wiki.is_dir():
        print(f"no wiki dir at {wiki}")
        return 1
    types = [t.strip().rstrip("s") for t in a.type.split(",") if t.strip()] or None
    if types:
        types = [FOLDER_TYPE.get(t + "s", t) for t in types]

    g = build(wiki, a.max_nodes, a.min_degree, types)
    write_outputs(g, Path(a.out))

    m = g["metrics"]
    print(f'pages={m["page_count"]} links={m["link_count"]} types={m["by_type"]}')
    print("hubs: " + (", ".join(f'{h["id"]}({h["in"]})' for h in m["hubs"][:5]) or "—"))
    print("orphans: " + (", ".join(m["orphans"][:10]) or "—"))
    print("weak rules: " + (", ".join(w["id"] for w in m["weak_rules"]) or "—"))
    print("broken links: " + (", ".join(f'{b["from"]}->{b["target"]}' for b in m["broken_links"][:10]) or "—"))
    print(f'wrote {a.out}/graph.html, graph.json, graph.md')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
