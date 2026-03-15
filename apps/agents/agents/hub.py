"""
Hub Agent
Manages the Beat Hub marketplace — scores beats, matches them
to artists, facilitates deals, and pays producers.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class HubAgent(BaseAgent):
    agent_id = "hub"
    agent_name = "Hub Agent"
    subscriptions = ["beat.submitted", "artist.needs_production"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "score_beat": self._score_beat,
            "match_beat_to_artist": self._match_beat_to_artist,
            "process_placement": self._process_placement,
            "pay_producer": self._pay_producer,
            "hub_stats": self._hub_stats,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _score_beat(self, task: AgentTask) -> dict:
        beat_id = task.payload.get("beat_id")
        if not beat_id:
            return {"error": "beat_id required"}
        quality = task.payload.get("quality_score", 75.0)
        uniqueness = task.payload.get("uniqueness_score", 70.0)
        sync = task.payload.get("sync_readiness", 65.0)
        await self.db_execute(
            "UPDATE hub_beats SET quality_score = $2, uniqueness_score = $3, sync_readiness = $4, status = 'available' WHERE id = $1::uuid",
            beat_id, quality, uniqueness, sync,
        )
        return {"beat_id": beat_id, "quality": quality, "uniqueness": uniqueness, "sync": sync}

    async def _match_beat_to_artist(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow("SELECT genre FROM artists WHERE id = $1::uuid", artist_id)
        if not artist:
            return {"error": "Artist not found"}
        genre = artist.get("genre", "")
        beats = await self.db_fetch(
            "SELECT id, title, bpm, key, quality_score FROM hub_beats WHERE status = 'available' AND $1 = ANY(genre) ORDER BY quality_score DESC LIMIT 10",
            genre,
        )
        if not beats:
            beats = await self.db_fetch(
                "SELECT id, title, bpm, key, quality_score FROM hub_beats WHERE status = 'available' ORDER BY quality_score DESC LIMIT 10"
            )
        return {"artist_id": artist_id, "genre": genre, "matched_beats": beats}

    async def _process_placement(self, task: AgentTask) -> dict:
        beat_id = task.payload.get("beat_id")
        track_id = task.payload.get("track_id")
        deal_type = task.payload.get("deal_type", "non_exclusive")
        price = task.payload.get("price", 0.0)
        await self.db_execute(
            "UPDATE hub_beats SET status = 'placed', placed_on_track_id = $2::uuid, purchase_count = purchase_count + 1 WHERE id = $1::uuid",
            beat_id, track_id,
        )
        await self.log_audit("beat_placement", "hub_beats", beat_id, {"track_id": track_id, "price": price})
        return {"beat_id": beat_id, "track_id": track_id, "deal_type": deal_type, "price": price}

    async def _pay_producer(self, task: AgentTask) -> dict:
        producer_id = task.payload.get("producer_id")
        amount = task.payload.get("amount", 0.0)
        await self.db_execute(
            "UPDATE producers SET total_earned = total_earned + $2, updated_at = NOW() WHERE id = $1::uuid",
            producer_id, amount,
        )
        return {"producer_id": producer_id, "amount_paid": amount, "channel": "stripe"}

    async def _hub_stats(self, task: AgentTask) -> dict:
        stats = await self.db_fetchrow(
            """
            SELECT
              COUNT(*) as total_beats,
              COUNT(*) FILTER (WHERE status = 'available') as available,
              COUNT(*) FILTER (WHERE status = 'placed') as placed,
              COALESCE(AVG(quality_score), 0) as avg_quality
            FROM hub_beats
            """
        )
        return dict(stats) if stats else {}

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
