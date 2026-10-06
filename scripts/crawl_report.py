#!/usr/bin/env python3
"""Inventory raw/ so a human can audit the crawl in 30 seconds. Writes raw/MANIFEST.md."""
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


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
    ap.add_argument("--raw", default="raw")
    a = ap.parse_args()
    raw = Path(a.raw)
    raw.mkdir(exist_ok=True)

    per = defaultdict(lambda: {"files": 0, "words": 0, "dates": [], "thin": []})
    for p in raw.rglob("*"):
        if not p.is_file() or p.name.startswith(".") or p.name == "MANIFEST.md":
            continue
        kind = p.relative_to(raw).parts[0] if len(p.relative_to(raw).parts) > 1 else "misc"
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        words = len(text.split())
        d = per[kind]
        d["files"] += 1
        d["words"] += words
        meta = fm_of(text)
        if meta.get("date"):
            d["dates"].append(meta["date"])
        if words < 150:
            d["thin"].append(p.relative_to(raw).as_posix())

    total_f = sum(v["files"] for v in per.values())
    total_w = sum(v["words"] for v in per.values())
    lines = [
        "# raw/ manifest",
        "",
        f"- generated: {date.today().isoformat()}",
        f"- **{total_f} files · {total_w:,} words**",
        "",
        "| source type | files | words | date range |",
        "|---|---:|---:|---|",
    ]
    for kind in sorted(per):
        v = per[kind]
        ds = sorted(d for d in v["dates"] if d)
        rng = f"{ds[0]} → {ds[-1]}" if ds else "—"
        lines.append(f'| {kind} | {v["files"]} | {v["words"]:,} | {rng} |')
    thin = [f for v in per.values() for f in v["thin"]]
    lines += [
        "",
        f"## Suspiciously thin files ({len(thin)}) — likely failed fetches",
        *(f"- {t}" for t in thin[:40] or ["- none"]),
        "",
        "## Known gaps",
        "- fill in anything that needed a login/paywall and must be clipped manually",
    ]
    report = "\n".join(lines)
    (raw / "MANIFEST.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    print("\nwrote raw/MANIFEST.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
