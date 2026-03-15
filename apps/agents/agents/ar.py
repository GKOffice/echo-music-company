"""
A&R Agent
Discovers talent, scores submissions, manages the signing pipeline,
and monitors the artist roster.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class ARAgent(BaseAgent):
    agent_id = "ar"
    agent_name = "A&R Agent"
    subscriptions = ["submission.received", "artist.prospect"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "score_submission": self._score_submission,
            "review_artist": self._review_artist,
            "sign_artist": self._sign_artist,
            "reject_submission": self._reject_submission,
            "pipeline_update": self._pipeline_update,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _score_submission(self, task: AgentTask) -> dict:
        submission_id = task.payload.get("submission_id")
        if not submission_id:
            return {"error": "submission_id required"}

        submission = await self.db_fetchrow(
            "SELECT * FROM submissions WHERE id = $1::uuid", submission_id
        )
        if not submission:
            return {"error": "Submission not found"}

        score = self._calculate_score(submission)
        category = "hot" if score >= 80 else "warm" if score >= 60 else "cold"

        await self.db_execute(
            "UPDATE submissions SET total_score = $2, category = $3, response_sent_at = NOW() WHERE id = $1::uuid",
            submission_id,
            score,
            category,
        )

        if score >= 75:
            await self.send_message("comms", "send_response", {
                "submission_id": submission_id,
                "category": "interested",
                "email": submission["email"],
            })

        return {"submission_id": submission_id, "score": score, "category": category}

    def _calculate_score(self, submission: dict) -> float:
        score = 50.0
        if submission.get("spotify_url"):
            score += 10
        if submission.get("soundcloud_url"):
            score += 5
        if submission.get("instagram_url"):
            score += 5
        if submission.get("audio_url"):
            score += 15
        if submission.get("ai_detected"):
            score -= 30
        if submission.get("already_signed"):
            score -= 50
        return max(0.0, min(100.0, score))

    async def _review_artist(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow("SELECT * FROM artists WHERE id = $1::uuid", artist_id)
        if not artist:
            return {"error": "Artist not found"}
        return {"artist_id": artist_id, "status": artist["status"], "echo_score": float(artist.get("echo_score", 0))}

    async def _sign_artist(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id")
        deal_type = task.payload.get("deal_type", "single")
        await self.db_execute(
            "UPDATE artists SET status = 'signed', deal_type = $2, updated_at = NOW() WHERE id = $1::uuid",
            artist_id,
            deal_type,
        )
        await self.send_message("legal", "draft_contract", {"artist_id": artist_id, "deal_type": deal_type})
        await self.broadcast("artist.signed", {"artist_id": artist_id, "deal_type": deal_type})
        await self.log_audit("sign_artist", "artists", artist_id)
        return {"artist_id": artist_id, "status": "signed", "deal_type": deal_type}

    async def _reject_submission(self, task: AgentTask) -> dict:
        submission_id = task.payload.get("submission_id")
        await self.db_execute(
            "UPDATE submissions SET ar_decision = 'pass', response_sent_at = NOW() WHERE id = $1::uuid",
            submission_id,
        )
        return {"submission_id": submission_id, "decision": "pass"}

    async def _pipeline_update(self, task: AgentTask) -> dict:
        prospects = await self.db_fetch(
            "SELECT id, name, echo_score, status FROM artists WHERE status IN ('prospect','reviewing') ORDER BY echo_score DESC LIMIT 20"
        )
        return {"pipeline": prospects, "count": len(prospects)}
