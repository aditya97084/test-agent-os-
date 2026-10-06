---
description: Step 3 - derive the operating rules (how he works) from the wiki, each backed by exact quotes.
---

# /extract-rules

Turn the wiki into a small set of **operating rules** — not topics he knows, but the way he works.

## Steps

1. Read `wiki/index.md`, all of `wiki/methods/`, `wiki/principles/`, and every `wiki/sources/`
   page tagged with teaching, debugging, workflow, or llm-usage.
2. Candidate rules = behaviours that repeat across **3+ independent sources**. Write them as
   imperatives a model can follow ("predict the output before running"), never as vibes
   ("he is rigorous"). Aim for 7 (±2). More than 10 means you are splitting hairs; merge.
3. For each rule create `wiki/rules/<slug>.md` containing:
   - `confidence:` high (2+ independent sources) / medium (1) / inferred (0)
   - 1–3 **verbatim** quotes, each with `[[sources/...]]` + timestamp or anchor
   - "What this looks like in practice" — 3 concrete agent behaviours
   - "Failure mode it prevents" — one line
   - `## Related` backlinks
4. Any rule you believe but cannot quote goes under `## Inferred` on the page, clearly marked.
   **Never fabricate a quote.** A missing quote is a finding, not a problem to paper over.
5. Rewrite `.agents/rules/01-karpathy-operating-rules.md` from these pages: same numbering,
   each rule one line of behaviour + one short quote + source link. Keep it under 12,000 chars.
6. Update `index.md`, append `## [YYYY-MM-DD] extract-rules | <n> rules` to `log.md`.
7. Show the human a table: rule | confidence | #sources | strongest quote. Ask for sign-off.

## Guardrails

- Rules with confidence `medium` are "on the bench": usable but flagged. When a later ingest adds
  a second independent source, promote to high and log the promotion.
- Rule text is about *behaviour under uncertainty*. If a rule can't change what you'd do on the
  next task, delete it.
