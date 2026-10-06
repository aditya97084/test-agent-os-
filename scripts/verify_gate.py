#!/usr/bin/env python3
"""The run gate: block an answer that claims unrun code works.

Claude Code does this with a Stop hook. Antigravity has no Stop hook, so the agent is
required (by .agents/rules/02-verification-gate.md) to call this as the last action of any
turn in which it wrote or changed code.

A code file is VERIFIED when .state/run_log.jsonl contains a run that
  (a) referenced that file, and
  (b) started at or after the file's last modification time.
Exit 0 = everything that changed was actually run. Exit 1 = you have work to do.

Usage:
  python scripts/verify_gate.py
  python scripts/verify_gate.py --paths sandbox scripts --window 240   # also police tooling edits
  python scripts/verify_gate.py --require-pass     # also fail if the last run exited non-zero
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / ".state" / "run_log.jsonl"
CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".rb", ".go", ".rs"}
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".state", "raw", "wiki"}


def load_runs() -> list[dict]:
    if not LOG.exists():
        return []
    runs = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            runs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return runs


def ts_epoch(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso).timestamp()
    except ValueError:
        return 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="*", default=["sandbox"],
                    help="dirs to police; add scripts when you edited the tooling itself")
    ap.add_argument("--window", type=int, default=180, help="only check files touched in the last N minutes")
    ap.add_argument("--require-pass", action="store_true", help="also fail when the latest run exited non-zero")
    a = ap.parse_args()

    cutoff = time.time() - a.window * 60
    candidates: list[Path] = []
    for base in a.paths:
        root = ROOT / base
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix in CODE_EXT and not SKIP_DIRS & set(p.parts):
                if p.stat().st_mtime >= cutoff:
                    candidates.append(p)

    if not candidates:
        print("[gate] PASS - no code changed in the window, nothing to verify.")
        return 0

    runs = load_runs()
    unverified, failing = [], []
    for p in candidates:
        rel = p.resolve().relative_to(ROOT).as_posix()
        mtime = p.stat().st_mtime
        matched = [r for r in runs if rel in r.get("files", []) and ts_epoch(r.get("ts", "")) >= mtime - 2]
        if not matched:
            unverified.append(rel)
        elif a.require_pass and matched[-1].get("exit_code") != 0:
            failing.append((rel, matched[-1].get("exit_code")))

    if unverified or failing:
        print("[gate] BLOCKED - do not claim this works yet.\n")
        for rel in unverified:
            print(f"  NEVER RUN SINCE LAST EDIT : {rel}")
            print(f"      python scripts/run_and_log.py -- python {rel}")
        for rel, code in failing:
            print(f"  LAST RUN FAILED (exit {code}): {rel}")
        print("\nRun them, fix what breaks, then call this gate again.")
        return 1

    print(f"[gate] PASS - {len(candidates)} changed file(s) all have a post-edit run logged.")
    for p in candidates:
        print(f"  verified: {p.resolve().relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
