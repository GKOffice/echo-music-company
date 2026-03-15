"""
Production Agent
Manages recording sessions, coordinates with producers, handles
mixing/mastering workflow, and tracks asset delivery.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class ProductionAgent(BaseAgent):
    agent_id = "production"
    agent_name = "Production Agent"
    subscriptions = ["artist.signed", "release.created"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "schedule_session": self._schedule_session,
            "assign_producer": self._assign_producer,
            "track_delivery": self._track_delivery,
            "request_revision": self._request_revision,
            "approve_master": self._approve_master,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _schedule_session(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        artist_id = task.payload.get("artist_id") or task.artist_id
        logger.info(f"[Production] Scheduling session for release {release_id}")
        await self.db_execute(
            "UPDATE releases SET status = 'in_production', updated_at = NOW() WHERE id = $1::uuid",
            release_id,
        )
        return {"release_id": release_id, "status": "session_scheduled"}

    async def _assign_producer(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id")
        genre = task.payload.get("genre", "")
        producers = await self.db_fetch(
            "SELECT id, name, quality_score FROM producers WHERE status = 'active' AND $1 = ANY(genres) ORDER BY quality_score DESC LIMIT 5",
            genre,
        )
        if not producers:
            producers = await self.db_fetch(
                "SELECT id, name, quality_score FROM producers WHERE status = 'active' ORDER BY quality_score DESC LIMIT 5"
            )
        return {"release_id": release_id, "recommended_producers": producers}

    async def _track_delivery(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id")
        master_url = task.payload.get("master_url")
        if master_url:
            await self.db_execute(
                "UPDATE releases SET master_audio_url = $2, updated_at = NOW() WHERE id = $1::uuid",
                release_id,
                master_url,
            )
        return {"release_id": release_id, "master_url": master_url, "status": "delivered"}

    async def _request_revision(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id")
        notes = task.payload.get("notes", "")
        logger.info(f"[Production] Revision requested for {release_id}: {notes}")
        return {"release_id": release_id, "revision_requested": True, "notes": notes}

    async def _approve_master(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id")
        await self.db_execute(
            "UPDATE releases SET status = 'mastered', updated_at = NOW() WHERE id = $1::uuid",
            release_id,
        )
        await self.send_message("qc", "quality_check", {"release_id": release_id})
        await self.log_audit("approve_master", "releases", release_id)
        return {"release_id": release_id, "status": "mastered"}
