"""
YouTube Agent
Manages YouTube channel operations — uploads, monetization,
Content ID, Shorts strategy, and analytics.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class YouTubeAgent(BaseAgent):
    agent_id = "youtube"
    agent_name = "YouTube Agent"
    subscriptions = ["release.distributed"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "upload_video": self._upload_video,
            "enable_monetization": self._enable_monetization,
            "create_short": self._create_short,
            "content_id_claim": self._content_id_claim,
            "channel_report": self._channel_report,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _upload_video(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow("SELECT title FROM releases WHERE id = $1::uuid", release_id)
        title = release["title"] if release else "New Release"
        logger.info(f"[YouTube] Uploading video for: {title}")
        youtube_url = f"https://youtube.com/watch?v=placeholder_{(release_id or 'new')[:8]}"
        await self.db_execute(
            "UPDATE releases SET youtube_url = $2, updated_at = NOW() WHERE id = $1::uuid",
            release_id, youtube_url,
        )
        return {"release_id": release_id, "youtube_url": youtube_url, "status": "uploaded"}

    async def _enable_monetization(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        return {"release_id": release_id, "monetization": "enabled", "ad_formats": ["overlay", "skippable"]}

    async def _create_short(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        clip_duration = task.payload.get("clip_duration_seconds", 30)
        return {"release_id": release_id, "short_created": True, "duration": clip_duration, "status": "processing"}

    async def _content_id_claim(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        return {"track_id": track_id, "content_id_registered": True, "policy": "monetize"}

    async def _channel_report(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow("SELECT youtube_channel_id FROM artists WHERE id = $1::uuid", artist_id)
        return {
            "artist_id": artist_id,
            "channel_id": artist["youtube_channel_id"] if artist else None,
            "subscribers": 0,
            "views_30d": 0,
            "revenue_30d": 0.0,
        }

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
