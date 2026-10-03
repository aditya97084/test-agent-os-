"""Event bus: Redis pub/sub when AGENTOS_REDIS_URL is set, otherwise no-op publish
(the gateway WS tailer reads Postgres truth directly — events are a stream, never a source)."""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

CHANNEL = "agentos:events"
_redis = None


def _redis_enabled() -> bool:
    return bool(os.environ.get("AGENTOS_REDIS_URL"))


async def publish_event(task_id: str, data: dict[str, Any]) -> None:
    global _redis
    if not _redis_enabled():
        return
    try:
        if _redis is None:
            import redis.asyncio as redis

            _redis = redis.from_url(os.environ["AGENTOS_REDIS_URL"])
        await _redis.publish(CHANNEL, json.dumps({"task_id": task_id, **data}))
    except Exception:  # events must never break task execution
        pass


async def subscribe_events(queue: asyncio.Queue) -> None:
    """Redis -> queue relay for the gateway WS hub."""
    if not _redis_enabled():
        return
    try:
        import redis.asyncio as redis

        r = redis.from_url(os.environ["AGENTOS_REDIS_URL"])
        pub = r.pubsub()
        await pub.subscribe(CHANNEL)
        async for msg in pub.listen():
            if msg.get("type") == "message":
                try:
                    queue.put_nowait(json.loads(msg["data"]))
                except Exception:
                    pass
    except Exception:
        return
