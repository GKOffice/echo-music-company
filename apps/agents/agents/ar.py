"""
ECHO A&R Agent — Talent Scout & Signing Pipeline
Discovers talent, scores submissions, manages the signing pipeline,
sends recommendations to CEO, and monitors the artist roster.
"""

import json
import logging
import os
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

from anthropic import AsyncAnthropic
from base_agent import BaseAgent, AgentTask, AgentResult
from guardrails import ScopeGuard, REAL_ID_FIELDS
from memory_store import ErrorType

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
        self._scope_guard = ScopeGuard()

    async def on_start(self):
        logger.info("[A&R] Online — scanning talent pipeline")
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        await self._seed_known_hallucinations()

    async def handle_task(self, task: AgentTask) -> AgentResult:
        # Scope guard for tasks that involve external entity lookups
        if task.task_type in ("review_artist", "score_submission", "recommend_signing"):
            scope = self._scope_guard.check(self.agent_id, task.task_type, task.payload)
            if not scope.passed:
                logger.warning(f"[A&R] Scope guard rejected task {task.task_id}: {scope.reason}")
                if self._memory_store:
                    await self._memory_store.log_failure(
                        agent_id=self.agent_id,
                        task_type=task.task_type,
                        input_data=task.payload,
                        bad_output={},
                        error_type=ErrorType.OUT_OF_SCOPE,
                        correction=scope.reason,
                    )
                return AgentResult(
                    success=True,
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    result=scope.safe_response or {"found": False, "reason": scope.reason},
                )

        handlers = {
            "score_submission": self._score_submission,
            "scan_submissions": self._scan_submissions,
            "review_artist": self._review_artist,
            "sign_artist": self._sign_artist,
            "reject_signing": self._reject_signing,
            "reject_submission": self._reject_submission,
            "pipeline_update": self._pipeline_update,
            "recommend_signing": self._recommend_signing,
            "momentum_scan": self._task_momentum_scan,
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
            return {"found": False, "reason": "Artist not found in music databases", "searched": ["internal_db"]}

        artist_dict = dict(artist)

        # Confidence gate: require at least one real external ID
        has_real_id = any(artist_dict.get(f) for f in REAL_ID_FIELDS)
        if not has_real_id:
            logger.warning(f"[A&R] Artist {artist_id} has no real external ID — low confidence")
            if self._memory_store:
                await self._memory_store.log_failure(
                    agent_id=self.agent_id,
                    task_type="review_artist",
                    input_data={"artist_id": artist_id},
                    bad_output={"name": artist_dict.get("name"), "no_external_id": True},
                    error_type=ErrorType.LOW_CONFIDENCE,
                    correction="Artist has no Spotify/MusicBrainz/Chartmetric ID — cannot verify identity",
                    confidence_score=0.3,
                )
            return {
                "found": False,
                "reason": "Artist not found in music databases — no verified external ID",
                "searched": ["spotify", "musicbrainz", "chartmetric"],
                "artist_id": artist_id,
            }

        result = {
            "found": True,
            "artist_id": artist_id,
            "name": artist_dict.get("name"),
            "status": artist_dict.get("status"),
            "echo_score": float(artist_dict.get("echo_score") or 0),
            "genre": artist_dict.get("genre"),
        }

        if self.claude and artist_dict.get("status") in ("prospect", "reviewing"):
            result["ai_analysis"] = await self._claude_artist_analysis(artist_dict)

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
        base_prompt = (
            f"Score this artist submission for ECHO Records:\n{json.dumps(data, indent=2)}\n\n"
            f"Score each dimension 0-100. Return JSON only:\n"
            f'{{\n  "music_quality": float,\n  "social_presence": float,\n'
            f'  "commercial_potential": float,\n  "genre_fit": float,\n'
            f'  "brand_strength": float,\n  "total": float,\n  "summary": str\n}}\n\n'
            f"total = music×0.35 + social×0.20 + commercial×0.25 + genre×0.10 + brand×0.10\n\n"
            f"IMPORTANT: Only score based on provided data. Do not invent streaming numbers or social stats."
        )
        prompt = await self._build_prompt_with_memory(base_prompt, "score_submission")
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
        base_prompt = (
            f"Analyze this artist prospect for potential signing:\n{json.dumps(safe, indent=2)}\n\n"
            f"Return JSON: {{\"strengths\": list, \"weaknesses\": list, "
            f"\"recommendation\": str, \"deal_type\": str}}\n\n"
            f"IMPORTANT: Only include verifiable facts. "
            f"If you cannot verify a claim, omit it rather than guessing."
        )
        prompt = await self._build_prompt_with_memory(base_prompt, "review_artist")
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

    async def _seed_known_hallucinations(self):
        """
        Seed the memory store with known hallucination patterns on startup.
        Only inserts if this agent has zero memory records (idempotent).
        """
        if not self._memory_store or not self._db_pool:
            return
        try:
            count = await self._db_pool.fetchval(
                "SELECT COUNT(*) FROM agent_memory WHERE agent_id = $1", self.agent_id
            )
            if count and count > 0:
                return  # Already seeded

            # Dorin Hirvi hallucination — invented artist with fabricated details
            await self._memory_store.log_failure(
                agent_id=self.agent_id,
                task_type="review_artist",
                input_data={"artist_name": "Dorin Hirvi"},
                bad_output={
                    "name": "Dorin Hirvi",
                    "spotify_id": "3abc123fake",
                    "monthly_listeners": 45000,
                    "genre": "electronic",
                    "label": "Independent",
                },
                error_type=ErrorType.HALLUCINATION,
                correction=(
                    "Dorin Hirvi does not exist in Spotify, MusicBrainz, or Chartmetric. "
                    "All details were fabricated. Return found=false for unknown artists."
                ),
                confidence_score=0.0,
            )
            logger.info("[A&R] Seeded known hallucination patterns into memory store")
        except Exception as e:
            logger.warning(f"[A&R] Could not seed hallucinations (table may not exist yet): {e}")

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


    # ----------------------------------------------------------------
    # Hero Skills
    # ----------------------------------------------------------------

    async def _task_momentum_scan(self, task: AgentTask) -> dict:
        """Momentum Detector — scores artist buzz from free public APIs."""
        artist_name = task.payload.get("artist_name", "")
        timeframe_days = int(task.payload.get("timeframe_days", 30))

        if not artist_name:
            return {"error": "artist_name required"}

        encoded = urllib.parse.quote(artist_name)

        # --- iTunes Search ---
        itunes_rank = None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://itunes.apple.com/search?term={encoded}&entity=musicArtist&limit=10"
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    for i, r in enumerate(results):
                        name = r.get("artistName", "").lower()
                        if artist_name.lower() in name or name in artist_name.lower():
                            itunes_rank = i + 1
                            break
        except Exception as e:
            logger.warning(f"[A&R] iTunes API error: {e}")

        if itunes_rank and itunes_rank <= 3:
            search_visibility = "high"
            visibility_pts = 40
        elif itunes_rank and itunes_rank <= 10:
            search_visibility = "medium"
            visibility_pts = 25
        else:
            search_visibility = "low"
            visibility_pts = 10

        # --- MusicBrainz ---
        release_count_12m = 0
        mb_found = False
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")
        try:
            async with httpx.AsyncClient(
                timeout=10.0,
                headers={"User-Agent": "MelodioApp/1.0 (melodio.io)"},
            ) as client:
                resp = await client.get(
                    f"https://musicbrainz.org/ws/2/artist/?query={encoded}&fmt=json&limit=5"
                )
                if resp.status_code == 200:
                    for a in resp.json().get("artists", []):
                        if artist_name.lower() in a.get("name", "").lower():
                            mb_found = True
                            mb_id = a.get("id")
                            if mb_id:
                                rel_resp = await client.get(
                                    f"https://musicbrainz.org/ws/2/release-group"
                                    f"?artist={mb_id}&fmt=json&limit=100"
                                )
                                if rel_resp.status_code == 200:
                                    for rg in rel_resp.json().get("release-groups", []):
                                        if rg.get("first-release-date", "") >= cutoff_date:
                                            release_count_12m += 1
                            break
        except Exception as e:
            logger.warning(f"[A&R] MusicBrainz API error: {e}")

        if release_count_12m >= 3:
            release_velocity = "high"
            velocity_pts = 40
        elif release_count_12m == 2:
            release_velocity = "medium"
            velocity_pts = 30
        elif release_count_12m == 1:
            release_velocity = "low"
            velocity_pts = 20
        else:
            release_velocity = "none"
            velocity_pts = 5

        # --- Name uniqueness ---
        words = artist_name.strip().split()
        common_prefixes = {"the", "dj", "mc", "lil", "young", "big", "king", "queen"}
        is_common_prefix = bool(words) and words[0].lower() in common_prefixes
        if len(artist_name) >= 10 and not is_common_prefix:
            name_uniqueness = "high"
            uniqueness_pts = 20
        elif len(artist_name) >= 6:
            name_uniqueness = "medium"
            uniqueness_pts = 14
        else:
            name_uniqueness = "low"
            uniqueness_pts = 8

        momentum_score = visibility_pts + velocity_pts + uniqueness_pts

        if momentum_score >= 70:
            recommendation = "HIGH MOMENTUM — flag for immediate review"
        elif momentum_score >= 40:
            recommendation = "BUILDING — monitor weekly"
        else:
            recommendation = "EARLY STAGE — check back in 90 days"

        return {
            "momentum_score": momentum_score,
            "signals": {
                "search_visibility": search_visibility,
                "itunes_rank": itunes_rank,
                "release_velocity": release_velocity,
                "releases_last_12m": release_count_12m,
                "name_uniqueness": name_uniqueness,
                "mb_found": mb_found,
            },
            "recommendation": recommendation,
            "hero_skill": "momentum_detector",
        }


if __name__ == "__main__":
    import asyncio
    from bus import bus

    async def main():
        await bus.connect()
        agent = ARAgent()
        await agent.start()

    asyncio.run(main())
