---
description: Health check the wiki - orphans, broken links, unquoted rules, stale pages, missing index entries.
---

# /wiki-lint

## Steps

1. `python scripts/wiki_lint.py --report wiki/_graph/lint-report.md`
2. Fix mechanically what the script found, in this order:
   broken links → missing index entries → orphan pages (add backlinks or delete) →
   frontmatter gaps → rules with zero quotes (downgrade to `inferred` or find the quote in `raw/`).
3. Then do the part a script can't: read `wiki/overview.md` and the `rules/` pages and look for
   - contradictions between pages
   - claims superseded by a newer source (check dates)
   - concepts mentioned in 3+ pages with no page of their own
   - thin pages that should be merged into a parent
4. Propose the next 3 sources to ingest and the 3 questions the wiki currently cannot answer.
5. Append `## [YYYY-MM-DD] lint | <n> issues found, <m> fixed` to `wiki/log.md`.

Run this every ~10 ingests, or whenever an answer feels thinner than the sources deserve.
