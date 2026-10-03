#!/usr/bin/env python3
"""Phase 0 ACCEPTANCE — the definition of done for the entire spine.

Boots gateway + worker (own processes), creates the demo task (6 steps × 15 s per spec;
DEMO_STEP_SECONDS overrides for CI), lets it pass step 3, **SIGKILLs both processes**,
relaunches, and asserts:
  - task reaches COMPLETED
  - every step completed EXACTLY once (no repeated work after crash)
  - steps 4-6 completed AFTER the kill, steps 1-3 started BEFORE it (resume, not restart)
Engine: temporal when AGENTOS_TEMPORAL_HOST (or scripts/dev_temporal.py addr file) is
available; otherwise set AGENTOS_ENGINE=local (dev-only, prints a loud note).
PASS/FAIL + the actual step log is the required PROGRESS.md evidence (E1/Law 11).
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = pathlib.Path(os.environ.get("AGENTOS_ROOT", pathlib.Path(__file__).resolve().parents[2]))
PORT = int(os.environ.get("AGENTOS_ACCEPT_PORT", "8310"))
BASE = f"http://127.0.0.1:{PORT}"


def http(method: str, path: str, body: dict | None = None, timeout: int = 10, raw: bool = False):
    url = path if path.startswith("http") else BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read()
            return r.status, (b if raw else json.loads(b))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="ignore")
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def wait_health(procs: list[subprocess.Popen], deadline: float) -> dict:
    while time.time() < deadline:
        st, h = http("GET", "/v1/health", timeout=3)
        if st == 200 and isinstance(h, dict) and h.get("db"):
            return h
        for p in procs:
            if p.poll() is not None:
                raise RuntimeError(f"spawned process exited early rc={p.returncode}")
        time.sleep(1)
    raise RuntimeError("health timeout")


def resolve_temporal() -> tuple[str | None, str]:
    host = os.environ.get("AGENTOS_TEMPORAL_HOST")
    ns = os.environ.get("TEMPORAL_NAMESPACE", "")
    addr = ROOT / "data" / "temporal_addr.json"
    if not host and addr.exists():
        d = json.loads(addr.read_text())
        host, ns = d["host"], d.get("namespace", "default")
    return host, ns or "default"


started_ok = [False]


DB_URL = os.environ.get("AGENTOS_ACCEPT_DB", f"sqlite+aiosqlite:///{ROOT}/data/acceptance_{uuid.uuid4().hex[:6]}.db")


def spawn(logs_dir: pathlib.Path) -> tuple[list[subprocess.Popen], dict]:
    env = dict(os.environ)
    env.update(
        PYTHONPATH=str(ROOT / "packages/contracts") + os.pathsep + str(ROOT / "packages/db")
        + os.pathsep + str(ROOT / "packages/events") + os.pathsep + str(ROOT / "services/gateway")
        + os.pathsep + str(ROOT / "services/orchestrator"),
        AGENTOS_ROOT=str(ROOT),
        GATEWAY_PORT=str(PORT),
        AGENTOS_DB_URL=DB_URL,  # SAME durable store across the kill/restart — the whole point
    )
    host, ns = resolve_temporal()
    if host:
        env["AGENTOS_TEMPORAL_HOST"] = host
        env["TEMPORAL_NAMESPACE"] = ns
        env["AGENTOS_ENGINE"] = "temporal"
    else:
        env["AGENTOS_ENGINE"] = os.environ.get("AGENTOS_ENGINE", "local")
        print(f"[accept] NOTE: no temporal host found → engine={env['AGENTOS_ENGINE']} (dev-only path)")
    procs = []
    for name, mod in (("gateway", "agentos_gateway"), ("worker", "agentos_orchestrator")):
        f = open(logs_dir / f"{name}.log", "wb")
        procs.append(subprocess.Popen([sys.executable, "-m", mod], cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT))
    return procs, env


def kill_all(procs: list[subprocess.Popen]) -> float:
    for p in procs:
        try:
            p.kill()  # SIGKILL — the harshest honest crash
        except ProcessLookupError:
            pass
    for p in procs:
        p.wait(timeout=10)
    return time.time()


def main() -> int:
    logs = ROOT / "data"
    logs.mkdir(exist_ok=True)
    print("[accept] Phase 0 — kill app mid-task, relaunch, resume from same step")
    procs, env = spawn(logs)
    task_id = None
    try:
        h = wait_health(procs, time.time() + 60)
        started_ok[0] = True
        print(f"[accept] healthy. engine={h['engine']}")
        st, body = http("POST", "/v1/tasks", {"goal": "acceptance: durable resume", "priority": 1}, timeout=20)
        assert st == 201, f"intake failed {st} {body}"
        task_id = body["state"]["task_id"]
        total = int(env.get("DEMO_STEPS", os.environ.get("DEMO_STEPS", "6")))
        # wait until at least 3 steps completed
        deadline = time.time() + 60 + total * float(os.environ.get("DEMO_STEP_SECONDS", 15))
        while time.time() < deadline:
            st2, cur = http("GET", f"/v1/tasks/{task_id}")
            if st2 == 200 and len(cur["state"]["completed_steps"]) >= 3:
                break
            time.sleep(1)
        else:
            raise RuntimeError("never reached step 3 — killing anyway would prove nothing")
        pre = http("GET", f"/v1/tasks/{task_id}")[1]["state"]["completed_steps"]
        print(f"[accept] {len(pre)} steps done — SIGKILL gateway+worker now")
        kill_t = kill_all(procs)
        time.sleep(1.5)
        print("[accept] relaunched")
        procs2, _ = spawn(logs)
        wait_health(procs2, time.time() + 60)
        deadline = time.time() + 180 + total * float(os.environ.get("DEMO_STEP_SECONDS", 15))
        status = "UNKNOWN"
        while time.time() < deadline:
            st2, cur = http("GET", f"/v1/tasks/{task_id}")
            if st2 == 200:
                status = cur["state"]["status"]
                if status in ("COMPLETED", "FAILED_FINAL", "CANCELLED"):
                    break
            time.sleep(1.5)
        st3, summ = http("GET", f"/v1/tasks/{task_id}/steps")
        if not isinstance(summ, dict):
            raise RuntimeError(f"steps endpoint broken after restart: status={st3} body={summ}")
        counts = summ["completed_count_per_step"]
        rows = summ["steps"]
        print("[accept] ---- step log (from DB, not memory) ----")
        for r in rows:
            print(f"  {r['step']:<14} attempt={r['attempt']} {r['state']:<9} started={r['started_at']} completed={r['completed_at']}")
        ok = []
        ok.append(("COMPLETED reached", status == "COMPLETED"))
        ok.append(("every step completed exactly once", set(counts.values()) == {1} and len(counts) == total))
        first_start = {r["step"]: r["started_at"] for r in rows}
        last_done = {r["step"]: r["completed_at"] for r in rows if r["state"] == "completed"}
        kill_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(kill_t))
        early = [f"demo_step_{i}" for i in (1, 2, 3)]
        late = [f"demo_step_{i}" for i in range(4, total + 1)]
        ok.append(("steps 1-3 started before kill (no restart)", all((first_start.get(s) or "Z") < kill_iso for s in early)))
        if len(late) >= 1:
            ok.append(("post-kill steps completed after kill", all((last_done.get(s) or "0") > kill_iso for s in late)))
        diag = http("GET", "/v1/diag")[1]
        if env.get("AGENTOS_ENGINE") == "local":
            ok.append(("local engine resumed task on boot", diag.get("resumed_on_boot", 0) >= 1))
        print("[accept] ---- verdicts ----")
        allok = True
        for name, good in ok:
            print(f"  {'PASS' if good else 'FAIL'}  {name}")
            allok &= bool(good)
        print(f"\n[accept] RESULT: {'PASS ✅ durable resume proven' if allok else 'FAIL ❌'} (task={task_id}, engine={env.get('AGENTOS_ENGINE')})")
        kill_all(procs2)
        pathlib.Path(DB_URL.replace("sqlite+aiosqlite:///", "")).unlink(missing_ok=True)
        return 0 if allok else 1
    except Exception as e:  # noqa: BLE001
        print(f"[accept] RESULT: FAIL ❌ ({e})")
        for p in procs:
            try:
                p.kill()
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
