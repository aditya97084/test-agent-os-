#!/usr/bin/env bash
# AgenticOS Phase-0 dev run WITHOUT docker: local engine + sqlite. For the durable path run
# deploy/scripts/setup.sh (compose) — then AGENTOS_ENGINE=temporal is what the gateway uses.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
[ -d .venv ] && PY=.venv/bin/python
$PY -m pip install -q -e . >/dev/null 2>&1 || $PY -m pip install -q -e .
mkdir -p data logs
export AGENTOS_ROOT="$PWD"
export AGENTOS_ENGINE=local
export GATEWAY_PORT="${GATEWAY_PORT:-8000}"
export AGENTOS_DB_URL="${AGENTOS_DB_URL:-sqlite+aiosqlite:///$PWD/data/dev.db}"
export DEMO_STEP_SECONDS="${DEMO_STEP_SECONDS:-5}"
echo "[dev] gateway (local engine — worker not needed; it exits cleanly if started) on :$GATEWAY_PORT — DB: $AGENTOS_DB_URL"
$PY -m agentos_gateway &
GW=$!
echo "[dev] open http://127.0.0.1:$GATEWAY_PORT/ — Ctrl+C to stop"
trap 'kill $GW 2>/dev/null || true' EXIT
wait $GW
