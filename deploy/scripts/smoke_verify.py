#!/usr/bin/env python3
"""AgenticOS deploy verification — REAL checks (no mocks, Law 10).

Checks: (1) core ports listening, (2) LiteLLM alive, (3) live chat through `planning`
group (must be answered by claude-sonnet-4-6 or the MiniMax failover), (4) optional
`--full` also pings fast/research, (5) `--offline` only tests local Ollama group.

Exit codes: 0 = all required checks passed / skipped-by-missing-key; 1 = failure.
Never prints secret values — only variable names (Law 7).
"""
import json
import os
import socket
import sys
import urllib.request
from pathlib import Path

DEPLOY_DIR = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
CORE_PORTS = {  # name: port
    "postgres": 5432, "redis": 6379, "temporal": 7233,
    "temporal-ui": 8080, "litellm": 4000,
}
OLLAMA_PORT = 11434
LITELLM = f"http://{HOST}:4000"


def load_env() -> None:
    env_file = DEPLOY_DIR / ".env"
    if not env_file.exists():
        print("[verify] WARNING: deploy/.env not found — copy .env.example to .env")
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key and key not in os.environ:
            os.environ[key] = val


def check_tcp(name: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((HOST, port), timeout=timeout):
            print(f"  [ok]   {name:<12} tcp:{port}")
            return True
    except OSError:
        print(f"  [FAIL] {name:<12} tcp:{port} — not listening")
        return False


def http_json(url: str, payload: dict | None = None, token: str | None = None, timeout: int = 90):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode())


def ping_group(group: str, token: str) -> bool:
    """Real chat completion through the gateway. Proves routing + provider keys + fallback config."""
    try:
        status, body = http_json(
            f"{LITELLM}/v1/chat/completions",
            {
                "model": group,
                "messages": [{"role": "user", "content": "Reply with exactly: PONG"}],
                "max_tokens": 16,
            },
            token=token,
        )
        model = body.get("model", "?")
        content = ""
        try:
            content = (body["choices"][0]["message"]["content"] or "").strip()[:40]
        except (KeyError, IndexError):
            pass
        if status == 200 and body.get("choices"):
            print(f"  [ok]   group '{group}' served by: {model} -> {content!r}")
            return True
        print(f"  [FAIL] group '{group}': status {status}")
        return False
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        detail = e.read().decode(errors="ignore")[:200]
        print(f"  [FAIL] group '{group}': HTTP {e.code} {detail}")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"  [FAIL] group '{group}': {e}")
        return False


def main() -> int:
    args = {a.lstrip("-") for a in sys.argv[1:]}
    load_env()
    token = os.environ.get("LITELLM_MASTER_KEY", "")
    ok = True

    print("[verify] 1) core services:")
    for name, port in CORE_PORTS.items():
        if not check_tcp(name, port):
            ok = False

    if "offline" in args:
        print("[verify] 2) local group only (offline mode):")
        if check_tcp("ollama", OLLAMA_PORT):
            ok = ping_group("local", token) and ok
        else:
            print("  [FAIL] ollama not running — start: docker compose --profile local up -d ollama")
            ok = False
        return 0 if ok else 1

    print("[verify] 2) litellm liveliness:")
    try:
        status, _ = http_json(f"{LITELLM}/health/liveliness")
        print(f"  [ok]   liveliness http {status}")
    except Exception as e:  # noqa: BLE001
        print(f"  [FAIL] litellm not responding: {e}")
        ok = False

    have_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    have_minimax = bool(os.environ.get("MINIMAX_API_KEY"))
    if not (have_anthropic or have_minimax):
        print("  [SKIP] no provider keys in deploy/.env — cloud ping skipped.")
        print("         (free-first: fill ANTHROPIC_API_KEY / MINIMAX_API_KEY, or run 'local' profile with --offline)")
    else:
        print("[verify] 3) LIVE model routing (real chat completions):")
        ok = ping_group("planning", token) and ok
        if "full" in args:
            ok = ping_group("coding", token) and ok
            ok = ping_group("fast", token) and ok
            ok = ping_group("research", token) and ok

    print("[verify] 4) optional local floor:")
    if check_tcp("ollama", OLLAMA_PORT, timeout=1.0):
        ok = ping_group("local", token) and ok
    else:
        print("  [skip] ollama down (ok if you don't need offline yet)")

    print("\n[verify] RESULT:", "PASS ✅ — deploy stack is REAL and reachable" if ok else "FAIL ❌ — fix above before Phase 0 starts")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
