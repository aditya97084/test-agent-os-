---
name: karpathy-teach
description: Use when the user wants something explained, taught, or built so they actually understand it - teaches with the smallest runnable example, predicts output before running, shows the broken version, and self-grades against the 7 Karpathy rules.
---

# Karpathy Teach

## When to use

The user says "explain", "teach me", "I don't understand", "how does X work", "build me a tiny
version of X", or hands over code they can't reason about. Not for pure ops/refactor tasks.

## Procedure

1. **Ground.** Read `wiki/index.md` → pull the 2–5 relevant pages (`topics/`, `methods/`,
   `rules/`). Cite them inline as `[[topics/tokenization]]`.
2. **Assumptions + done.** List assumptions. Define "done" in one line. Ask 2–3 questions if the
   request is thin — do not guess for the user.
3. **Smallest version.** Write the least code that demonstrates the idea, into `sandbox/`.
   No classes, no CLI, no config unless they are the lesson.
4. **Predict.** Before running, state specifically what you expect (values, shapes, error type).
5. **Run.** `python scripts/run_and_log.py -- python sandbox/<file>.py`. Paste real output.
6. **Compare.** Did the prediction hold? If not, explain the gap — that's the most valuable part.
7. **One step at a time.** Add exactly one concept, repeat 4–6. Stop when the original question
   is answered, not when the code is "complete".
8. **Break it on purpose** if the bug is instructive: show the broken version, the real error,
   then the fix.
9. **Gate.** `python scripts/verify_gate.py` must exit 0.
10. **Self-grade** one line per rule (PASS / WEAK / FAIL / N/A + reason). Fix FAILs, then answer.
11. **File it back.** If the explanation is reusable, offer to write `wiki/topics/<slug>.md`.

## Output template

```
Assumptions: ...
Done means: ...

Step 1 - <one idea>
  code -> prediction -> actual -> held? y/n

Step 2 - <one more idea>
  ...

Broken version (why it matters): ...

Recap
  ran: ... | output: ... | changed: ... | rules: #1 #3 #5
Rule check
  1 PASS ... 7 WEAK ...
```

## Anti-patterns

- Dumping 200 lines then saying "this works".
- Explaining before running. Explaining *instead of* running.
- Two new concepts in one step. Jargon with no definition on first use.
- Praise, hedging, filler, emoji.
