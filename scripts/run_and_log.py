#!/usr/bin/env python3
"""Run a command, stream its output, and record proof of the run.

The agent must execute code through this wrapper so that verify_gate.py can prove
nothing was claimed without being run.

Usage:
  python scripts/run_and_log.py -- python sandbox/bpe.py
  python scripts/run_and_log.py --tag "windows-encoding" -- python sandbox/scrape.py
Env passthrough works normally:
  PYTHONIOENCODING=cp1252 python scripts/run_and_log.py -- python sandbox/scrape.py
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / ".state" / "run_log.jsonl"
CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".rb", ".go", ".rs", ".java", ".c", ".cpp", ".ipynb"}


def referenced_files(cmd: list[str]) -> list[str]:
    hits = []
    for tok in cmd:
        tok = tok.strip("'\"")
        if Path(tok).suffix in CODE_EXT:
            p = (ROOT / tok) if not Path(tok).is_absolute() else Path(tok)
            if p.exists():
                try:
                    hits.append(p.resolve().relative_to(ROOT).as_posix())
                except ValueError:
                    hits.append(p.as_posix())
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="", help="why this run exists, e.g. 'emoji crash repro'")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()

    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd:
        print("usage: python scripts/run_and_log.py [--tag X] -- <command>")
        return 2

    LOG.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace")
    dur = round(time.time() - t0, 3)

    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)

    def clip(s: str, n: int = 4000) -> str:
        s = s or ""
        return s if len(s) <= n else s[: n // 2] + f"\n...[{len(s)-n} chars clipped]...\n" + s[-n // 2 :]

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cmd": cmd,
        "tag": a.tag,
        "exit_code": proc.returncode,
        "duration_s": dur,
        "files": referenced_files(cmd),
        "stdout": clip(proc.stdout),
        "stderr": clip(proc.stderr),
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    status = "OK" if proc.returncode == 0 else f"FAIL(exit={proc.returncode})"
    print(f"\n[run_and_log] {status} in {dur}s · logged to .state/run_log.jsonl", file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
