#!/usr/bin/env bash
# AgenticOS — verify infra + LIVE model routing. Pass args: --full | --offline
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
"$PY" scripts/smoke_verify.py "$@"
