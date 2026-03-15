"""
Analytics Agent
Tracks streaming performance, generates insights, monitors
artist growth, and provides data to all other agents.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class AnalyticsAgent(BaseAgent):
    agent_id = "analytics"
    agent_name = "Analytics Agent"
    subscriptions = ["release.distributed", "royalties.received"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "track_release": self._track_release,
            "artist_report": self._artist_report,
            "streaming_snapshot": self._streaming_snapshot,
            "echo_score_update": self._echo_score_update,
            "top_tracks": self._top_tracks,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _track_release(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        return {"release_id": release_id, "tracking": True, "metrics": ["streams", "saves", "playlist_adds", "revenue"]}

    async def _artist_report(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow(
            "SELECT name, monthly_listeners, total_streams, echo_score, tier FROM artists WHERE id = $1::uuid", artist_id
        )
        releases = await self.db_fetch(
            "SELECT COUNT(*) as count, COALESCE(SUM(streams_total), 0) as total_streams FROM releases WHERE artist_id = $1::uuid",
            artist_id,
        )
        return {"artist": dict(artist) if artist else {}, "release_stats": releases[0] if releases else {}}

    async def _streaming_snapshot(self, task: AgentTask) -> dict:
        top = await self.db_fetch(
            "SELECT r.title, a.name, r.streams_total FROM releases r LEFT JOIN artists a ON r.artist_id = a.id ORDER BY r.streams_total DESC LIMIT 10"
        )
        return {"top_releases": top}

    async def _echo_score_update(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        new_score = task.payload.get("score", 0.0)
        await self.db_execute(
            "UPDATE artists SET echo_score = $2, updated_at = NOW() WHERE id = $1::uuid",
            artist_id, new_score,
        )
        tier = "platinum" if new_score >= 90 else "gold" if new_score >= 70 else "silver" if new_score >= 50 else "seed"
        await self.db_execute(
            "UPDATE artists SET tier = $2, updated_at = NOW() WHERE id = $1::uuid",
            artist_id, tier,
        )
        return {"artist_id": artist_id, "echo_score": new_score, "tier": tier}

    async def _top_tracks(self, task: AgentTask) -> dict:
        tracks = await self.db_fetch(
            "SELECT t.title, a.name, t.streams_total, t.revenue_total FROM tracks t LEFT JOIN artists a ON t.artist_id = a.id ORDER BY t.streams_total DESC LIMIT 20"
        )
        return {"top_tracks": tracks}
