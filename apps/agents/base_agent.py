"""
ECHO Base Agent
All 21 ECHO agents inherit from this class.
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg
from pydantic import BaseModel

from bus import bus
from guardrails import ConfidenceGate, GuardrailStatus
from memory_store import AgentMemoryStore, ErrorType

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://echo:echo_dev@localhost:5432/echo",
).replace("postgresql+asyncpg://", "postgresql://")


class AgentTask(BaseModel):
    task_id: str
    task_type: str
    priority: str = "normal"
    payload: dict = {}
    release_id: Optional[str] = None
    artist_id: Optional[str] = None


class AgentResult(BaseModel):
    success: bool
    task_id: str
    agent_id: str
    result: dict = {}
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class BaseAgent(ABC):
    """
    Base class for all ECHO agents.

    Each agent:
    - Has a unique agent_id and human-readable name
    - Connects to Redis message bus and PostgreSQL
    - Processes tasks from its dedicated stream
    - Can publish messages to other agents
    - Logs all activity to the database
    """

    agent_id: str = "base"
    agent_name: str = "Base Agent"
    subscriptions: list[str] = []

    def __init__(self):
        self._db_pool: Optional[asyncpg.Pool] = None
        self._running = False
        self._task_count = 0
        self._error_count = 0
        self._consecutive_errors = 0  # Circuit breaker counter
        self._started_at: Optional[datetime] = None
        self._memory_store: Optional[AgentMemoryStore] = None
        self._confidence_gate = ConfidenceGate()

    @property
    def is_healthy(self) -> bool:
        """Returns False if agent has hit 5+ consecutive errors (circuit breaker tripped)."""
        return self._consecutive_errors < 5

    async def start(self):
        """Start the agent — connect to services and begin processing."""
        logger.info(f"[{self.agent_id}] Starting {self.agent_name}...")
        self._started_at = datetime.now(timezone.utc)
        self._running = True

        await self._connect_db()

        for topic in self.subscriptions:
            await bus.subscribe(topic, self._handle_bus_message)

        await bus.broadcast_status(self.agent_id, "online")
        await self.on_start()

        logger.info(f"[{self.agent_id}] {self.agent_name} is online")

        await asyncio.gather(
            self._process_loop(),
            bus.listen() if not self.subscriptions else asyncio.sleep(0),
        )

    async def stop(self):
        """Gracefully stop the agent."""
        logger.info(f"[{self.agent_id}] Stopping...")
        self._running = False
        await bus.broadcast_status(self.agent_id, "offline")
        await self.on_stop()
        if self._db_pool:
            await self._db_pool.close()
        logger.info(f"[{self.agent_id}] Stopped. Tasks processed: {self._task_count}, Errors: {self._error_count}")

    async def _connect_db(self):
        try:
            self._db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
            logger.info(f"[{self.agent_id}] Database connected")
            self._memory_store = AgentMemoryStore(pool=self._db_pool)
            await self._memory_store.ensure_table()
        except Exception as e:
            logger.error(f"[{self.agent_id}] Database connection failed: {e}")

    async def _process_loop(self):
        """Main task processing loop — pulls from agent's Redis Stream."""
        while self._running:
            try:
                tasks = await bus.dequeue_task(
                    self.agent_id,
                    group=f"{self.agent_id}_workers",
                    consumer=f"{self.agent_id}_1",
                    count=5,
                    block_ms=2000,
                )

                for task_data in tasks:
                    stream_id = task_data.pop("_stream_id", None)
                    task = AgentTask(
                        task_id=task_data.get("task_id", "unknown"),
                        task_type=task_data.get("task_type", "unknown"),
                        priority=task_data.get("priority", "normal"),
                        payload=task_data.get("payload", {}),
                        release_id=task_data.get("release_id"),
                        artist_id=task_data.get("artist_id"),
                    )

                    start_ms = asyncio.get_event_loop().time()
                    try:
                        await self._mark_task_running(task.task_id)
                        result = await self.handle_task(task)
                        elapsed_ms = int((asyncio.get_event_loop().time() - start_ms) * 1000)
                        result.duration_ms = elapsed_ms
                        result = await self._run_with_guardrails(task, result)
                        await self._mark_task_complete(task.task_id, result)
                        self._task_count += 1
                        self._consecutive_errors = 0  # Reset circuit breaker on success
                    except Exception as e:
                        self._error_count += 1
                        self._consecutive_errors += 1
                        logger.error(f"[{self.agent_id}] Task {task.task_id} failed: {e}")
                        await self._mark_task_failed(task.task_id, str(e))
                        if self._consecutive_errors >= 5:
                            logger.critical(
                                f"[{self.agent_id}] Circuit breaker TRIPPED — "
                                f"{self._consecutive_errors} consecutive errors. Backing off 60s."
                            )
                    finally:
                        if stream_id:
                            await bus.ack_task(
                                self.agent_id,
                                f"{self.agent_id}_workers",
                                stream_id,
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_errors += 1
                logger.error(f"[{self.agent_id}] Process loop error: {e}")
                if self._consecutive_errors >= 5:
                    logger.critical(
                        f"[{self.agent_id}] Circuit breaker TRIPPED — backing off 60s"
                    )
                    await asyncio.sleep(60)
                else:
                    await asyncio.sleep(5)

    async def _handle_bus_message(self, message: dict):
        """Handle a pub/sub message from the bus."""
        try:
            await self.on_message(message)
        except Exception as e:
            logger.error(f"[{self.agent_id}] Message handler error: {e}")

    async def _mark_task_running(self, task_id: str):
        if not self._db_pool:
            return
        await self._db_pool.execute(
            "UPDATE agent_tasks SET status = 'running', started_at = NOW() WHERE id = $1::uuid",
            task_id,
        )

    async def _mark_task_complete(self, task_id: str, result: AgentResult):
        if not self._db_pool:
            return
        import json
        await self._db_pool.execute(
            """
            UPDATE agent_tasks
            SET status = 'completed', completed_at = NOW(), result_json = $2::jsonb
            WHERE id = $1::uuid
            """,
            task_id,
            json.dumps(result.result),
        )

    async def _mark_task_failed(self, task_id: str, error: str):
        if not self._db_pool:
            return
        import json
        await self._db_pool.execute(
            """
            UPDATE agent_tasks
            SET status = 'failed', completed_at = NOW(), result_json = $2::jsonb
            WHERE id = $1::uuid
            """,
            task_id,
            json.dumps({"error": error}),
        )

    async def send_message(
        self,
        to_agent: str,
        topic: str,
        payload: dict,
        priority: str = "normal",
    ):
        """Send a message to another agent via the bus."""
        await bus.publish(
            f"agent.{to_agent}",
            {
                "from_agent": self.agent_id,
                "to_agent": to_agent,
                "topic": topic,
                "payload": payload,
                "priority": priority,
            },
        )

    async def broadcast(self, topic: str, payload: dict):
        """Broadcast a message to all subscribers of a topic."""
        await bus.publish(topic, {"from_agent": self.agent_id, **payload})

    async def db_fetch(self, query: str, *args) -> list[dict]:
        """Execute a SELECT query and return list of row dicts."""
        if not self._db_pool:
            return []
        rows = await self._db_pool.fetch(query, *args)
        return [dict(row) for row in rows]

    async def db_fetchrow(self, query: str, *args) -> Optional[dict]:
        """Execute a SELECT query and return single row dict."""
        if not self._db_pool:
            return None
        row = await self._db_pool.fetchrow(query, *args)
        return dict(row) if row else None

    async def db_execute(self, query: str, *args) -> str:
        """Execute a non-SELECT query."""
        if not self._db_pool:
            return ""
        return await self._db_pool.execute(query, *args)

    async def log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: dict = None,
    ):
        """Write an audit log entry."""
        if not self._db_pool:
            return
        import json
        await self._db_pool.execute(
            """
            INSERT INTO audit_log (actor_type, actor_id, action, resource_type, resource_id, details)
            VALUES ('agent', NULL, $1, $2, $3::uuid, $4::jsonb)
            """,
            action,
            resource_type,
            resource_id,
            json.dumps(details or {"agent_id": self.agent_id}),
        )

    # ----------------------------------------------------------------
    # Guardrails & learning system
    # ----------------------------------------------------------------

    async def _run_with_guardrails(self, task: "AgentTask", result: "AgentResult") -> "AgentResult":
        """
        Run confidence gate on every result before it is written to DB.

        - PASS: log success to memory store, return result unchanged.
        - FAIL: log failure to memory store, replace result with safe not-found response.
        """
        gate_result = self._confidence_gate.check(
            result.result, self.agent_id, task.task_type
        )

        if gate_result.passed:
            if self._memory_store:
                await self._memory_store.log_success(
                    self.agent_id, task.task_type, result.result,
                    confidence_score=gate_result.confidence,
                )
            return result

        # Gate failed — log and replace with safe response
        logger.warning(
            f"[{self.agent_id}] Guardrail FAIL on task {task.task_id} "
            f"({task.task_type}): {gate_result.reason}"
        )
        if self._memory_store:
            await self._memory_store.log_failure(
                agent_id=self.agent_id,
                task_type=task.task_type,
                input_data=task.payload,
                bad_output=result.result,
                error_type=ErrorType.LOW_CONFIDENCE,
                correction=gate_result.reason,
                confidence_score=gate_result.confidence,
            )

        safe = gate_result.safe_response or {
            "found": False,
            "reason": gate_result.reason,
            "task_type": task.task_type,
        }
        result.result = safe
        return result

    async def _get_context_from_memory(self, task_type: str) -> str:
        """
        Query memory store for recent failure patterns for this agent+task_type
        and return a formatted warning block for LLM prompt injection.
        """
        if not self._memory_store:
            return ""
        patterns = await self._memory_store.get_failure_patterns(
            self.agent_id, task_type, limit=10
        )
        return AgentMemoryStore.format_patterns_for_prompt(patterns)

    async def _build_prompt_with_memory(self, base_prompt: str, task_type: str) -> str:
        """
        Append known failure patterns to a base LLM prompt so the model
        avoids repeating previous mistakes.
        """
        memory_context = await self._get_context_from_memory(task_type)
        if not memory_context:
            return base_prompt
        return f"{base_prompt}\n\n{memory_context}"

    # ----------------------------------------------------------------
    # Abstract / override methods
    # ----------------------------------------------------------------

    @abstractmethod
    async def handle_task(self, task: AgentTask) -> AgentResult:
        """Process a task. Must be implemented by each agent."""
        ...

    async def on_start(self):
        """Called after connections are established. Override for init logic."""
        pass

    async def on_stop(self):
        """Called before shutdown. Override for cleanup logic."""
        pass

    async def on_message(self, message: dict):
        """Called when a subscribed bus message is received. Override to handle."""
        pass

    @property
    def status(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "running": self._running,
            "task_count": self._task_count,
            "error_count": self._error_count,
            "started_at": self._started_at.isoformat() if self._started_at else None,
        }
