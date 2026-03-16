"""
ECHO A&R Agent — Talent Scout & Signing Pipeline
Discovers talent, scores submissions, manages the signing pipeline,
sends recommendations to CEO, and monitors the artist roster.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from anthropic import AsyncAnthropic
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """You are the A&R (Artists & Repertoire) agent at ECHO, an autonomous AI music company.

Your role:
- Discover and evaluate emerging music talent
- Score artist submissions across multiple dimensions
- Build signing recommendations for the CEO
- Monitor the artist development pipeline

Scoring dimensions (0-100 each):
1. music_quality — production value, originality, commercial appeal
2. social_presence — follower counts, engagement rates, growth trajectory
3. commercial_potential — streaming numbers, live history, sync potential
4. genre_fit — alignment with ECHO's roster and market strategy
5. brand_strength — visual identity, narrative, marketability

Total = music×0.35 + social×0.20 + commercial×0.25 + genre×0.10 + brand×0.10
Score ≥ 75 triggers a signing recommendation to the CEO.

Be analytical and data-driven. No hype."""


class ARAgent(BaseAgent):
    agent_id = "ar"
    agent_name = "A&R Agent"
    subscriptions = ["submission.received", "artist.prospect", "ar.reject_signing"]

    def __init__(self):
        super().__init__()
        self.claude = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

    async def on_start(self):
        logger.info("[A&R] Online — scanning talent pipeline")
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "score_submission": self._score_submission,
            "scan_submissions": self._scan_submissions,
            "review_artist": self._review_artist,
            "sign_artist": self._sign_artist,
            "reject_signing": self._reject_signing,
            "reject_submission": self._reject_submission,
            "pipeline_update": self._pipeline_update,
            "recommend_signing": self._recommend_signing,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        payload = message.get("payload", {})

        if topic == "submission.received":
            submission_id = payload.get("submission_id")
            if submission_id:
                logger.info(f"[A&R] New submission: {submission_id}")
                fake_task = AgentTask(
                    task_id=f"auto_{submission_id}",
                    task_type="score_submission",
                    payload={"submission_id": submission_id},
                )
                await self._score_submission(fake_task)

        elif topic == "ar.reject_signing":
            artist_id = payload.get("artist_id")
            reason = payload.get("reason", "")
            if artist_id:
                await self.db_execute(
                    "UPDATE artists SET status = 'rejected', updated_at = NOW() WHERE id = $1::uuid",
                    artist_id,
                )
                logger.info(f"[A&R] Signing rejected for {artist_id}: {reason}")

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _score_submission(self, task: AgentTask) -> dict:
        submission_id = task.payload.get("submission_id")
        if not submission_id:
            return {"error": "submission_id required"}

        submission = await self.db_fetchrow(
            "SELECT * FROM submissions WHERE id = $1::uuid", submission_id
        )
        if not submission:
            return {"error": "Submission not found"}

        if self.claude:
            scores = await self._claude_score(submission)
        else:
            scores = self._rule_based_score(submission)

        total = scores["total"]
        category = "hot" if total >= 80 else "warm" if total >= 60 else "cold"
        ar_decision = "interested" if total >= 75 else "pass"

        await self.db_execute(
            """UPDATE submissions
               SET total_score = $2, category = $3, ar_decision = $4, response_sent_at = NOW()
               WHERE id = $1::uuid""",
            submission_id,
            total,
            category,
            ar_decision,
        )

        if ar_decision == "interested":
            await self.send_message("comms", "send_response", {
                "submission_id": submission_id,
                "category": "interested",
                "email": submission.get("email", ""),
                "name": submission.get("artist_name", ""),
            })
            artist_id = await self._upsert_prospect(submission, total)
            if artist_id and total >= 80:
                await self._send_signing_recommendation(artist_id, dict(submission), scores)

        return {
            "submission_id": submission_id,
            "score": total,
            "scores": scores,
            "category": category,
            "decision": ar_decision,
        }

    async def _scan_submissions(self, task: AgentTask) -> dict:
        """Batch score all pending (unscored) submissions."""
        pending = await self.db_fetch(
            "SELECT id FROM submissions WHERE total_score IS NULL ORDER BY created_at ASC LIMIT 50"
        )
        scored = 0
        errors = 0
        for row in pending:
            try:
                sub_task = AgentTask(
                    task_id=f"scan_{row['id']}",
                    task_type="score_submission",
                    payload={"submission_id": str(row["id"])},
                )
                await self._score_submission(sub_task)
                scored += 1
            except Exception as e:
                logger.error(f"[A&R] Error scoring {row['id']}: {e}")
                errors += 1

        return {"scanned": len(pending), "scored": scored, "errors": errors}

    async def _review_artist(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow("SELECT * FROM artists WHERE id = $1::uuid", artist_id)
        if not artist:
            return {"error": "Artist not found"}

        result = {
            "artist_id": artist_id,
            "name": artist.get("name"),
            "status": artist.get("status"),
            "echo_score": float(artist.get("echo_score") or 0),
            "genre": artist.get("genre"),
        }

        if self.claude and artist.get("status") in ("prospect", "reviewing"):
            result["ai_analysis"] = await self._claude_artist_analysis(dict(artist))

        return result

    async def _sign_artist(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id")
        deal_type = task.payload.get("deal_type", "single")
        if not artist_id:
            return {"error": "artist_id required"}

        await self.db_execute(
            "UPDATE artists SET status = 'signed', deal_type = $2, updated_at = NOW() WHERE id = $1::uuid",
            artist_id,
            deal_type,
        )
        await self.send_message("legal", "draft_contract", {"artist_id": artist_id, "deal_type": deal_type})
        await self.broadcast("artist.signed", {"artist_id": artist_id, "deal_type": deal_type})
        await self.log_audit("sign_artist", "artists", artist_id)
        logger.info(f"[A&R] Artist signed: {artist_id} ({deal_type})")
        return {"artist_id": artist_id, "status": "signed", "deal_type": deal_type}

    async def _reject_signing(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id")
        reason = task.payload.get("reason", "")
        if artist_id:
            await self.db_execute(
                "UPDATE artists SET status = 'rejected', updated_at = NOW() WHERE id = $1::uuid",
                artist_id,
            )
        return {"artist_id": artist_id, "status": "rejected", "reason": reason}

    async def _reject_submission(self, task: AgentTask) -> dict:
        submission_id = task.payload.get("submission_id")
        await self.db_execute(
            "UPDATE submissions SET ar_decision = 'pass', response_sent_at = NOW() WHERE id = $1::uuid",
            submission_id,
        )
        return {"submission_id": submission_id, "decision": "pass"}

    async def _pipeline_update(self, task: AgentTask) -> dict:
        prospects = await self.db_fetch(
            """SELECT id, name, echo_score, status, genre
               FROM artists
               WHERE status IN ('prospect','reviewing')
               ORDER BY echo_score DESC LIMIT 20"""
        )
        hot = [p for p in prospects if (p.get("echo_score") or 0) >= 80]
        return {
            "pipeline": [dict(p) for p in prospects],
            "count": len(prospects),
            "hot_prospects": len(hot),
        }

    async def _recommend_signing(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        if not artist_id:
            return {"error": "artist_id required"}

        artist = await self.db_fetchrow("SELECT * FROM artists WHERE id = $1::uuid", artist_id)
        if not artist:
            return {"error": "Artist not found"}

        score = float(artist.get("echo_score") or 0)
        await self._send_signing_recommendation(artist_id, dict(artist), {"total": score})
        return {"artist_id": artist_id, "recommendation_sent": True}

    # ----------------------------------------------------------------
    # Scoring
    # ----------------------------------------------------------------

    def _rule_based_score(self, submission: dict) -> dict:
        music = 50.0
        social = 50.0
        commercial = 50.0

        if submission.get("audio_url"):
            music += 20
        if submission.get("spotify_url"):
            social += 15
            commercial += 10
        if submission.get("soundcloud_url"):
            social += 8
        if submission.get("instagram_url"):
            social += 7
        if submission.get("ai_detected"):
            music -= 30
        if submission.get("already_signed"):
            commercial -= 50

        music = max(0.0, min(100.0, music))
        social = max(0.0, min(100.0, social))
        commercial = max(0.0, min(100.0, commercial))
        genre_fit = 60.0
        brand = 55.0

        total = (
            music * 0.35 + social * 0.20 + commercial * 0.25 + genre_fit * 0.10 + brand * 0.10
        )
        return {
            "music_quality": round(music, 1),
            "social_presence": round(social, 1),
            "commercial_potential": round(commercial, 1),
            "genre_fit": round(genre_fit, 1),
            "brand_strength": round(brand, 1),
            "total": round(total, 1),
        }

    async def _claude_score(self, submission: dict) -> dict:
        data = {
            "artist_name": submission.get("artist_name", ""),
            "genre": submission.get("genre", ""),
            "notes": submission.get("notes", ""),
            "has_spotify": bool(submission.get("spotify_url")),
            "has_soundcloud": bool(submission.get("soundcloud_url")),
            "has_instagram": bool(submission.get("instagram_url")),
            "has_tiktok": bool(submission.get("tiktok_url")),
            "has_audio": bool(submission.get("audio_url")),
            "ai_detected": bool(submission.get("ai_detected")),
            "already_signed": bool(submission.get("already_signed")),
        }
        prompt = (
            f"Score this artist submission for ECHO Records:\n{json.dumps(data, indent=2)}\n\n"
            f"Score each dimension 0-100. Return JSON only:\n"
            f'{{\n  "music_quality": float,\n  "social_presence": float,\n'
            f'  "commercial_potential": float,\n  "genre_fit": float,\n'
            f'  "brand_strength": float,\n  "total": float,\n  "summary": str\n}}\n\n'
            f"total = music×0.35 + social×0.20 + commercial×0.25 + genre×0.10 + brand×0.10"
        )
        try:
            response = await self.claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                scores = json.loads(text[start:end])
                # Recompute total from individual scores to prevent drift
                weights = {
                    "music_quality": 0.35,
                    "social_presence": 0.20,
                    "commercial_potential": 0.25,
                    "genre_fit": 0.10,
                    "brand_strength": 0.10,
                }
                scores["total"] = round(sum(scores.get(k, 0) * w for k, w in weights.items()), 1)
                return scores
        except Exception as e:
            logger.error(f"[A&R] Claude scoring error: {e}")
        return self._rule_based_score(submission)

    async def _claude_artist_analysis(self, artist: dict) -> dict:
        safe = {k: v for k, v in artist.items() if k not in ("id", "user_id")}
        prompt = (
            f"Analyze this artist prospect for potential signing:\n{json.dumps(safe, indent=2)}\n\n"
            f"Return JSON: {{\"strengths\": list, \"weaknesses\": list, "
            f"\"recommendation\": str, \"deal_type\": str}}"
        )
        try:
            response = await self.claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception as e:
            logger.error(f"[A&R] Claude analysis error: {e}")
        return {}

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    async def _upsert_prospect(self, submission: dict, score: float) -> Optional[str]:
        """Create or update an artist record from a submission."""
        try:
            existing = await self.db_fetchrow(
                "SELECT id FROM artists WHERE name = $1",
                submission.get("artist_name", ""),
            )
            if existing:
                artist_id = str(existing["id"])
                await self.db_execute(
                    "UPDATE artists SET echo_score = $2, status = 'reviewing', updated_at = NOW() WHERE id = $1::uuid",
                    artist_id,
                    score,
                )
            else:
                row = await self.db_fetchrow(
                    """INSERT INTO artists (name, genre, echo_score, status)
                       VALUES ($1, $2, $3, 'prospect')
                       RETURNING id""",
                    submission.get("artist_name", "Unknown"),
                    submission.get("genre", ""),
                    score,
                )
                artist_id = str(row["id"]) if row else None
            return artist_id
        except Exception as e:
            logger.error(f"[A&R] Upsert prospect error: {e}")
            return None

    async def _send_signing_recommendation(
        self, artist_id: str, artist_data: dict, scores: dict
    ):
        total = scores.get("total", 0)
        deal_type = "album" if total >= 90 else "ep" if total >= 80 else "single"
        await self.broadcast("signing.recommendation", {
            "artist_id": artist_id,
            "artist": {
                "name": artist_data.get("name") or artist_data.get("artist_name", ""),
                "score": total,
                "scores": scores,
                "genre": artist_data.get("genre", ""),
            },
            "recommended_deal": deal_type,
            "from_agent": self.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"[A&R] Signing recommendation → CEO: artist {artist_id} (score={total})")


if __name__ == "__main__":
    import asyncio
    from bus import bus

    async def main():
        await bus.connect()
        agent = ARAgent()
        await agent.start()

    asyncio.run(main())
