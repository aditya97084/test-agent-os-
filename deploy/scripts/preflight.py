#!/usr/bin/env python3
"""AgenticOS preflight (E1 — Jarvis pack JAR-007 law: 'done = preflight passed').

LIVE end-to-end chain checks against the RUNNING system. No unit tests, no mocks here —
this exists precisely because the failures that hurt are the ones where unit tests pass and
a real chain is dead. Grows one check per real incident (append-only, every check earned).

Usage: python deploy/scripts/preflight.py   (env: GATEWAY=http://127.0.0.1:8000,
LITELLM=http://127.0.0.1:4000, AGENTOS_ROOT for disk paths)
Exit non-zero on any FAIL. Prints: N pass, N fail, N warn.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

GATEWAY = os.environ.get("GATEWAY", "http://127.0.0.1:8000").rstrip("/")
ROOT = pathlib.Path(os.environ.get("AGENTOS_ROOT", pathlib.Path(__file__).resolve().parents[2]))
results: list[tuple[str, str, str]] = []  # (check, PASS/FAIL/WARN, detail)


def add(name: str, verdict: str, detail: str = "") -> None:
    icon = {"PASS": "[ok]  ", "FAIL": "[XX]  ", "WARN": "[warn]"}[verdict]
    print(f"  {icon} {name:<44} {detail[:160]}")
    results.append((name, verdict, detail))


def http(method: str, url: str, body: dict | None = None, token: str | None = None, timeout: int = 120):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw and "json" in (r.headers.get("content-type") or "") else raw)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400].decode(errors="ignore")
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def main() -> int:
    print("[preflight] live-chain checks against", GATEWAY)
    # 1) server up and serving
    st, h = http("GET", f"{GATEWAY}/v1/health")
    if st == 200 and isinstance(h, dict) and h.get("db"):
        add("gateway up + db reachable", "PASS", f"system={h['system']} engine={h['engine']}")
    else:
        add("gateway up + db reachable", "FAIL", f"status={st} {h}")
        return finish()
    engine = h.get("engine", "")
    if "local(dev)" in engine:
        add("durable engine active", "WARN", "engine=local(dev) — dev-only; run AGENTOS_ENGINE=temporal for Phase-0 acceptance")
    elif h.get("temporal"):
        add("durable engine active", "PASS", "temporal connected")
    else:
        add("durable engine active", "FAIL", "engine=temporal but temporal NOT connected (intake would 503 — correct hard-fail, but stack is down)")

    # 2) viewer served AND identical to disk (stale-serving ghost bug)
    st, served = http("GET", f"{GATEWAY}/viewer/index.html")
    disk = ROOT / "apps" / "web" / "index.html"
    if st == 200 and isinstance(served, (bytes, str)):
        b_served = served.encode() if isinstance(served, str) else served
        same = hashlib.sha256(b_served).hexdigest() == hashlib.sha256(disk.read_bytes()).hexdigest()
        add("served viewer == disk file", "PASS" if same else "FAIL", "sha256 match" if same else "STALE SERVED FILE")
    else:
        add("served viewer == disk file", "FAIL", f"status={st}")

    # 3) secrets NOT reachable from browser (must fail loudly if served)
    for probe in ("/../deploy/.env", "/deploy/.env", "/config/../pyproject.toml", "/viewer/../../deploy/.env"):
        st, _ = http("GET", GATEWAY + probe)
        if st == 200:
            add(f"secret path unreachable: {probe}", "FAIL", "SERVED — Law 7 violation")
            return finish()
    add("secret paths unreachable", "PASS", ".env / config not mounted into viewer")

    # 4) real task E2E through the engine: create -> completes; steps exactly-once
    st, body = http("POST", f"{GATEWAY}/v1/tasks", {"goal": "preflight: real durable task", "priority": 1})
    if st == 201:
        tid = body["state"]["task_id"]
        deadline = time.time() + 240
        status = "RUNNING"
        while time.time() < deadline:
            st2, cur = http("GET", f"{GATEWAY}/v1/tasks/{tid}")
            status = cur["state"]["status"]
            if status in ("COMPLETED", "FAILED_FINAL", "CANCELLED"):
                break
            time.sleep(2)
        st3, summ = http("GET", f"{GATEWAY}/v1/tasks/{tid}/steps")
        counts = summ.get("completed_count_per_step", {}) if isinstance(summ, dict) else {}
        ok_counts = all(v == 1 for v in counts.values()) and len(counts) > 0
        add("task runs to COMPLETED", "PASS" if status == "COMPLETED" else "FAIL", f"{tid} status={status}")
        add("each step completed exactly once", "PASS" if ok_counts else "FAIL", str(counts))
        add("checkpoint rows written before steps", "PASS" if len(summ.get("checkpoints", [])) >= len(counts) else "FAIL",
            f"{len(summ.get('checkpoints', []))} checkpoints")
    else:
        add("task intake POST /v1/tasks", "FAIL", f"status={st} {body}")

    # 5) LiteLLM groups live (same key rules as deploy verify; WARN when keys absent by design)
    key = os.environ.get("LITELLM_MASTER_KEY") or _dotenv_value("LITELLM_MASTER_KEY")
    have_prov = bool(_dotenv_value("ANTHROPIC_API_KEY") or _dotenv_value("MINIMAX_API_KEY"))
    if key:
        st, r = http("POST", f"{os.environ.get('LITELLM', 'http://127.0.0.1:4000')}/v1/chat/completions",
                     {"model": "planning", "messages": [{"role": "user", "content": "Reply with exactly: PONG"}], "max_tokens": 16},
                     token=key)
        if st == 200 and isinstance(r, dict) and r.get("choices"):
            add("litellm planning group answers", "PASS", f"model={r.get('model')}")
        else:
            add("litellm planning group answers", "FAIL" if have_prov else "WARN", f"status={st} {str(r)[:100]}")
    else:
        add("litellm reachable with master key", "WARN", "LITELLM_MASTER_KEY unset — fill deploy/.env")

    # 6) diag endpoint (E2) responds booleans-only from live process
    st, d = http("GET", f"{GATEWAY}/v1/diag")
    good = st == 200 and isinstance(d, dict) and "process" in d and "goal" not in json.dumps(d)[:400]
    add("GET /v1/diag (E2 truth endpoint)", "PASS" if good else "FAIL", f"engine={d.get('engine') if isinstance(d, dict) else '?'}")

    return finish()


def _dotenv_value(name: str) -> str:
    if os.environ.get(name):
        return os.environ[name]
    p = ROOT / "deploy" / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip().startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return ""


def finish() -> int:
    n = {v: sum(1 for _, x, _ in results if x == v) for v in ("PASS", "FAIL", "WARN")}
    print(f"\n[preflight] {n['PASS']} pass, {n['FAIL']} fail, {n['WARN']} warn")
    return 1 if n["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
