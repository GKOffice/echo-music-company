"""
ECHO Agent Message Bus
Redis-backed publish/subscribe and task queue system.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Awaitable, Optional
import redis.asyncio as aioredis
import os

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class MessageBus:
    """Redis message bus for inter-agent communication."""

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._subscriptions: dict[str, list[Callable]] = {}

    async def connect(self):
        self._client = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        self._pubsub = self._client.pubsub()
        logger.info("MessageBus connected to Redis")

    async def disconnect(self):
        if self._pubsub:
            await self._pubsub.close()
        if self._client:
            await self._client.aclose()
        logger.info("MessageBus disconnected")

    async def publish(self, topic: str, payload: dict[str, Any]) -> int:
        """Publish a message to a topic. Returns number of subscribers."""
        if not self._client:
            raise RuntimeError("Bus not connected")
        message = json.dumps({"topic": topic, "payload": payload})
        count = await self._client.publish(f"echo:{topic}", message)
        logger.debug(f"Published to {topic}: {count} subscribers")
        return count

    async def subscribe(self, topic: str, handler: Callable[[dict], Awaitable[None]]):
        """Subscribe to a topic with an async handler."""
        channel = f"echo:{topic}"
        if channel not in self._subscriptions:
            self._subscriptions[channel] = []
            await self._pubsub.subscribe(channel)
        self._subscriptions[channel].append(handler)
        logger.info(f"Subscribed to {topic}")

    async def listen(self):
        """Start listening for messages. Run as background task."""
        if not self._pubsub:
            raise RuntimeError("Bus not connected")
        async for message in self._pubsub.listen():
            if message["type"] != "message":
                continue
            channel = message["channel"]
            try:
                data = json.loads(message["data"])
                handlers = self._subscriptions.get(channel, [])
                for handler in handlers:
                    asyncio.create_task(handler(data))
            except Exception as e:
                logger.error(f"Error handling message on {channel}: {e}")

    async def enqueue_task(self, agent_id: str, task: dict[str, Any]):
        """Push a task to an agent's Redis Stream."""
        if not self._client:
            raise RuntimeError("Bus not connected")
        await self._client.xadd(
            f"agent:tasks:{agent_id}",
            {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in task.items()},
            maxlen=10000,
        )

    async def dequeue_task(
        self,
        agent_id: str,
        group: str = "workers",
        consumer: str = "default",
        count: int = 1,
        block_ms: int = 5000,
    ) -> list[dict]:
        """Read tasks from an agent's Redis Stream (consumer group)."""
        if not self._client:
            raise RuntimeError("Bus not connected")

        stream = f"agent:tasks:{agent_id}"
        try:
            await self._client.xgroup_create(stream, group, id="0", mkstream=True)
        except Exception:
            pass

        results = await self._client.xreadgroup(
            group,
            consumer,
            {stream: ">"},
            count=count,
            block=block_ms,
        )

        tasks = []
        if results:
            for _, messages in results:
                for msg_id, data in messages:
                    task = {k: _try_parse_json(v) for k, v in data.items()}
                    task["_stream_id"] = msg_id
                    tasks.append(task)
        return tasks

    async def ack_task(self, agent_id: str, group: str, message_id: str):
        """Acknowledge a task as processed."""
        if not self._client:
            raise RuntimeError("Bus not connected")
        await self._client.xack(f"agent:tasks:{agent_id}", group, message_id)

    async def set_agent_state(self, agent_id: str, state: dict[str, Any]):
        """Store agent state in Redis."""
        if not self._client:
            raise RuntimeError("Bus not connected")
        await self._client.hset(
            f"agent:state:{agent_id}",
            mapping={k: json.dumps(v) if isinstance(v, (dict, list, bool)) else str(v) for k, v in state.items()},
        )
        await self._client.expire(f"agent:state:{agent_id}", 86400)

    async def get_agent_state(self, agent_id: str) -> dict[str, Any]:
        """Retrieve agent state from Redis."""
        if not self._client:
            raise RuntimeError("Bus not connected")
        raw = await self._client.hgetall(f"agent:state:{agent_id}")
        return {k: _try_parse_json(v) for k, v in raw.items()}

    async def broadcast_status(self, agent_id: str, status: str, details: dict = None):
        """Broadcast agent status update."""
        await self.publish(
            "agent.status",
            {"agent_id": agent_id, "status": status, "details": details or {}},
        )


def _try_parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


bus = MessageBus()
