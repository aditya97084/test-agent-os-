---
description: Step 1 - crawl every public Karpathy source into raw/, one subagent per source type.
---

# /crawl-sources

Goal: fill `raw/` with verbatim public material by Andrej Karpathy, one subfolder per source type,
plus a manifest the human can audit. Target: 500k+ words. Expect 30–60 minutes.

## Steps

1. Read `config/sources.json`. If the human passed extra URLs with the command, append them there first.
2. Set up once: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
   (Windows: `.venv\Scripts\activate`). Log the versions you installed.
3. Launch **one subagent per source type** so they run in parallel. Each subagent gets:
   - its own folder (`raw/youtube/`, `raw/blog/`, `raw/github/`, `raw/x/`, `raw/papers/`)
   - the matching script from `scripts/`
   - the instruction: verbatim text only, YAML frontmatter on every file, skip existing files,
     never write outside its own folder.
4. While they run, do nothing else that writes to `raw/`.
5. When all subagents report back, run:
   `python scripts/crawl_report.py` → writes `raw/MANIFEST.md`.
6. Show the human: total files, total words per source type, date range, and the failure list.
7. Ask: "anything missing before we compile the wiki?" Do **not** auto-continue to `/build-wiki`.

## Guardrails

- X/Twitter needs `TWITTERAPI_IO_KEY` in `.env`. Missing → skip, record the gap, continue.
- Anything behind a login/paywall: list it for manual clipping instead of fighting the site.
- Never summarise during the crawl. This stage is capture only; compression happens in `/build-wiki`.
