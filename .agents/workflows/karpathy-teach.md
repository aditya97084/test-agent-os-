---
description: Ask the Karpathy Teacher agent to explain or build something, then self-grade against the 7 rules.
---

# /karpathy-teach <what you're stuck on>

## Steps

1. Read `.agents/rules/01-karpathy-operating-rules.md` and `wiki/index.md`.
2. Pull only the wiki pages relevant to the question (topics + methods + rules). Cite them.
3. Hand the task to the **karpathy-teacher** subagent (`.agents/agents/karpathy-teacher.md`)
   so this conversation's context doesn't leak in.
4. The answer must follow the shape in rule file §"Answer shape":
   assumptions → done means → smallest version → prediction → real output → comparison →
   broken version if instructive → recap table.
5. Any code goes in `sandbox/` and is executed with
   `python scripts/run_and_log.py -- python sandbox/<file>.py`. Paste real output.
6. Run `python scripts/verify_gate.py`. Must exit 0 before you present the answer.
7. **Self-grade.** Print a checklist, one line per rule:

   ```
   1 build-it            PASS  built sandbox/bpe.py, ran it
   2 first-order-first   PASS  one concept per step
   3 predict-run-compare PASS  predicted 27 merges, got 27
   4 show-wrong-version  N/A   no instructive bug here
   5 prove-dont-claim    PASS  output pasted below
   6 say-assumptions     PASS  3 assumptions listed up top
   7 simpler-wins        WEAK  dropped the class wrapper, still 40 lines
   ```

   Any FAIL → fix it and re-grade before answering. `N/A` needs a half-line reason.
8. If the explanation is reusable, offer to file it as `wiki/topics/<slug>.md`.

## Guardrails

- No walls of text. Smallest working thing first, one addition at a time.
- Don't flatter, don't hedge, don't pad. If the human's premise is wrong, say so in line one.
