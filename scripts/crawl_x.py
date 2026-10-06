#!/usr/bin/env python3
"""Pull a user's X/Twitter posts into raw/x/ via twitterapi.io (paid, ~$1 for a full archive).

Key: put TWITTERAPI_IO_KEY=... in .env (gitignored). No key -> the script exits cleanly with a
gap note, it never scrapes X directly.

Usage:
  python scripts/crawl_x.py --user karpathy --since 2023-01-01
  python scripts/crawl_x.py --user karpathy --max-pages 200
Output: one markdown file per year, posts in chronological order with permalinks.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "raw" / "x"
API = "https://api.twitterapi.io/twitter/user/last_tweets"


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def fetch_page(user: str, cursor: str, key: str) -> dict:
    q = urllib.parse.urlencode({"userName": user, **({"cursor": cursor} if cursor else {})})
    req = urllib.request.Request(f"{API}?{q}", headers={"X-API-Key": key})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def norm(t: dict) -> dict | None:
    txt = t.get("text") or t.get("full_text") or ""
    if not txt:
        return None
    created = t.get("createdAt") or t.get("created_at") or ""
    dt = None
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(created, fmt)
            break
        except ValueError:
            continue
    return {
        "id": str(t.get("id") or t.get("id_str") or ""),
        "date": (dt or datetime.now(timezone.utc)).date().isoformat(),
        "text": txt,
        "likes": t.get("likeCount") or t.get("favorite_count") or 0,
        "replies": t.get("replyCount") or 0,
        "is_reply": bool(t.get("inReplyToId") or t.get("in_reply_to_status_id")),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="karpathy")
    ap.add_argument("--since", default="2023-01-01")
    ap.add_argument("--max-pages", type=int, default=120)
    ap.add_argument("--include-replies", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.6)
    a = ap.parse_args()

    load_env()
    key = os.environ.get("TWITTERAPI_IO_KEY", "").strip()
    if not key:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "_GAP.md").write_text(
            "# gap: X/Twitter not crawled\n\nNo TWITTERAPI_IO_KEY in .env, so posts were skipped.\n"
            "Add the key and re-run `python scripts/crawl_x.py --user karpathy`,\n"
            "or clip individual threads manually into raw/misc/.\n",
            encoding="utf-8",
        )
        print("no TWITTERAPI_IO_KEY -> wrote raw/x/_GAP.md and stopped (this is fine, continue the build)")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    posts: list[dict] = []
    cursor, pages = "", 0
    while pages < a.max_pages:
        pages += 1
        try:
            data = fetch_page(a.user, cursor, key)
        except Exception as e:  # noqa: BLE001
            print(f"  ! page {pages} failed: {e}")
            time.sleep(3)
            continue
        batch = (data.get("data") or {}).get("tweets") or data.get("tweets") or []
        rows = [p for p in (norm(t) for t in batch) if p]
        if not a.include_replies:
            rows = [p for p in rows if not p["is_reply"]]
        posts += rows
        print(f"page {pages}: +{len(rows)} (total {len(posts)})")
        cursor = data.get("next_cursor") or (data.get("data") or {}).get("next_cursor") or ""
        has_next = data.get("has_next_page", bool(cursor))
        if not cursor or not has_next or not batch:
            break
        if rows and min(p["date"] for p in rows) < a.since:
            break
        time.sleep(a.sleep)

    posts = [p for p in posts if p["date"] >= a.since]
    posts.sort(key=lambda p: p["date"])
    by_year: dict[str, list[dict]] = defaultdict(list)
    for p in posts:
        by_year[p["date"][:4]].append(p)

    total_words = 0
    for year, rows in sorted(by_year.items()):
        body = []
        for p in rows:
            body.append(f'## {p["date"]} · https://x.com/{a.user}/status/{p["id"]}\n')
            body.append(re.sub(r"\n{3,}", "\n\n", p["text"]).strip() + "\n")
        text = "\n".join(body)
        total_words += len(text.split())
        fm = [
            "---",
            f'title: "X posts by @{a.user} ({year})"',
            f"url: https://x.com/{a.user}",
            f"date: {year}-12-31",
            "source_type: x",
            f"post_count: {len(rows)}",
            f"word_count: {len(text.split())}",
            f"fetched_at: {datetime.now(timezone.utc).date().isoformat()}",
            "---",
            "",
        ]
        (OUT / f"{year}-posts-{a.user}.md").write_text("\n".join(fm) + text, encoding="utf-8")
        print(f"wrote raw/x/{year}-posts-{a.user}.md ({len(rows)} posts)")

    print(f"\nx: {len(posts)} posts · {total_words:,} words across {len(by_year)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
