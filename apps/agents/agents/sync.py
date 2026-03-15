"""
Sync Agent
Handles sync licensing — pitches catalog to TV, film, ads,
and games. Manages sync tags, briefs, and deal negotiation.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class SyncAgent(BaseAgent):
    agent_id = "sync"
    agent_name = "Sync Agent"
    subscriptions = ["release.distributed"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "tag_for_sync": self._tag_for_sync,
            "pitch_sync": self._pitch_sync,
            "process_brief": self._process_brief,
            "catalog_search": self._catalog_search,
            "report_sync_revenue": self._report_sync_revenue,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _tag_for_sync(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        tags = task.payload.get("tags", {})
        import json
        await self.db_execute(
            "UPDATE tracks SET sync_tags_json = $2::jsonb WHERE id = $1::uuid",
            track_id, json.dumps(tags),
        )
        return {"track_id": track_id, "tags_applied": tags}

    async def _pitch_sync(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        opportunity = task.payload.get("opportunity", "")
        logger.info(f"[Sync] Pitching track {track_id} for: {opportunity}")
        return {"track_id": track_id, "opportunity": opportunity, "status": "pitched"}

    async def _process_brief(self, task: AgentTask) -> dict:
        brief = task.payload.get("brief", {})
        mood = brief.get("mood", "")
        genre = brief.get("genre", "")
        tracks = await self.db_fetch(
            "SELECT t.id, t.title, a.name FROM tracks t LEFT JOIN artists a ON t.artist_id = a.id WHERE t.genre = $1 LIMIT 10",
            genre,
        )
        return {"brief": brief, "matching_tracks": tracks}

    async def _catalog_search(self, task: AgentTask) -> dict:
        query = task.payload.get("query", "")
        bpm_min = task.payload.get("bpm_min")
        bpm_max = task.payload.get("bpm_max")
        params = [query]
        q = "SELECT id, title, bpm, key, genre FROM tracks WHERE title ILIKE $1"
        if bpm_min:
            q += " AND bpm >= $2"
            params.append(bpm_min)
        if bpm_max:
            q += f" AND bpm <= ${len(params)+1}"
            params.append(bpm_max)
        tracks = await self.db_fetch(q + " LIMIT 20", *params)
        return {"query": query, "results": tracks}

    async def _report_sync_revenue(self, task: AgentTask) -> dict:
        revenue = await self.db_fetchrow(
            "SELECT COALESCE(SUM(net_amount), 0) as total FROM royalties WHERE source = 'sync'"
        )
        return {"sync_revenue_total": float(revenue["total"]) if revenue else 0.0}
