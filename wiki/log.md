# Log

Append-only. One entry per operation, newest at the bottom.
Format (keep it exact — `grep "^## \[" wiki/log.md | tail -5` must work):

```
## [YYYY-MM-DD] <ingest|build-wiki|extract-rules|query|lint|graph> | <title>
- pages created: ...
- pages updated: ...
- promoted: rules/<slug> medium -> high (2nd source)
- conflicts: ...
```

## [2026-10-06] init | workspace scaffolded
- created AGENTS.md, .agents/{rules,workflows,skills,agents}, scripts/, empty raw/ + wiki/
- nothing ingested yet
