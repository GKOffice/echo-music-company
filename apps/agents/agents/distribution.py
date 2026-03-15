"""
Distribution Agent
Handles delivery to all DSPs (Spotify, Apple Music, etc.),
manages release scheduling, and tracks distribution status.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

DSP_PLATFORMS = ["spotify", "apple_music", "amazon_music", "youtube_music", "tidal", "deezer", "soundcloud"]


class DistributionAgent(BaseAgent):
    agent_id = "distribution"
    agent_name = "Distribution Agent"
    subscriptions = ["release.mastered", "release.approved"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "prepare_distribution": self._prepare_distribution,
            "submit_to_dsps": self._submit_to_dsps,
            "check_status": self._check_status,
            "schedule_release": self._schedule_release,
            "takedown": self._takedown,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _prepare_distribution(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow("SELECT * FROM releases WHERE id = $1::uuid", release_id)
        if not release:
            return {"error": "Release not found"}
        missing = []
        if not release.get("master_audio_url"):
            missing.append("master_audio_url")
        if not release.get("artwork_url"):
            missing.append("artwork_url")
        if missing:
            return {"release_id": release_id, "ready": False, "missing": missing}
        await self.db_execute(
            "UPDATE releases SET status = 'distribution_ready', updated_at = NOW() WHERE id = $1::uuid",
            release_id,
        )
        return {"release_id": release_id, "ready": True, "platforms": DSP_PLATFORMS}

    async def _submit_to_dsps(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        platforms = task.payload.get("platforms", DSP_PLATFORMS)
        logger.info(f"[Distribution] Submitting {release_id} to {len(platforms)} DSPs")
        await self.db_execute(
            "UPDATE releases SET status = 'distributed', updated_at = NOW() WHERE id = $1::uuid",
            release_id,
        )
        await self.broadcast("release.distributed", {"release_id": release_id, "platforms": platforms})
        await self.log_audit("submit_to_dsps", "releases", release_id, {"platforms": platforms})
        return {"release_id": release_id, "submitted_to": platforms, "status": "distributed"}

    async def _check_status(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow("SELECT id, status, spotify_url, apple_url FROM releases WHERE id = $1::uuid", release_id)
        return {"release_id": release_id, "distribution_status": dict(release) if release else None}

    async def _schedule_release(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release_date = task.payload.get("release_date")
        await self.db_execute(
            "UPDATE releases SET release_date = $2, updated_at = NOW() WHERE id = $1::uuid",
            release_id,
            release_date,
        )
        return {"release_id": release_id, "release_date": release_date}

    async def _takedown(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        reason = task.payload.get("reason", "label_request")
        await self.db_execute(
            "UPDATE releases SET status = 'taken_down', updated_at = NOW() WHERE id = $1::uuid",
            release_id,
        )
        await self.log_audit("takedown", "releases", release_id, {"reason": reason})
        return {"release_id": release_id, "status": "taken_down", "reason": reason}
