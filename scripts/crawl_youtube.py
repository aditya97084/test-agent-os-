#!/usr/bin/env python3
"""Pull YouTube captions into raw/youtube/ as verbatim markdown with timestamps.

Primary: youtube-transcript-api. Fallback: yt-dlp subtitle download.
Channel/playlist expansion uses yt-dlp --flat-playlist.

Usage:
  python scripts/crawl_youtube.py --from-config config/sources.json
  python scripts/crawl_youtube.py --url https://www.youtube.com/@AndrejKarpathy/videos
  python scripts/crawl_youtube.py --url https://youtu.be/zduSFxRajkE --no-timestamps
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "raw" / "youtube"


def slug(s: str, n: int = 70) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (s or "").lower()).strip("-")
    return (s[:n] or "untitled").strip("-")


def video_ids(url: str) -> list[dict]:
    """Expand a channel/playlist/video URL into [{id,title,date}] via yt-dlp."""
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url)
    if m:
        return [{"id": m.group(1), "title": "", "date": ""}]
    try:
        p = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J", url],
            capture_output=True, text=True, timeout=300, check=True,
        )
        data = json.loads(p.stdout)
    except Exception as e:  # noqa: BLE001
        print(f"  ! yt-dlp expansion failed for {url}: {e}")
        return []
    out = []
    for e in data.get("entries") or []:
        if e and e.get("id"):
            out.append({"id": e["id"], "title": e.get("title", ""), "date": e.get("upload_date", "")})
    return out


def transcript_api(vid: str, timestamps: bool) -> str | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(vid, languages=["en", "en-US", "en-GB"])
        rows = [{"text": s.text, "start": s.start} for s in fetched]
    except Exception as e:  # noqa: BLE001
        print(f"  ! transcript-api {vid}: {type(e).__name__}")
        return None
    if timestamps:
        lines = []
        for r in rows:
            mm, ss = divmod(int(r["start"]), 60)
            hh, mm = divmod(mm, 60)
            lines.append(f'[{hh:02d}:{mm:02d}:{ss:02d}] {r["text"]}')
        return "\n".join(lines)
    return " ".join(r["text"] for r in rows)


def ytdlp_subs(vid: str) -> str | None:
    tmp = OUT / ".tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["yt-dlp", "--skip-download", "--write-auto-subs", "--write-subs",
             "--sub-langs", "en.*", "--convert-subs", "srt",
             "-o", str(tmp / "%(id)s.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"],
            capture_output=True, text=True, timeout=300, check=False,
        )
    except Exception as e:  # noqa: BLE001
        print(f"  ! yt-dlp subs {vid}: {e}")
        return None
    srts = list(tmp.glob(f"{vid}*.srt"))
    if not srts:
        return None
    raw = srts[0].read_text(encoding="utf-8", errors="replace")
    lines, seen = [], set()
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or ln.isdigit() or "-->" in ln:
            continue
        ln = re.sub(r"<[^>]+>", "", ln)
        if ln and ln not in seen:
            seen.add(ln)
            lines.append(ln)
    for f in srts:
        f.unlink(missing_ok=True)
    return "\n".join(lines)


def meta(vid: str) -> dict:
    try:
        p = subprocess.run(
            ["yt-dlp", "-J", "--skip-download", f"https://www.youtube.com/watch?v={vid}"],
            capture_output=True, text=True, timeout=180, check=True,
        )
        d = json.loads(p.stdout)
        return {"title": d.get("title", ""), "date": d.get("upload_date", ""), "channel": d.get("uploader", "")}
    except Exception:  # noqa: BLE001
        return {"title": "", "date": "", "channel": ""}


def save(vid: str, info: dict, body: str) -> Path:
    title = info.get("title") or vid
    d = info.get("date") or ""
    iso = f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 else ""
    name = f'{iso + "-" if iso else ""}{slug(title)}-{vid}.md'
    path = OUT / name
    fm = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f"url: https://www.youtube.com/watch?v={vid}",
        f"date: {iso}",
        "source_type: youtube",
        f'channel: "{info.get("channel","")}"',
        f"word_count: {len(body.split())}",
        f"fetched_at: {datetime.now(timezone.utc).date().isoformat()}",
        "---",
        "",
    ]
    path.write_text("\n".join(fm) + body + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--from-config", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-timestamps", action="store_true")
    ap.add_argument("--sleep", type=float, default=1.0)
    a = ap.parse_args()

    urls = list(a.url)
    if a.from_config:
        cfg = json.loads(Path(a.from_config).read_text(encoding="utf-8"))
        urls += [s["url"] for s in cfg.get("sources", []) if s.get("type") == "youtube"]
    if not urls:
        print("nothing to do: pass --url or --from-config")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    targets: list[dict] = []
    for u in urls:
        found = video_ids(u)
        print(f"{u} -> {len(found)} video(s)")
        targets += found
    if a.limit:
        targets = targets[: a.limit]

    ok = skip = fail = 0
    for i, t in enumerate(targets, 1):
        vid = t["id"]
        if list(OUT.glob(f"*{vid}.md")):
            skip += 1
            print(f"[{i}/{len(targets)}] SKIP {vid} (exists)")
            continue
        body = transcript_api(vid, not a.no_timestamps) or ytdlp_subs(vid)
        if not body or len(body.split()) < 50:
            fail += 1
            print(f"[{i}/{len(targets)}] FAIL {vid} (no captions)")
            continue
        info = {"title": t.get("title", ""), "date": t.get("date", "")}
        if not info["title"] or not info["date"]:
            info = {**info, **{k: v for k, v in meta(vid).items() if v}}
        p = save(vid, info, body)
        ok += 1
        print(f'[{i}/{len(targets)}] OK   {p.name} ({len(body.split()):,} words)')
        time.sleep(a.sleep)

    print(f"\nyoutube: {ok} fetched · {skip} skipped · {fail} failed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
