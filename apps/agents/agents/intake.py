"""
Intake Agent
First point of contact for all demo submissions.
Scores, categorizes, and routes inbound demos through the pipeline.
"""

import logging
import uuid
from datetime import datetime, timezone

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Scoring weights
SCORE_WEIGHTS = {
    "audio_quality": 0.25,
    "platform_presence": 0.20,
    "growth_velocity": 0.20,
    "engagement_rate": 0.15,
    "content_consistency": 0.10,
    "genre_fit": 0.10,
}

# Category thresholds
CATEGORY_PRIORITY = 75   # → forward to A&R
CATEGORY_WATCHLIST = 60  # → re-check monthly
CATEGORY_FILE = 40       # → store, no action
# < 40 → PASS

LABEL_GENRES = {"r&b", "hip-hop", "pop", "electronic", "indie"}

RESPONSE_TEMPLATES = {
    "PRIORITY": (
        "Hey {name}! We've been listening to your music and we're really feeling it. "
        "We'd love to talk more about what we can build together. "
        "Are you available for a conversation this week?"
    ),
    "WATCHLIST": (
        "Thanks for sending your music, {name}. We're digging what you're building. "
        "Keep dropping heat and we'll be in touch when the timing is right. 🎵"
    ),
    "FILE": (
        "Appreciate you sharing your music, {name}. "
        "It's not quite the right fit for us right now, but feel free to submit again anytime."
    ),
    "PASS": (
        "Thanks for reaching out, {name}. We've listened to your submission and while it's not "
        "the direction we're heading right now, we encourage you to keep developing your sound."
    ),
}


def _score_from_data(data: dict) -> dict:
    """
    Rule-based scoring from submission data.
    Returns individual dimension scores (0-100) and weighted total.
    """
    # Audio quality (25%) — infer from file signals
    audio = 50.0
    if data.get("audio_url"):
        audio += 20.0
    if data.get("soundcloud_url"):
        audio += 10.0
    if data.get("ai_detected"):
        audio -= 30.0
    audio = max(0.0, min(100.0, audio))

    # Platform presence (20%) — follower / stream signals
    presence = 40.0
    if data.get("spotify_url"):
        presence += 15.0
    if data.get("monthly_listeners", 0) > 10000:
        presence += 15.0
    elif data.get("monthly_listeners", 0) > 1000:
        presence += 8.0
    if data.get("instagram_url"):
        presence += 10.0
    if data.get("tiktok_url"):
        presence += 10.0
    if data.get("youtube_url"):
        presence += 5.0
    presence = max(0.0, min(100.0, presence))

    # Growth velocity (20%) — MoM growth %
    growth = 50.0
    growth_pct = data.get("growth_pct_monthly", 0)
    if growth_pct >= 50:
        growth = 90.0
    elif growth_pct >= 20:
        growth = 75.0
    elif growth_pct >= 10:
        growth = 65.0
    elif growth_pct < 0:
        growth = 30.0

    # Engagement rate (15%)
    engagement = 50.0
    eng_rate = data.get("engagement_rate", 0)
    if eng_rate >= 0.08:
        engagement = 90.0
    elif eng_rate >= 0.04:
        engagement = 70.0
    elif eng_rate >= 0.02:
        engagement = 55.0
    elif eng_rate > 0:
        engagement = 40.0

    # Content consistency (10%) — releases in last 12 months
    consistency = 50.0
    releases_12m = data.get("releases_last_12m", 0)
    if releases_12m >= 6:
        consistency = 90.0
    elif releases_12m >= 3:
        consistency = 75.0
    elif releases_12m >= 1:
        consistency = 60.0
    else:
        consistency = 30.0

    # Genre fit (10%) — match to label focus
    genre = (data.get("genre") or "").lower().strip()
    genre_fit = 75.0 if any(g in genre for g in LABEL_GENRES) else 40.0

    scores = {
        "audio_quality": round(audio, 1),
        "platform_presence": round(presence, 1),
        "growth_velocity": round(growth, 1),
        "engagement_rate": round(engagement, 1),
        "content_consistency": round(consistency, 1),
        "genre_fit": round(genre_fit, 1),
    }

    total = round(sum(scores[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS), 1)
    scores["total"] = total
    return scores


def _categorize(score: float) -> str:
    if score >= CATEGORY_PRIORITY:
        return "PRIORITY"
    elif score >= CATEGORY_WATCHLIST:
        return "WATCHLIST"
    elif score >= CATEGORY_FILE:
        return "FILE"
    return "PASS"


def _build_response(category: str, name: str) -> str:
    template = RESPONSE_TEMPLATES.get(category, RESPONSE_TEMPLATES["PASS"])
    return template.format(name=name or "there")


class IntakeAgent(BaseAgent):
    agent_id = "intake"
    agent_name = "Intake Agent"
    subscriptions = ["submission.new"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "process_submission": self._process_submission,
            "send_response": self._send_response,
            "update_watchlist": self._update_watchlist,
            "get_submission_stats": self._get_submission_stats,
            # Legacy
            "check_duplicate": self._check_duplicate,
            "validate_submission": self._validate_submission,
            "route_to_ar": self._route_to_ar,
            "submission_stats": self._get_submission_stats,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    # ----------------------------------------------------------------
    # process_submission
    # ----------------------------------------------------------------

    async def _process_submission(self, task: AgentTask) -> dict:
        payload = task.payload
        submission_id = payload.get("submission_id")

        # If submission_id provided, load from DB; otherwise, create new record
        if submission_id:
            submission = await self.db_fetchrow(
                "SELECT * FROM submissions WHERE id = $1::uuid", submission_id
            )
            if not submission:
                return {"error": f"Submission {submission_id} not found"}
            data = dict(submission)
        else:
            # Deduplicate by email (within 30 days)
            email = payload.get("email", "")
            duplicate = False
            if email:
                existing = await self.db_fetchrow(
                    "SELECT id FROM submissions WHERE email = $1 AND created_at > NOW() - INTERVAL '30 days'",
                    email,
                )
                duplicate = existing is not None

            submission_id = str(uuid.uuid4())
            await self.db_execute(
                """
                INSERT INTO submissions (id, channel, artist_name, email, phone, genre,
                  spotify_url, soundcloud_url, audio_url, instagram_url, tiktok_url,
                  referral_code, duplicate)
                VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                submission_id,
                payload.get("channel", "web"),
                payload.get("artist_name"),
                email,
                payload.get("phone"),
                payload.get("genre"),
                payload.get("spotify_url"),
                payload.get("soundcloud_url"),
                payload.get("audio_url"),
                payload.get("instagram_url"),
                payload.get("tiktok_url"),
                payload.get("referral_code"),
                duplicate,
            )

            if duplicate:
                logger.info(f"[Intake] Duplicate submission: {email}")
                return {"submission_id": submission_id, "duplicate": True, "action": "skipped"}

            data = payload
            data["id"] = submission_id

        # Score the submission
        scores = _score_from_data(data)
        total = scores["total"]
        category = _categorize(total)
        artist_name = data.get("artist_name", "")

        # Map category to legacy DB values
        db_category = {
            "PRIORITY": "hot",
            "WATCHLIST": "warm",
            "FILE": "cold",
            "PASS": "cold",
        }.get(category, "cold")
        ar_decision = "interested" if category == "PRIORITY" else "pass"

        await self.db_execute(
            """UPDATE submissions
               SET total_score = $2, category = $3, ar_decision = $4, response_sent_at = NOW()
               WHERE id = $1::uuid""",
            submission_id,
            total,
            db_category,
            ar_decision,
        )

        response_text = _build_response(category, artist_name)

        # Route based on category
        if category == "PRIORITY":
            # Forward to A&R agent
            await self.send_message("ar", "score_submission", {"submission_id": submission_id})
            logger.info(f"[Intake] PRIORITY: {artist_name} (score={total}) → A&R")

        elif category == "WATCHLIST":
            logger.info(f"[Intake] WATCHLIST: {artist_name} (score={total})")

        elif category == "FILE":
            logger.info(f"[Intake] FILE: {artist_name} (score={total})")

        else:  # PASS
            logger.info(f"[Intake] PASS: {artist_name} (score={total})")

        # Log the response
        await self.log_audit("intake_processed", "submissions", submission_id, {
            "category": category,
            "score": total,
            "artist_name": artist_name,
        })

        return {
            "submission_id": submission_id,
            "artist_name": artist_name,
            "score": total,
            "scores": scores,
            "category": category,
            "action": ar_decision,
            "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text,
        }

    # ----------------------------------------------------------------
    # send_response
    # ----------------------------------------------------------------

    async def _send_response(self, task: AgentTask) -> dict:
        submission_id = task.payload.get("submission_id")
        category = task.payload.get("category")
        name = task.payload.get("name") or task.payload.get("artist_name", "")
        email = task.payload.get("email", "")

        if submission_id and not category:
            sub = await self.db_fetchrow(
                "SELECT artist_name, email, category FROM submissions WHERE id = $1::uuid", submission_id
            )
            if sub:
                name = name or sub.get("artist_name", "")
                email = email or sub.get("email", "")
                db_cat = sub.get("category", "cold")
                category = {"hot": "PRIORITY", "warm": "WATCHLIST", "cold": "FILE"}.get(db_cat, "PASS")

        response_text = _build_response(category or "PASS", name)

        # Delegate actual sending to Comms agent
        await self.send_message("comms", "send_email", {
            "to_email": email,
            "to_name": name,
            "subject": "Your ECHO Demo Submission",
            "body": response_text,
            "category": category,
            "submission_id": submission_id,
        })

        if submission_id:
            await self.db_execute(
                "UPDATE submissions SET response_sent_at = NOW() WHERE id = $1::uuid",
                submission_id,
            )

        return {
            "submission_id": submission_id,
            "category": category,
            "response_sent": True,
            "channel": "email",
            "response_preview": response_text,
        }

    # ----------------------------------------------------------------
    # update_watchlist
    # ----------------------------------------------------------------

    async def _update_watchlist(self, task: AgentTask) -> dict:
        """Re-score all watchlist (warm) submissions monthly."""
        watchlist = await self.db_fetch(
            "SELECT * FROM submissions WHERE category = 'warm' ORDER BY created_at DESC LIMIT 100"
        )

        promoted = []
        updated = 0

        for sub in watchlist:
            data = dict(sub)
            scores = _score_from_data(data)
            total = scores["total"]
            new_category = _categorize(total)
            db_category = {"PRIORITY": "hot", "WATCHLIST": "warm", "FILE": "cold", "PASS": "cold"}.get(new_category, "cold")

            await self.db_execute(
                "UPDATE submissions SET total_score = $2, category = $3, updated_at = NOW() WHERE id = $1::uuid",
                str(sub["id"]),
                total,
                db_category,
            )
            updated += 1

            if new_category == "PRIORITY":
                await self.send_message("ar", "score_submission", {"submission_id": str(sub["id"])})
                promoted.append({"submission_id": str(sub["id"]), "artist_name": sub.get("artist_name"), "score": total})
                logger.info(f"[Intake] Watchlist → PRIORITY: {sub.get('artist_name')} (score={total})")

        return {
            "watchlist_checked": len(watchlist),
            "updated": updated,
            "promoted_to_priority": len(promoted),
            "promoted": promoted,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # get_submission_stats
    # ----------------------------------------------------------------

    async def _get_submission_stats(self, task: AgentTask) -> dict:
        stats = await self.db_fetchrow(
            """
            SELECT
              COUNT(*) as total,
              COUNT(*) FILTER (WHERE category = 'hot') as priority,
              COUNT(*) FILTER (WHERE category = 'warm') as watchlist,
              COUNT(*) FILTER (WHERE category = 'cold') as filed,
              COUNT(*) FILTER (WHERE ar_decision = 'pass') as passed,
              COUNT(*) FILTER (WHERE duplicate = TRUE) as duplicates,
              COUNT(*) FILTER (WHERE response_sent_at IS NOT NULL) as responses_sent,
              ROUND(AVG(total_score)::numeric, 1) as avg_score,
              COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as last_7_days,
              COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as last_30_days
            FROM submissions
            """
        )
        return dict(stats) if stats else {}

    # ----------------------------------------------------------------
    # Legacy / compat handlers
    # ----------------------------------------------------------------

    async def _check_duplicate(self, task: AgentTask) -> dict:
        email = task.payload.get("email", "")
        existing = await self.db_fetchrow("SELECT id FROM submissions WHERE email = $1", email)
        return {"email": email, "is_duplicate": existing is not None}

    async def _validate_submission(self, task: AgentTask) -> dict:
        p = task.payload
        errors = []
        if not p.get("artist_name"):
            errors.append("artist_name required")
        if not p.get("email") and not p.get("phone"):
            errors.append("email or phone required")
        if not p.get("audio_url") and not p.get("spotify_url"):
            errors.append("audio_url or spotify_url required")
        return {"valid": len(errors) == 0, "errors": errors}

    async def _route_to_ar(self, task: AgentTask) -> dict:
        submission_id = task.payload.get("submission_id")
        await self.send_message("ar", "score_submission", {"submission_id": submission_id})
        return {"submission_id": submission_id, "routed_to": "ar"}

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Intake] Online — processing demo submissions")
