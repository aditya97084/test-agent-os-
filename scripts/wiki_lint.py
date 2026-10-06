#!/usr/bin/env python3
"""Health-check the wiki: broken links, orphans, missing index entries, unquoted rules, stale pages.

Usage:
  python scripts/wiki_lint.py
  python scripts/wiki_lint.py --report wiki/_graph/lint-report.md --stale-days 120
Exit code 1 when there are errors (broken links / unquoted rules), 0 otherwise.
"""
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
QUOTE_RE = re.compile(r"^>\s+\S", re.M)
REQUIRED_FM = ["title", "type", "last_updated"]


def fm_of(text: str) -> dict:
    m = FM_RE.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.strip().startswith("-"):
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", default="wiki")
    ap.add_argument("--report", default="")
    ap.add_argument("--stale-days", type=int, default=180)
    a = ap.parse_args()

    wiki = Path(a.wiki)
    pages = sorted(p for p in wiki.rglob("*.md")
                   if "_graph" not in p.parts and p.name.lower() != "readme.md")
    if not pages:
        print("wiki is empty - run /build-wiki first")
        return 0

    ids = {p.relative_to(wiki).with_suffix("").as_posix(): p for p in pages}
    inbound = defaultdict(set)
    errors, warnings = [], []

    index_path = wiki / "index.md"
    index_text = index_path.read_text(encoding="utf-8", errors="replace") if index_path.exists() else ""
    if not index_text:
        errors.append("wiki/index.md is missing or empty")

    for pid, p in ids.items():
        text = p.read_text(encoding="utf-8", errors="replace")
        fm = fm_of(text)
        body = FM_RE.sub("", text)

        for key in REQUIRED_FM:
            if key not in fm:
                warnings.append(f"{pid}: frontmatter missing `{key}`")

        for raw in LINK_RE.findall(body):
            t = raw.strip().strip("/")
            t = t[:-3] if t.endswith(".md") else t
            if t in ids:
                inbound[t].add(pid)
                continue
            tail = t.split("/")[-1]
            hits = [i for i in ids if i.split("/")[-1] == tail]
            if len(hits) == 1:
                inbound[hits[0]].add(pid)
            else:
                errors.append(f"{pid}: broken link [[{raw.strip()}]]")

        if pid.startswith("rules/"):
            quotes = len(QUOTE_RE.findall(body))
            conf = fm.get("confidence", "")
            if quotes == 0 and conf != "inferred":
                errors.append(f"{pid}: rule has 0 quotes but confidence={conf or 'unset'} (set `inferred` or find the quote)")
            srcs = [l for l in LINK_RE.findall(body) if l.strip().startswith("sources/")]
            if len(set(srcs)) < 2 and conf == "high":
                warnings.append(f"{pid}: confidence=high but only {len(set(srcs))} source link(s)")

        if pid not in ("index", "log", "overview") and pid not in index_text:
            warnings.append(f"{pid}: not listed in wiki/index.md")

        lu = fm.get("last_updated", "")
        if lu:
            try:
                age = (date.today() - datetime.fromisoformat(lu).date()).days
                if age > a.stale_days:
                    warnings.append(f"{pid}: last_updated {lu} ({age}d ago) - re-check against newer sources")
            except ValueError:
                warnings.append(f"{pid}: last_updated `{lu}` is not ISO YYYY-MM-DD")

    orphans = [pid for pid in ids if pid not in ("index", "log", "overview") and not inbound[pid]]
    for o in orphans:
        warnings.append(f"{o}: orphan - no page links to it")

    lines = [
        "# Wiki lint report",
        "",
        f"- generated: {date.today().isoformat()}",
        f"- pages: {len(ids)} · errors: {len(errors)} · warnings: {len(warnings)} · orphans: {len(orphans)}",
        "",
        "## Errors (fix these)",
        *(f"- {e}" for e in errors or ["none"]),
        "",
        "## Warnings",
        *(f"- {w}" for w in warnings or ["none"]),
        "",
        "## Next, do the part a script cannot",
        "- read overview.md + rules/ for contradictions and superseded claims",
        "- find concepts mentioned in 3+ pages with no page of their own",
        "- list the 3 questions this wiki still cannot answer, and the sources that would fix that",
    ]
    report = "\n".join(lines)
    print(report)
    if a.report:
        out = Path(a.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report + "\n", encoding="utf-8")
        print(f"\nwrote {out}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
