#!/usr/bin/env bash
# AgenticOS — boot the durable core stack (Windows: use setup.ps1)
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[setup] Created deploy/.env from template."
  echo "[setup] EDIT IT (ANTHROPIC_API_KEY, MINIMAX_API_KEY, LITELLM_MASTER_KEY, POSTGRES_PASSWORD) then re-run setup."
  exit 2
fi

command -v docker >/dev/null 2>&1 || { echo "[setup] Docker not installed. Install Docker Desktop first (see HANDOFF.md §1)."; exit 1; }
docker info >/dev/null 2>&1 || { echo "[setup] Docker daemon not running — start Docker Desktop, then re-run."; exit 1; }

echo "[setup] booting core stack (postgres, redis, temporal, temporal-ui, litellm)..."
docker compose up -d --wait postgres redis temporal temporal-ui litellm

echo "[setup] registering Temporal namespace 'agentos' (idempotent)..."
docker compose --profile setup run --rm temporal-ns || true

echo ""
echo "[setup] core stack UP. Now verify:"
echo "        bash scripts/verify.sh          # + '--full' for all model groups"
echo ""
echo "[setup] optional free-local fallback: docker compose --profile local up -d ollama"
echo "        then: docker compose exec ollama ollama pull qwen3:8b"
echo "[setup] optional n8n integrations:   docker compose --profile integrations up -d n8n"
