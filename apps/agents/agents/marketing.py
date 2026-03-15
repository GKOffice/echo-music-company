"""
Marketing Agent
Plans and executes marketing campaigns, manages ad spend,
coordinates playlist pitching, and tracks campaign performance.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class MarketingAgent(BaseAgent):
    agent_id = "marketing"
    agent_name = "Marketing Agent"
    subscriptions = ["release.distributed", "artist.signed"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "plan_campaign": self._plan_campaign,
            "pitch_playlists": self._pitch_playlists,
            "run_ads": self._run_ads,
            "report_performance": self._report_performance,
            "press_release": self._create_press_release,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _plan_campaign(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow("SELECT * FROM releases WHERE id = $1::uuid", release_id)
        if not release:
            return {"error": "Release not found"}
        priority = release.get("priority", "standard")
        budget = {"priority": 5000, "standard": 2000, "low": 500}.get(priority, 2000)
        campaign = {
            "release_id": release_id,
            "budget_usd": budget,
            "channels": ["spotify_editorial", "instagram", "tiktok", "youtube"],
            "timeline_days": 30,
            "strategy": "release_week_push",
        }
        await self.send_message("social", "create_content_calendar", {"release_id": release_id, "campaign": campaign})
        return campaign

    async def _pitch_playlists(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        genre = task.payload.get("genre", "")
        playlists_pitched = ["RapCaviar", "New Music Friday", "Lorem", "Fresh Finds"]
        logger.info(f"[Marketing] Pitching {release_id} to {len(playlists_pitched)} playlists")
        return {"release_id": release_id, "playlists_pitched": playlists_pitched}

    async def _run_ads(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        budget = task.payload.get("budget_usd", 1000)
        platforms = task.payload.get("platforms", ["instagram", "tiktok"])
        logger.info(f"[Marketing] Running ads for {release_id}: ${budget} across {platforms}")
        return {"release_id": release_id, "budget": budget, "platforms": platforms, "status": "ads_live"}

    async def _report_performance(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow("SELECT streams_total, revenue_total FROM releases WHERE id = $1::uuid", release_id)
        return {"release_id": release_id, "streams": dict(release) if release else {}}

    async def _create_press_release(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow(
            "SELECT r.title, a.name FROM releases r LEFT JOIN artists a ON r.artist_id = a.id WHERE r.id = $1::uuid",
            release_id,
        )
        if not release:
            return {"error": "Release not found"}
        return {
            "release_id": release_id,
            "press_release_draft": f"{release['name']} drops new release '{release['title']}' via ECHO",
            "status": "draft",
        }
