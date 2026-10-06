---
description: Ingest one new link/file into raw/, then ripple it through every wiki page it touches.
---

# /karpathy-ingest <url | path>

The compounding loop. One link in → the whole brain gets slightly better.

## Steps

1. Already in `raw/`? Reuse it. Otherwise fetch with the right crawler
   (`crawl_youtube.py` / `crawl_web.py` / `crawl_x.py`) into the right `raw/<type>/` folder.
   Verbatim + YAML frontmatter. Show the word count.
2. Read it end to end. Report 3–5 key takeaways to the human **before** writing any page.
3. Write `wiki/sources/<date>-<slug>.md` (summary, pull-quotes, topics touched).
4. Ripple. For every claim in the source, find the pages it affects and update them:
   - new behaviour → extend the matching `wiki/rules/` page's "in practice" section
   - a rule at `confidence: medium` that now has a 2nd independent source → promote to `high`
     and state the promotion in the log
   - new topic/person → new page + backlinks
   - conflicts with an existing page → `## Contradictions` on both pages, ask the human
   Typical ripple is 5–15 pages. One page means you under-read the source.
5. Update `wiki/index.md` and `wiki/overview.md` if the synthesis shifted.
6. `python scripts/wiki_lint.py` → fix what it finds. Then `/wiki-graph` to refresh the picture.
7. Append to `wiki/log.md`:
   `## [YYYY-MM-DD] ingest | <title>` + a bullet per page touched + "promoted:" / "conflicts:" lines.
8. Report a diff summary: pages created, pages updated, rules changed, confidence promotions.
