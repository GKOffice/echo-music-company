"""
Creative Agent
Manages artwork creation, visual identity, brand guidelines,
and creative assets for all releases.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class CreativeAgent(BaseAgent):
    agent_id = "creative"
    agent_name = "Creative Agent"
    subscriptions = ["release.created", "artist.signed"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "artwork_review": self._artwork_review,
            "generate_artwork_brief": self._generate_artwork_brief,
            "approve_artwork": self._approve_artwork,
            "brand_audit": self._brand_audit,
            "visual_assets": self._create_visual_assets,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _artwork_review(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow("SELECT artwork_url, title FROM releases WHERE id = $1::uuid", release_id)
        if not release:
            return {"error": "Release not found"}
        if not release.get("artwork_url"):
            return {"release_id": release_id, "approved": False, "reason": "No artwork uploaded"}
        return {"release_id": release_id, "approved": True, "artwork_url": release["artwork_url"]}

    async def _generate_artwork_brief(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        genre = task.payload.get("genre", "")
        return {
            "release_id": release_id,
            "brief": {
                "style": "dark, minimalist",
                "colors": ["#0a0a0f", "#8b5cf6", "#10b981"],
                "dimensions": "3000x3000px",
                "format": "JPEG/PNG",
                "genre": genre,
            },
        }

    async def _approve_artwork(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        artwork_url = task.payload.get("artwork_url")
        await self.db_execute(
            "UPDATE releases SET artwork_url = $2, updated_at = NOW() WHERE id = $1::uuid",
            release_id, artwork_url,
        )
        await self.log_audit("approve_artwork", "releases", release_id)
        return {"release_id": release_id, "artwork_approved": True}

    async def _brand_audit(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow("SELECT name, profile_photo_url, brand_guidelines_url FROM artists WHERE id = $1::uuid", artist_id)
        issues = []
        if not artist or not artist.get("profile_photo_url"):
            issues.append("Missing profile photo")
        if not artist or not artist.get("brand_guidelines_url"):
            issues.append("Missing brand guidelines")
        return {"artist_id": artist_id, "brand_issues": issues, "audit_passed": len(issues) == 0}

    async def _create_visual_assets(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        return {
            "release_id": release_id,
            "assets_created": ["instagram_square", "instagram_story", "twitter_header", "youtube_thumbnail"],
            "status": "pending_upload",
        }
