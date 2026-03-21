"""
Agent Memory Store

Persistent storage for agent failures and successes, backed by PostgreSQL.
Failure patterns survive restarts and are injected into future LLM prompts.
"""

import json
import logging
from enum import Enum
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)

# DDL — matches apps/api/migrations/add_agent_memory.sql
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(50) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    error_type VARCHAR(50),
    input_summary TEXT,
    bad_output_summary TEXT,
    correction TEXT,
    confidence_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_success BOOLEAN DEFAULT FALSE
);
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_agent_memory_lookup
    ON agent_memory(agent_id, task_type, created_at DESC);
"""


class ErrorType(str, Enum):
    HALLUCINATION = "HALLUCINATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    API_ERROR = "API_ERROR"


class AgentMemoryStore:
    """
    Persistent memory for agent failures and successes.

    Pass the agent's existing asyncpg.Pool to share the connection pool,
    or leave it None to silently no-op (useful in tests / early boot).
    """

    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        self._pool = pool

    async def ensure_table(self):
        """Idempotently create the agent_memory table and index."""
        if not self._pool:
            return
        try:
            await self._pool.execute(_CREATE_TABLE_SQL)
            await self._pool.execute(_CREATE_INDEX_SQL)
        except Exception as e:
            logger.error(f"[MemoryStore] ensure_table failed: {e}")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def log_failure(
        self,
        agent_id: str,
        task_type: str,
        input_data: dict,
        bad_output: dict,
        error_type: "ErrorType | str",
        correction: str = "",
        confidence_score: float = 0.0,
    ):
        """Persist a failure pattern so future prompts can avoid it."""
        if not self._pool:
            return
        try:
            error_str = error_type.value if isinstance(error_type, ErrorType) else str(error_type)
            input_summary = json.dumps(input_data, default=str)[:1000]
            bad_output_summary = json.dumps(bad_output, default=str)[:1000]
            await self._pool.execute(
                """
                INSERT INTO agent_memory
                    (agent_id, task_type, error_type, input_summary,
                     bad_output_summary, correction, confidence_score, is_success)
                VALUES ($1, $2, $3, $4, $5, $6, $7, FALSE)
                """,
                agent_id, task_type, error_str,
                input_summary, bad_output_summary,
                correction, confidence_score,
            )
            logger.debug(f"[MemoryStore] failure logged: {agent_id}/{task_type} [{error_str}]")
        except Exception as e:
            logger.error(f"[MemoryStore] log_failure error: {e}")

    async def log_success(
        self,
        agent_id: str,
        task_type: str,
        output_data: dict,
        confidence_score: float = 1.0,
    ):
        """Persist a success example (used to calibrate what good looks like)."""
        if not self._pool:
            return
        try:
            output_summary = json.dumps(output_data, default=str)[:1000]
            await self._pool.execute(
                """
                INSERT INTO agent_memory
                    (agent_id, task_type, bad_output_summary, confidence_score, is_success)
                VALUES ($1, $2, $3, $4, TRUE)
                """,
                agent_id, task_type, output_summary, confidence_score,
            )
        except Exception as e:
            logger.error(f"[MemoryStore] log_success error: {e}")

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_failure_patterns(
        self, agent_id: str, task_type: str, limit: int = 10
    ) -> list[dict]:
        """Retrieve recent failure patterns for injection into LLM prompts."""
        if not self._pool:
            return []
        try:
            rows = await self._pool.fetch(
                """
                SELECT error_type, input_summary, bad_output_summary,
                       correction, confidence_score
                FROM agent_memory
                WHERE agent_id = $1
                  AND task_type = $2
                  AND is_success = FALSE
                ORDER BY created_at DESC
                LIMIT $3
                """,
                agent_id, task_type, limit,
            )
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"[MemoryStore] get_failure_patterns error: {e}")
            return []

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    @staticmethod
    def format_patterns_for_prompt(patterns: list[dict]) -> str:
        """
        Format failure patterns as a warning block for LLM prompt injection.

        Example output:
            KNOWN FAILURE PATTERNS (do not repeat these mistakes):
            - [HALLUCINATION] Bad output: {"name": "Dorin Hirvi"...} → Correction: Artist not in any music DB
        """
        if not patterns:
            return ""
        lines = ["KNOWN FAILURE PATTERNS (do not repeat these mistakes):"]
        for p in patterns:
            error_type = p.get("error_type", "UNKNOWN")
            bad = (p.get("bad_output_summary") or "")[:200]
            correction = p.get("correction", "")
            line = f"- [{error_type}] Bad output: {bad}"
            if correction:
                line += f" → Correction: {correction}"
            lines.append(line)
        return "\n".join(lines)
