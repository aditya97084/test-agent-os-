#!/usr/bin/env python3
"""Karpathy Brain dashboard - one page that shows whether the brain is actually healthy.

Pure stdlib. Reads wiki/, raw/ and .state/run_log.jsonl live; rebuilds the graph on every
refresh and embeds it.

Usage:
  python scripts/dashboard.py                       # http://localhost:8081
  python scripts/dashboard.py --wiki docs/example-wiki --port 8081
  python scripts/dashboard.py --host 0.0.0.0 --port 8081 --no-open
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_graph as bg  # noqa: E402

LOG_ENTRY_RE = re.compile(r"^##\s*\[(\d{4}-\d{2}-\d{2})\]\s*([a-z\-]+)\s*\|\s*(.*)$", re.M)
QUOTE_RE = re.compile(r"^>\s+\S", re.M)
LINK_RE = bg.LINK_RE


def wiki_stats(wiki: Path, out_dir: Path) -> dict:
    graph = bg.build(wiki, max_nodes=5000, min_degree=0, types=None)
    bg.write_outputs(graph, out_dir)
    m = graph["metrics"]

    rules, words_total = [], 0
    for p in sorted(wiki.rglob("*.md")):
        if "_graph" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        words_total += len(text.split())
        pid = p.relative_to(wiki).with_suffix("").as_posix()
        if not pid.startswith("rules/"):
            continue
        fm = bg.parse_frontmatter(text)
        body = bg.FM_RE.sub("", text)
        srcs = {l.strip() for l in LINK_RE.findall(body) if l.strip().startswith("sources/")}
        rules.append({
            "id": pid,
            "title": fm.get("title", pid.split("/")[-1].replace("-", " ")),
            "confidence": fm.get("confidence", "unset"),
            "sources": len(srcs),
            "quotes": len(QUOTE_RE.findall(body)),
            "last_updated": fm.get("last_updated", ""),
        })
    rules.sort(key=lambda r: (-r["sources"], r["title"]))

    return {
        "pages": m["page_count"],
        "links": m["link_count"],
        "words": words_total,
        "by_type": m["by_type"],
        "orphans": m["orphans"],
        "hubs": m["hubs"],
        "broken_links": m["broken_links"],
        "rules": rules,
    }


def raw_stats(raw: Path) -> dict:
    per = defaultdict(lambda: {"files": 0, "words": 0})
    if raw.is_dir():
        for p in raw.rglob("*"):
            if not p.is_file() or p.name.startswith(".") or p.name in ("README.md", "MANIFEST.md"):
                continue
            parts = p.relative_to(raw).parts
            kind = parts[0] if len(parts) > 1 else "misc"
            try:
                per[kind]["words"] += len(p.read_text(encoding="utf-8", errors="replace").split())
            except OSError:
                continue
            per[kind]["files"] += 1
    return {
        "by_type": {k: v for k, v in sorted(per.items())},
        "files": sum(v["files"] for v in per.values()),
        "words": sum(v["words"] for v in per.values()),
    }


def log_stats(wiki: Path) -> dict:
    f = wiki / "log.md"
    if not f.exists():
        return {"entries": [], "by_op": {}, "by_day": {}, "total": 0}
    text = f.read_text(encoding="utf-8", errors="replace")
    entries = [{"date": d, "op": o, "title": t.strip()} for d, o, t in LOG_ENTRY_RE.findall(text)]
    return {
        "entries": entries[-12:][::-1],
        "by_op": dict(Counter(e["op"] for e in entries)),
        "by_day": dict(sorted(Counter(e["date"] for e in entries).items())[-21:]),
        "total": len(entries),
    }


def run_stats() -> dict:
    f = ROOT / ".state" / "run_log.jsonl"
    runs = []
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    runs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    recent = [{
        "ts": r.get("ts", "")[:19].replace("T", " "),
        "cmd": " ".join(r.get("cmd", []))[:90],
        "exit_code": r.get("exit_code"),
        "duration_s": r.get("duration_s"),
        "tag": r.get("tag", ""),
    } for r in runs[-10:][::-1]]
    return {
        "total": len(runs),
        "passed": sum(1 for r in runs if r.get("exit_code") == 0),
        "failed": sum(1 for r in runs if r.get("exit_code") not in (0, None)),
        "recent": recent,
    }


def health(w: dict, r: dict, runs: dict) -> dict:
    checks = []
    checks.append(("sources captured", r["words"] >= 50_000, f'{r["words"]:,} words in raw/'))
    checks.append(("wiki compiled", w["pages"] >= 20, f'{w["pages"]} pages'))
    checks.append(("no broken links", len(w["broken_links"]) == 0, f'{len(w["broken_links"])} broken'))
    checks.append(("no orphans", len(w["orphans"]) == 0, f'{len(w["orphans"])} orphans'))
    rules = w["rules"]
    strong = [x for x in rules if x["sources"] >= 2]
    checks.append(("rules quote-backed", bool(rules) and all(x["quotes"] > 0 or x["confidence"] == "inferred" for x in rules),
                   f'{sum(1 for x in rules if x["quotes"] > 0)}/{len(rules)} with quotes'))
    checks.append(("rules on 2+ sources", bool(rules) and len(strong) == len(rules),
                   f"{len(strong)}/{len(rules)} strong"))
    checks.append(("runs logged", runs["total"] > 0, f'{runs["total"]} runs, {runs["failed"]} failed'))
    score = round(100 * sum(1 for _, ok, _ in checks if ok) / len(checks))
    return {"score": score, "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in checks]}


def collect(wiki: Path, raw: Path, graph_out: Path) -> dict:
    w = wiki_stats(wiki, graph_out)
    r = raw_stats(raw)
    runs = run_stats()
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "wiki_path": str(wiki),
        "raw_path": str(raw),
        "wiki": w,
        "raw": r,
        "log": log_stats(wiki),
        "runs": runs,
        "health": health(w, r, runs),
    }


PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Karpathy Brain — dashboard</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0f1115;--card:#171a21;--line:#262b34;--txt:#e8eaed;--dim:#9aa0a6;--ok:#34a853;
      --warn:#fbbc04;--bad:#ea4335;--blue:#8ab4f8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font:14px/1.55 ui-sans-serif,system-ui,-apple-system,sans-serif}
header{padding:18px 22px;border-bottom:1px solid var(--line);display:flex;gap:16px;align-items:baseline;flex-wrap:wrap}
h1{font-size:17px;margin:0;letter-spacing:.2px}
.dim{color:var(--dim);font-size:12px}
main{padding:18px 22px;display:grid;gap:16px;max-width:1500px}
.row{display:grid;gap:16px}
.k4{grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.k2{grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card h2{font-size:12px;text-transform:uppercase;letter-spacing:.8px;color:var(--dim);margin:0 0 10px}
.big{font-size:30px;font-weight:600;line-height:1.1}
.sub{color:var(--dim);font-size:12px;margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--dim);font-weight:500;font-size:11px;text-transform:uppercase;
   letter-spacing:.6px;padding:5px 8px;border-bottom:1px solid var(--line)}
td{padding:6px 8px;border-bottom:1px solid #1e222a}
tr:last-child td{border-bottom:0}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;border:1px solid}
.p-ok{color:var(--ok);border-color:#1e4620;background:#13291a}
.p-warn{color:var(--warn);border-color:#4a3b06;background:#2a2309}
.p-bad{color:var(--bad);border-color:#5b1d18;background:#2d1311}
.p-dim{color:var(--dim);border-color:var(--line)}
.bar{height:7px;border-radius:4px;background:#232833;overflow:hidden}
.bar>i{display:block;height:100%}
.chips span{display:inline-block;margin:3px 6px 3px 0;padding:2px 9px;border-radius:999px;
            border:1px solid var(--line);font-size:12px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
iframe{width:100%;height:520px;border:1px solid var(--line);border-radius:10px;background:#0f1115}
code{background:#0f1115;border:1px solid var(--line);border-radius:5px;padding:1px 5px;font-size:12px}
.spark{display:flex;align-items:flex-end;gap:3px;height:46px}
.spark i{flex:1;background:var(--blue);border-radius:2px 2px 0 0;min-height:2px;opacity:.85}
a{color:var(--blue)}
</style></head><body>
<header>
  <h1>🧠 Karpathy Brain</h1>
  <span class="dim" id="paths"></span>
  <span class="dim" style="margin-left:auto" id="gen"></span>
</header>
<main>
  <div class="row k4" id="kpis"></div>
  <div class="row k2">
    <div class="card"><h2>Health checks</h2><div id="health"></div></div>
    <div class="card"><h2>Rule coverage — har rule ke peeche kitne sources</h2><div id="rules"></div></div>
  </div>
  <div class="row k2">
    <div class="card"><h2>raw/ — captured corpus</h2><div id="raw"></div></div>
    <div class="card"><h2>wiki/ — page types</h2><div id="types"></div>
      <h2 style="margin-top:14px">Top hubs</h2><div id="hubs"></div></div>
  </div>
  <div class="row k2">
    <div class="card"><h2>Activity (wiki/log.md)</h2><div class="spark" id="spark"></div><div id="log"></div></div>
    <div class="card"><h2>Run gate — execution proof (.state/run_log.jsonl)</h2><div id="runs"></div></div>
  </div>
  <div class="card"><h2>Graph — wiki ki shakal</h2>
    <iframe src="/graph/graph.html" title="wiki graph"></iframe>
    <div class="sub">Alag tab me: <a href="/graph/graph.html" target="_blank">/graph/graph.html</a> ·
      orphans aur weak rules upar table me hain</div>
  </div>
  <div class="dim" style="padding-bottom:24px">Auto-refresh har 20s ·
    <code>python scripts/dashboard.py --wiki wiki</code></div>
</main>
<script>
const COLORS={source:'#9aa0a6',topic:'#4285f4',principle:'#a142f4',rule:'#ea4335',
              method:'#34a853',person:'#fa7b17',index:'#5f6368',other:'#5f6368'};
const n=x=>(x||0).toLocaleString();
const pill=(cls,t)=>`<span class="pill ${cls}">${t}</span>`;

function kpi(label,value,sub,accent){return `<div class="card"><h2>${label}</h2>
  <div class="big" ${accent?`style="color:${accent}"`:''}>${value}</div><div class="sub">${sub}</div></div>`;}

async function load(){
  const d = await (await fetch('/api/stats')).json();
  document.getElementById('gen').textContent = 'updated ' + d.generated;
  document.getElementById('paths').textContent = `${d.wiki_path} · ${d.raw_path}`;

  const h = d.health, hc = h.score>=80?'var(--ok)':h.score>=50?'var(--warn)':'var(--bad)';
  const strong = d.wiki.rules.filter(r=>r.sources>=2).length;
  document.getElementById('kpis').innerHTML =
    kpi('Health','<span>'+h.score+'%</span>', h.checks.filter(c=>c.ok).length+'/'+h.checks.length+' checks pass', hc)
  + kpi('Raw corpus', n(d.raw.words), n(d.raw.files)+' files across '+Object.keys(d.raw.by_type).length+' source types')
  + kpi('Wiki', n(d.wiki.pages)+' pages', n(d.wiki.links)+' links · '+n(d.wiki.words)+' words')
  + kpi('Rules', strong+'/'+d.wiki.rules.length+' strong',
        d.wiki.orphans.length+' orphans · '+d.wiki.broken_links.length+' broken links',
        d.wiki.broken_links.length? 'var(--bad)': undefined);

  document.getElementById('health').innerHTML = `<div class="bar" style="margin-bottom:10px">
      <i style="width:${h.score}%;background:${hc}"></i></div><table>` +
    h.checks.map(c=>`<tr><td>${c.ok?pill('p-ok','pass'):pill('p-bad','todo')}</td>
      <td>${c.name}</td><td class="dim">${c.detail}</td></tr>`).join('') + '</table>';

  document.getElementById('rules').innerHTML = d.wiki.rules.length ? `<table>
    <tr><th>rule</th><th>sources</th><th>quotes</th><th>confidence</th></tr>` +
    d.wiki.rules.map(r=>{
      const cls = r.sources>=2?'p-ok':r.sources==1?'p-warn':'p-bad';
      return `<tr><td>${r.title}</td><td>${pill(cls,r.sources)}</td><td>${r.quotes}</td>
        <td>${pill(r.confidence=='high'?'p-ok':r.confidence=='medium'?'p-warn':'p-dim',r.confidence)}</td></tr>`;
    }).join('') + '</table><div class="sub">2+ independent sources = real rule. 1 = bench par. 0 = inferred.</div>'
    : '<div class="dim">abhi koi rule nahi — <code>/extract-rules</code> chalao</div>';

  const rt = Object.entries(d.raw.by_type);
  const maxw = Math.max(1,...rt.map(([,v])=>v.words));
  document.getElementById('raw').innerHTML = rt.length ? `<table>
    <tr><th>source type</th><th>files</th><th>words</th><th></th></tr>` +
    rt.map(([k,v])=>`<tr><td>${k}</td><td>${n(v.files)}</td><td>${n(v.words)}</td>
      <td style="width:45%"><div class="bar"><i style="width:${100*v.words/maxw}%;background:var(--blue)"></i></div></td></tr>`).join('')
    + '</table>' : '<div class="dim">raw/ khali hai — <code>/crawl-sources</code> chalao</div>';

  document.getElementById('types').innerHTML = '<div class="chips">' +
    Object.entries(d.wiki.by_type).map(([k,v])=>
      `<span><i class="dot" style="background:${COLORS[k]||'#5f6368'}"></i>${k} ${v}</span>`).join('') + '</div>';
  document.getElementById('hubs').innerHTML = d.wiki.hubs.length ? '<table>' +
    d.wiki.hubs.slice(0,6).map(x=>`<tr><td>${x.id}</td><td class="dim">${x.in} inbound</td></tr>`).join('')
    + '</table>' : '<div class="dim">—</div>';

  const days = Object.entries(d.log.by_day), mx = Math.max(1,...days.map(([,v])=>v));
  document.getElementById('spark').innerHTML = days.length
    ? days.map(([k,v])=>`<i title="${k}: ${v}" style="height:${100*v/mx}%"></i>`).join('')
    : '<span class="dim">no activity yet</span>';
  document.getElementById('log').innerHTML = d.log.entries.length ? '<table>' +
    d.log.entries.map(e=>`<tr><td class="dim">${e.date}</td><td>${pill('p-dim',e.op)}</td>
      <td>${e.title}</td></tr>`).join('') + '</table>' : '<div class="dim">log.md khali hai</div>';

  const r = d.runs;
  document.getElementById('runs').innerHTML =
    `<div style="margin-bottom:8px">${pill('p-ok',r.passed+' passed')} ${pill(r.failed?'p-bad':'p-dim',r.failed+' failed')}
     <span class="dim"> · total ${r.total}</span></div>` +
    (r.recent.length ? '<table><tr><th>when</th><th>command</th><th>exit</th></tr>' +
      r.recent.map(x=>`<tr><td class="dim">${x.ts}</td><td><code>${x.cmd}</code></td>
        <td>${x.exit_code===0?pill('p-ok','0'):pill('p-bad',x.exit_code)}</td></tr>`).join('') + '</table>'
      : '<div class="dim">abhi tak kuch run nahi hua — code hamesha <code>scripts/run_and_log.py</code> se chalao</div>');
}
load(); setInterval(load, 20000);
</script></body></html>
"""


def make_handler(wiki: Path, raw: Path, graph_out: Path):
    class H(BaseHTTPRequestHandler):
        def _send(self, body: bytes, ctype: str, code: int = 200) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?")[0]
            try:
                if path in ("/", "/index.html"):
                    self._send(PAGE.encode(), "text/html; charset=utf-8")
                elif path == "/api/stats":
                    self._send(json.dumps(collect(wiki, raw, graph_out)).encode(), "application/json")
                elif path.startswith("/graph/"):
                    f = graph_out / path[len("/graph/"):]
                    if f.is_file() and graph_out.resolve() in f.resolve().parents:
                        ctype = "text/html; charset=utf-8" if f.suffix == ".html" else "application/json"
                        self._send(f.read_bytes(), ctype)
                    else:
                        self._send(b"not found", "text/plain", 404)
                else:
                    self._send(b"not found", "text/plain", 404)
            except Exception as e:  # noqa: BLE001
                self._send(f"error: {e}".encode(), "text/plain", 500)

        def log_message(self, *a) -> None:  # silence per-request noise
            return

    return H


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", default="wiki")
    ap.add_argument("--raw", default="raw")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8081)
    ap.add_argument("--once", action="store_true", help="print the stats JSON and exit (no server)")
    a = ap.parse_args()

    wiki, raw = Path(a.wiki), Path(a.raw)
    graph_out = wiki / "_graph"
    if not wiki.is_dir():
        print(f"no wiki dir at {wiki}")
        return 1

    if a.once:
        print(json.dumps(collect(wiki, raw, graph_out), indent=2))
        return 0

    srv = ThreadingHTTPServer((a.host, a.port), make_handler(wiki, raw, graph_out))
    print(f"dashboard: http://localhost:{a.port}   (wiki={wiki} raw={raw})")
    print(f"today: {date.today().isoformat()} · Ctrl+C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
