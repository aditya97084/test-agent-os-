# AUDIT_PROMPT — standalone Phase -1 prompt (use if running the audit before the main brief)

Paste to Claude Code / Codex on the machine that has `D:\AI_SYSTEM`:

```text
Perform a READ-ONLY audit of D:\AI_SYSTEM.

Rules:
- Do not delete, rename, move, overwrite, or restructure ANY file. Read-only.
- Inventory every folder, project, script, config, database, service, node_modules/venv, scheduled task and running process related to this directory.
- Classify each component as exactly one of: WORKING / PARTIAL / MOCK / BROKEN / MISSING / DO_NOT_REUSE.
  - MOCK means it looks functional in the UI but has hardcoded responses, dead buttons, or fake integrations. Report these explicitly with file:line evidence — these are the most important findings.
  - DO_NOT_REUSE requires a one-line reason.
- For anything that looks like an agent/CLI tool (Claude Code, Codex, Hermes, OpenClaw, n8n, Ollama, Obsidian vaults, browsers automation…), record: version found, whether it has a real headless API/CLI, auth state (without printing any secret values), and last-known activity date.
- Note existing databases/schemas and any user data that must be preserved (vaults, artifacts, repos, downloads).
- Output: write docs/AUDIT_REPORT.md with (1) summary counts per class, (2) full table path|type|class|evidence|recommendation(preserve/migrate/isolate/ignore), (3) PRESERVE-LIST, (4) DO-NOT-TOUCH-LIST, (5) open questions.
- Tag every finding FACT (verified by reading), INFERENCE (guessed from names), or UNKNOWN. Do not present inference as fact.
Finish by asking me to confirm the report. Wait for confirmation before any integration work.
```

Human note: yeh report hi decide karegi ki kya preserve hai, kya naya banana hai, aur kya "pehle se bana hai" sirf dikhawe ka hai. Iske bina build shuru karna blueprint violation hai (Law 9).
