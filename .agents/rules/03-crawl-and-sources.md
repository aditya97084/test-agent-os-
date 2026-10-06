---
trigger: model_decision
description: Read this before crawling, downloading, or adding anything new to raw/ (YouTube, blogs, GitHub, X).
---

# Crawling rules

- The manifest is `config/sources.json`. Add a source there first, then crawl. One subfolder of
  `raw/` per source type: `youtube/ blog/ github/ x/ papers/ misc/`.
- Tools, in order of preference:
  - YouTube → `scripts/crawl_youtube.py` (youtube-transcript-api, falls back to yt-dlp subtitles).
  - Blog/web/GitHub READMEs → `scripts/crawl_web.py` (trafilatura → markdown).
  - X/Twitter → `scripts/crawl_x.py` (twitterapi.io, key in `.env` as `TWITTERAPI_IO_KEY`).
    No key? Skip it, record the gap in `raw/MANIFEST.md`, continue. Do not scrape X by hand.
  - Anything paywalled/logged-in → ask the human to clip it (Obsidian Web Clipper) into `raw/misc/`.
- **Parallelism**: run one subagent per source type, not one per URL. Each subagent owns exactly
  one `raw/<type>/` folder, so no two agents write the same file.
- Every crawled file gets YAML frontmatter: `title, url, date, source_type, word_count, fetched_at`.
- Idempotent: if the target file already exists with non-trivial content, skip it and log `SKIP`.
- Rate limit 1 req/sec, 3 retries with backoff. Respect robots.txt and ToS. Public content only.
- When a crawl pass ends, write/refresh `raw/MANIFEST.md`: a table of source type, item count,
  word count, date range, plus a list of everything that failed and why. The human must be able
  to check your work without reading 700k words.
