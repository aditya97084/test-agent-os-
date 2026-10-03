"""Config resolution: config/gateway.yaml, overridden by env vars. Secrets are never read
into objects that could be serialized to responses or logs (Law 7) — only env var NAMES
appear in docs; values are pulled at connect time."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def repo_root() -> Path:
    env = os.environ.get("AGENTOS_ROOT")
    if env:
        return Path(env).resolve()
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "AGENTS.md").exists() and (parent / "contracts").is_dir():
            return parent
    return Path.cwd()


def _load_yaml() -> dict[str, Any]:
    cfg = repo_root() / "config" / "gateway.yaml"
    if cfg.exists():
        return yaml.safe_load(cfg.read_text()) or {}
    return {}


class Settings:
    def __init__(self) -> None:
        y = _load_yaml()
        g = y.get("gateway", {}) or {}
        t = y.get("temporal", {}) or {}
        e = y.get("executor", {}) or {}
        d = y.get("database", {}) or {}
        self.gateway_host: str = os.environ.get("AGENTOS_GATEWAY_HOST", g.get("host", "127.0.0.1"))
        self.gateway_port: int = int(os.environ.get("GATEWAY_PORT", g.get("port", 8000)))
        self.temporal_host: str = os.environ.get("AGENTOS_TEMPORAL_HOST", t.get("host", "127.0.0.1:7233"))
        self.temporal_ns: str = os.environ.get("TEMPORAL_NAMESPACE", t.get("namespace", "default"))
        self.task_queue: str = os.environ.get("TEMPORAL_TASK_QUEUE", t.get("task_queue", "agentos-main"))
        # engine: "temporal" (production path, durable) or "local" (dev-only fallback:
        # same DB checkpoints + resume-on-restart, but no cross-process durability beyond DB).
        self.engine: str = os.environ.get("AGENTOS_ENGINE", e.get("mode", "temporal"))
        self.db_url: str = os.environ.get(
            "AGENTOS_DB_URL",
            d.get(
                "url",
                "postgresql+asyncpg://agentos:${POSTGRES_PASSWORD}@127.0.0.1:5432/agentos",
            ),
        )
        if "${POSTGRES_PASSWORD}" in self.db_url:
            pw = os.environ.get("POSTGRES_PASSWORD", "")
            self.db_url = self.db_url.replace("${POSTGRES_PASSWORD}", pw)
        self.redis_url: str | None = os.environ.get("AGENTOS_REDIS_URL")
        # Demo executor params (labeled demo: everywhere — not product logic).
        self.demo_steps: int = int(os.environ.get("DEMO_STEPS", e.get("demo_steps", 6)))
        self.demo_step_seconds: float = float(os.environ.get("DEMO_STEP_SECONDS", e.get("demo_step_seconds", 15)))
        self.run_migrations_on_start: bool = os.environ.get("AGENTOS_MIGRATE", "1") == "1"
        self.litellm_url: str = os.environ.get("LITELLM_URL", "http://127.0.0.1:4000")
        self.events_poll_seconds: float = float(os.environ.get("AGENTOS_EVENTS_POLL", "1.0"))

    @property
    def gateway_base(self) -> str:
        h = self.gateway_host if self.gateway_host != "0.0.0.0" else "127.0.0.1"
        return f"http://{h}:{self.gateway_port}"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
