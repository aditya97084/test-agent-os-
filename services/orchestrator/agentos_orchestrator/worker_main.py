"""Standalone Temporal worker for the durable task queue. `python -m agentos_orchestrator`."""
from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from agentos_contracts.config import get_settings
from agentos_db import ensure_schema
from agentos_orchestrator.activities import ACTIVITIES
from agentos_orchestrator.workflows import TaskExecution


async def run() -> None:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    log = logging.getLogger("agentos.worker")
    if settings.engine == "local":
        log.info("AGENTOS_ENGINE=local(dev) — gateway executes tasks in-process; no worker needed. exiting cleanly.")
        return
    await ensure_schema()
    log.info("connecting temporal %s ns=%s queue=%s", settings.temporal_host, settings.temporal_ns, settings.task_queue)
    client = await Client.connect(settings.temporal_host, namespace=settings.temporal_ns)
    worker = Worker(
        client,
        task_queue=settings.task_queue,
        workflows=[TaskExecution],
        activities=ACTIVITIES,
    )
    log.info("worker online")
    await worker.run()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
