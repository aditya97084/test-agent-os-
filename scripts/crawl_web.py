#!/usr/bin/env python3
"""Fetch blog posts / docs / GitHub READMEs into raw/<folder>/ as markdown.

Extraction order: trafilatura -> markdownify -> crude tag strip. Always verbatim text.

Usage:
  python scripts/crawl_web.py --from-config config/sources.json --kind blog
  python scripts/crawl_web.py --url https://karpathy.bearblog.dev/ --folder blog --crawl-links
  python scripts/crawl_web.py --github karpathy/nanoGPT --folder github
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import urllib.request

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (compatible; karpathy-brain-crawler/1.0; personal research)"


def slug(s: str, n: int = 70) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (s or "").lower()).strip("-")
    return (s[:n] or "untitled").strip("-")


def get(url: str, timeout: int = 45) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return r.read().decode(r.headers.get_content_charset() or "utf-8", errors="replace")


def to_markdown(html: str, url: str) -> tuple[str, str]:
    """Return (title, markdown)."""
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if m:
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
    try:
        import trafilatura

        txt = trafilatura.extract(html, url=url, include_links=True, include_comments=False,
                                  output_format="markdown")
        if txt and len(txt.split()) > 40:
            return title, txt
    except ImportError:
        pass
    try:
        from markdownify import markdownify

        body = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
        txt = markdownify(body, heading_style="ATX")
        return title, re.sub(r"\n{3,}", "\n\n", txt).strip()
    except ImportError:
        pass
    body = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    return title, re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", body)).strip()


def save(folder: str, url: str, title: str, body: str, date: str = "") -> Path:
    out = ROOT / "raw" / folder
    out.mkdir(parents=True, exist_ok=True)
    name = f'{date + "-" if date else ""}{slug(title or urlparse(url).path)}.md'
    path = out / name
    fm = [
        "---",
        f'title: "{(title or url).replace(chr(34), chr(39))}"',
        f"url: {url}",
        f"date: {date}",
        f"source_type: {folder}",
        f"word_count: {len(body.split())}",
        f"fetched_at: {datetime.now(timezone.utc).date().isoformat()}",
        "---",
        "",
    ]
    path.write_text("\n".join(fm) + body + "\n", encoding="utf-8")
    return path


def same_site_links(html: str, base: str) -> list[str]:
    out, seen = [], set()
    host = urlparse(base).netloc
    for href in re.findall(r'href="([^"#?]+)"', html):
        u = urljoin(base, href)
        if urlparse(u).netloc == host and u not in seen and not u.endswith((".png", ".jpg", ".css", ".js", ".xml")):
            seen.add(u)
            out.append(u)
    return out


def github_readme(repo: str) -> tuple[str, str]:
    for branch in ("main", "master"):
        for name in ("README.md", "readme.md"):
            try:
                return repo, get(f"https://raw.githubusercontent.com/{repo}/{branch}/{name}")
            except Exception:  # noqa: BLE001
                continue
    raise RuntimeError(f"no README found for {repo}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--github", action="append", default=[], help="owner/repo")
    ap.add_argument("--from-config", default="")
    ap.add_argument("--kind", default="", help="only this type from the config (blog/github/papers/misc)")
    ap.add_argument("--folder", default="blog")
    ap.add_argument("--crawl-links", action="store_true", help="also fetch same-site links one level deep")
    ap.add_argument("--limit", type=int, default=120)
    ap.add_argument("--sleep", type=float, default=1.0)
    a = ap.parse_args()

    jobs: list[tuple[str, str]] = [(u, a.folder) for u in a.url]
    repos = list(a.github)
    if a.from_config:
        cfg = json.loads(Path(a.from_config).read_text(encoding="utf-8"))
        for s in cfg.get("sources", []):
            t = s.get("type")
            if t in ("youtube", "x"):
                continue
            if a.kind and t != a.kind:
                continue
            if t == "github" and s.get("repo"):
                repos.append(s["repo"])
            elif s.get("url"):
                jobs.append((s["url"], t or a.folder))
                if s.get("crawl_links"):
                    a.crawl_links = True

    ok = skip = fail = 0

    for repo in repos:
        name = slug(repo.replace("/", "-"))
        if (ROOT / "raw" / "github" / f"{name}.md").exists():
            skip += 1
            print(f"SKIP github {repo}")
            continue
        try:
            _, md = github_readme(repo)
            p = save("github", f"https://github.com/{repo}", repo, md)
            ok += 1
            print(f"OK   {p.relative_to(ROOT)} ({len(md.split()):,} words)")
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"FAIL github {repo}: {e}")
        time.sleep(a.sleep)

    queue = list(jobs)
    done: set[str] = set()
    expanded = False
    while queue and len(done) < a.limit:
        url, folder = queue.pop(0)
        if url in done:
            continue
        done.add(url)
        try:
            html = get(url)
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f"FAIL {url}: {e}")
            continue
        title, md = to_markdown(html, url)
        if len(md.split()) < 60:
            print(f"THIN {url} ({len(md.split())} words) - not saved")
        else:
            p = save(folder, url, title, md)
            ok += 1
            print(f"OK   {p.relative_to(ROOT)} ({len(md.split()):,} words)")
        if a.crawl_links and not expanded:
            expanded = True
            for u in same_site_links(html, url)[: a.limit]:
                queue.append((u, folder))
        time.sleep(a.sleep)

    print(f"\nweb: {ok} fetched · {skip} skipped · {fail} failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
