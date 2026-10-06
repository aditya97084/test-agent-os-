---
description: Ship review - would this survive a real user? What should be deleted?
---

# /karpathy-review <path | "the diff">

The "would it ship?" pass from the video: adversarial, run-first, delete-happy.

## Steps

1. Read the target code. State in one line what it claims to do and what "working" would mean.
2. **Predict the failure before running.** List 3–5 concrete break scenarios with the exact
   trigger, e.g.:
   - non-UTF8 / emoji output on a Windows `cp1252` terminal
   - empty input, 1 item, 10k items
   - network timeout / 429 / expired token
   - path with a space; file already exists
   - timezone or locale difference
3. **Actually reproduce them**, each through `python scripts/run_and_log.py -- ...`.
   Force the environment instead of theorising:
   `PYTHONIOENCODING=cp1252 python scripts/run_and_log.py -- python <file>`
   Paste the real tracebacks.
4. Check side effects: does it write files *before* it can crash? Partial writes are bugs.
5. **Delete pass.** List everything not earning its place — unused imports, defensive branches
   that never fire, config nobody sets, abstractions with one caller. Propose the trimmed version.
6. **Prove the trim is equivalent**: run the original and the trimmed version on the same input,
   diff the outputs, paste both. No "should be the same".
7. Verdict table:

   ```
   Ships?        no
   Blockers      1) crashes on emoji (real traceback above) 2) writes CSV before validating
   Would delete  retry_wrapper(), --verbose flag, 3 unused imports (-61 lines)
   Risk if shipped  silent partial CSV for any comment containing an emoji
   ```
8. `python scripts/verify_gate.py` before answering.

## Guardrails

- Never approve code you did not run. "Looks fine" is not a verdict.
- Prefer deleting over adding. If you add anything, justify it in one line.
