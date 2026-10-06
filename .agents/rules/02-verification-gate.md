---
trigger: always_on
description: Run-before-you-answer gate. Antigravity has no Stop hook, so the gate is a script you must call yourself.
---

# Run gate

Claude Code can enforce this with a Stop hook. Antigravity cannot, so **you** enforce it.

- Execute code only via the logger, so the run is provable:
  `python scripts/run_and_log.py -- <command>`
  (e.g. `python scripts/run_and_log.py -- python sandbox/bpe_tokenizer.py`)
- **Last action of any turn that created or edited code:** `python scripts/verify_gate.py`
  - exit 0 → you may answer.
  - exit 1 → it prints the unverified files. Run them, fix failures, re-run the gate.
- Paste the real stdout/stderr in your answer. Truncate long output in the middle, never the end.
- If execution is impossible (no network, missing secret, needs GPU), you must:
  1. say so in one sentence, 2. mark the code `**UNVERIFIED**` at the top,
  3. give the exact command the human should run.
- A failing test is a result, not a defeat. Report it; never quietly rewrite the test to pass.
