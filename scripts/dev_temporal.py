"""Dev/test Temporal server without Docker (laptop sanity runs + CI + sandboxes).
Uses the SDK's local test server; address is written to data/temporal_addr.json which the
worker/gateway/acceptance test auto-read. NOTE: test-server state is in-RAM — for the REAL
durability acceptance run on your machine, use the compose stack (deploy/scripts/setup)."""
import asyncio
import json
import os
import pathlib

from temporalio.testing import WorkflowEnvironment

ROOT = pathlib.Path(os.environ.get("AGENTOS_ROOT", pathlib.Path(__file__).resolve().parents[1]))
OUT = ROOT / "data" / "temporal_addr.json"


async def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    env = await WorkflowEnvironment.start_local()
    OUT.write_text(json.dumps({"host": env.client.address, "namespace": env.client.namespace or "default"}))
    print(f"temporal test-server: {env.client.address} ns={env.client.namespace} (pid {os.getpid()})", flush=True)
    try:
        while True:
            await asyncio.sleep(300)
    finally:
        OUT.unlink(missing_ok=True)
        await env.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
