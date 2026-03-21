"""
ECHO Comms Agent
Single point of contact between ECHO and all artists.
Manages WhatsApp/Telegram comms, approvals, sentiment analysis, and escalations.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone

from anthropic import AsyncAnthropic
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Quiet hours (local time) — no non-urgent messages
QUIET_HOUR_START = 23  # 11 PM
QUIET_HOUR_END = 8     # 8 AM

# Max non-urgent messages per artist per day
MAX_DAILY_NON_URGENT = 3

# Tone examples by artist communication style
TONE_EXAMPLES = {
    "casual": {
        "milestone": "Yo! {message} 🔥",
        "update": "{message}",
        "approval": "Got {item} ready — sending it over, let me know which one hits 👀",
        "feedback": "Quick q for you — {question}",
    },
    "formal": {
        "milestone": "Exciting update: {message}",
        "update": "Update from ECHO: {message}",
        "approval": "We have {item} ready for your review. Please let us know your preference.",
        "feedback": "We'd appreciate your feedback: {question}",
    },
}

MILESTONE_MESSAGES = {
    "100k_streams": "Your track just hit 100K streams 🔥 That's {speed_note}",
    "1m_streams": "1 MILLION streams. That's not luck — that's a real fanbase.",
    "first_sync": "First sync placement locked in. Your music is in {placement}.",
    "first_press": "First press feature just went live — {outlet} covered you.",
    "release_live": "'{title}' is LIVE on all platforms. Let's gooo 🚀",
    "playlist_added": "You just got added to '{playlist}' on Spotify 👀",
}


class CommsAgent(BaseAgent):
    agent_id = "comms"
    agent_name = "Communications Agent"
    subscriptions = [
        "artist.signed",
        "release.completed",
        "alert.churn_risk",
        "agent.comms",
    ]

    def __init__(self):
        super().__init__()
        self.claude = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Comms] Online. Artist communication hub active.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "send_artist_update": self._send_artist_update,
            "request_approval": self._request_approval,
            "onboard_artist": self._onboard_artist,
            "send_milestone_celebration": self._send_milestone_celebration,
            "collect_feedback": self._collect_feedback,
            "check_sentiment": self._check_sentiment,
            "escalate_issue": self._escalate_issue,
            "tone_calibrate": self._task_tone_calibrate,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        payload = message.get("payload", {})
        if topic == "artist.signed":
            artist_id = payload.get("artist_id")
            if artist_id:
                await self.send_message("comms", "onboard_artist", {"artist_id": artist_id})
        elif topic == "release.completed":
            artist_id = payload.get("artist_id")
            release_id = payload.get("release_id")
            if artist_id:
                await self.send_message("comms", "send_milestone_celebration", {
                    "artist_id": artist_id,
                    "release_id": release_id,
                    "event": "release_live",
                })

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _send_artist_update(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        message_text = task.payload.get("message", "")
        context_type = task.payload.get("context_type", "update")
        context_id = task.payload.get("context_id")
        urgent = task.payload.get("urgent", False)
        channel = task.payload.get("channel", "whatsapp")

        artist = await self.db_fetchrow(
            "SELECT name, preferred_name, comm_style FROM artists WHERE id = $1::uuid", artist_id
        )

        artist_name = ""
        comm_style = "casual"
        if artist:
            artist_name = artist.get("preferred_name") or artist.get("name") or ""
            comm_style = artist.get("comm_style") or "casual"

        # Check daily message limit (non-urgent)
        if not urgent:
            daily_count = await self._get_daily_message_count(artist_id)
            if daily_count >= MAX_DAILY_NON_URGENT:
                logger.warning(f"[Comms] Daily limit reached for artist {artist_id} — message queued")
                return {
                    "artist_id": artist_id,
                    "status": "queued",
                    "reason": f"Daily limit of {MAX_DAILY_NON_URGENT} non-urgent messages reached",
                }

        # Format message in correct tone
        formatted = self._format_message(message_text, comm_style, context_type)

        # Log to communications table
        comm_id = str(uuid.uuid4())
        await self.db_execute(
            """
            INSERT INTO communications (id, artist_id, channel, direction, content, context_type, context_id)
            VALUES ($1::uuid, $2::uuid, $3, 'outbound', $4, $5, $6::uuid)
            """,
            comm_id, artist_id, channel, formatted, context_type,
            context_id if context_id else None,
        )

        logger.info(f"[Comms] Sent {context_type} to {artist_name or artist_id} via {channel}")
        return {
            "comm_id": comm_id,
            "artist_id": artist_id,
            "artist_name": artist_name,
            "channel": channel,
            "message": formatted,
            "context_type": context_type,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
        }

    async def _request_approval(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        item_type = task.payload.get("item_type", "deliverable")  # artwork, mix, release_date, contract
        options = task.payload.get("options", [])
        context_id = task.payload.get("context_id")
        deadline = task.payload.get("deadline", "")

        artist = await self.db_fetchrow("SELECT name, preferred_name, comm_style FROM artists WHERE id = $1::uuid", artist_id)
        artist_name = ""
        comm_style = "casual"
        if artist:
            artist_name = artist.get("preferred_name") or artist.get("name") or ""
            comm_style = artist.get("comm_style") or "casual"

        options_text = ""
        if options:
            options_text = "\n" + "\n".join([f"Option {i+1}: {o}" for i, o in enumerate(options)])

        if comm_style == "casual":
            message = f"Got {item_type} ready for you{options_text}\nLet me know which one works best 👀"
        else:
            message = f"We have the {item_type} ready for your review.{options_text}\nPlease indicate your preference."

        if deadline:
            message += f"\nDeadline: {deadline}"

        result = await self._send_artist_update(AgentTask(
            task_id=task.task_id,
            task_type="send_artist_update",
            payload={
                "artist_id": artist_id,
                "message": message,
                "context_type": "approval_request",
                "context_id": context_id,
                "urgent": True,
            },
        ))

        return {**result, "item_type": item_type, "options_count": len(options)}

    async def _onboard_artist(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist_name = task.payload.get("artist_name", "")

        artist = await self.db_fetchrow("SELECT name, preferred_name FROM artists WHERE id = $1::uuid", artist_id)
        if artist:
            artist_name = artist.get("preferred_name") or artist.get("name") or artist_name

        welcome_message = (
            f"Hey {artist_name}! Welcome to ECHO 🎵\n\n"
            f"I'm your dedicated comms link — this is where everything happens:\n"
            f"✅ Artwork approvals\n"
            f"✅ Release updates\n"
            f"✅ Royalty statements\n"
            f"✅ Any questions\n\n"
            f"You've got 21 AI agents working for you around the clock. "
            f"Let's build something 🔥\n\n"
            f"First up — your brand kit and roadmap are being put together right now."
        )

        comm_id = str(uuid.uuid4())
        await self.db_execute(
            """
            INSERT INTO communications (id, artist_id, channel, direction, content, context_type)
            VALUES ($1::uuid, $2::uuid, 'whatsapp', 'outbound', $3, 'onboarding')
            """,
            comm_id, artist_id, welcome_message,
        )

        logger.info(f"[Comms] Onboarding message sent to {artist_name}")
        return {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "message_sent": welcome_message,
            "channel": "whatsapp",
            "status": "onboarding_started",
        }

    async def _send_milestone_celebration(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        event = task.payload.get("event", "milestone")
        artist_name = task.payload.get("artist_name", "")
        custom_message = task.payload.get("message", "")

        artist = await self.db_fetchrow("SELECT name, preferred_name, comm_style FROM artists WHERE id = $1::uuid", artist_id)
        comm_style = "casual"
        if artist:
            artist_name = artist.get("preferred_name") or artist.get("name") or artist_name
            comm_style = artist.get("comm_style") or "casual"

        template = MILESTONE_MESSAGES.get(event, "🎉 Big milestone reached! {message}")
        message = template.format(
            message=custom_message,
            speed_note="faster than your last release",
            placement="a streaming series",
            outlet="a major music blog",
            title=task.payload.get("title", "your latest track"),
            playlist=task.payload.get("playlist", "a Spotify editorial playlist"),
        )

        if comm_style == "casual":
            message = f"Yo {artist_name}! {message}"
        else:
            message = f"{artist_name}, {message}"

        result = await self._send_artist_update(AgentTask(
            task_id=task.task_id,
            task_type="send_artist_update",
            payload={
                "artist_id": artist_id,
                "message": message,
                "context_type": "milestone",
                "urgent": False,
            },
        ))
        return {**result, "event": event}

    async def _collect_feedback(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        subject = task.payload.get("subject", "recent deliverable")
        question = task.payload.get("question", f"How are you feeling about the {subject}?")
        options = task.payload.get("options", ["Loving it", "Minor tweaks needed", "Need a redo"])

        artist = await self.db_fetchrow("SELECT name, preferred_name, comm_style FROM artists WHERE id = $1::uuid", artist_id)
        comm_style = "casual"
        if artist:
            comm_style = artist.get("comm_style") or "casual"

        if comm_style == "casual":
            message = f"Quick one — {question}\n" + "\n".join([f"{i+1}️⃣ {o}" for i, o in enumerate(options)])
        else:
            message = f"We'd appreciate your feedback on {subject}. {question}\n" + "\n".join([f"Option {i+1}: {o}" for i, o in enumerate(options)])

        result = await self._send_artist_update(AgentTask(
            task_id=task.task_id,
            task_type="send_artist_update",
            payload={
                "artist_id": artist_id,
                "message": message,
                "context_type": "feedback_request",
                "urgent": False,
            },
        ))
        return {**result, "subject": subject, "options": options}

    async def _check_sentiment(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        days = task.payload.get("days", 30)

        recent = await self.db_fetch(
            """
            SELECT content, direction, created_at
            FROM communications
            WHERE artist_id = $1::uuid AND created_at > NOW() - ($2 || ' days')::INTERVAL
            ORDER BY created_at DESC LIMIT 30
            """,
            artist_id, str(days),
        )

        if not recent:
            return {"artist_id": artist_id, "sentiment_score": 50, "message_count": 0, "note": "No recent messages"}

        inbound = [m for m in recent if m.get("direction") == "inbound"]
        outbound = [m for m in recent if m.get("direction") == "outbound"]

        score = 50  # Neutral baseline
        signals = []

        # Response ratio — artist responding to outbound is positive
        if outbound and len(inbound) / max(len(outbound), 1) >= 0.7:
            score += 15
            signals.append("Good response rate")
        elif outbound and len(inbound) / max(len(outbound), 1) < 0.3:
            score -= 20
            signals.append("Low response rate")

        if self.claude and inbound:
            try:
                sample_messages = [m["content"][:200] for m in inbound[:10]]
                msg = await self.claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=200,
                    system="Analyze artist messages for sentiment. Return JSON only.",
                    messages=[{"role": "user", "content": (
                        f"Analyze these artist messages and return sentiment score 0-100 "
                        f"(0=very unhappy, 50=neutral, 100=very happy) + key signals.\n"
                        f"Messages: {json.dumps(sample_messages)}\n"
                        f"Return JSON: {{\"score\": int, \"signals\": [str]}}"
                    )}],
                )
                text = msg.content[0].text.strip()
                start, end = text.find("{"), text.rfind("}") + 1
                if start >= 0 and end > start:
                    analysis = json.loads(text[start:end])
                    ai_score = analysis.get("score", score)
                    # Blend base score with AI analysis
                    score = int((score + ai_score) / 2)
                    signals += analysis.get("signals", [])
            except Exception as e:
                logger.error(f"[Comms] Claude sentiment error: {e}")

        score = max(0, min(100, score))
        sentiment_label = "positive" if score >= 70 else ("neutral" if score >= 40 else "negative")

        # Update sentiment in DB
        if inbound:
            await self.db_execute(
                """
                UPDATE communications SET sentiment_score = $2
                WHERE artist_id = $1::uuid AND direction = 'inbound'
                AND created_at = (SELECT MAX(created_at) FROM communications WHERE artist_id = $1::uuid AND direction = 'inbound')
                """,
                artist_id, score / 100,
            )

        return {
            "artist_id": artist_id,
            "sentiment_score": score,
            "sentiment_label": sentiment_label,
            "message_count": len(recent),
            "inbound_count": len(inbound),
            "outbound_count": len(outbound),
            "signals": signals,
            "period_days": days,
        }

    async def _escalate_issue(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        issue = task.payload.get("issue", "Unspecified issue")
        severity = task.payload.get("severity", "medium")
        churn_score = task.payload.get("churn_score")
        signals = task.payload.get("signals", [])

        artist = await self.db_fetchrow("SELECT name FROM artists WHERE id = $1::uuid", artist_id)
        artist_name = artist["name"] if artist else str(artist_id)

        # Route based on severity
        escalation_routes = {
            "critical": ["ceo", "artist_dev"],
            "high": ["ceo", "artist_dev"],
            "medium": ["artist_dev"],
            "low": ["artist_dev"],
        }
        routes = escalation_routes.get(severity, ["artist_dev"])

        for target_agent in routes:
            await self.send_message(target_agent, "alert.issue", {
                "artist_id": artist_id,
                "artist_name": artist_name,
                "issue": issue,
                "severity": severity,
                "churn_score": churn_score,
                "signals": signals,
                "escalated_by": self.agent_id,
                "escalated_at": datetime.now(timezone.utc).isoformat(),
            })

        await self.log_audit("escalate_issue", "artists", artist_id, {
            "issue": issue,
            "severity": severity,
            "routes": routes,
        })
        logger.info(f"[Comms] Issue escalated for {artist_name}: '{issue}' ({severity}) → {routes}")

        return {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "issue": issue,
            "severity": severity,
            "escalated_to": routes,
            "escalated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # Hero Skills
    # ----------------------------------------------------------------

    async def _task_tone_calibrate(self, task: AgentTask) -> dict:
        """Tone Calibrator — builds a communication tone profile for an artist."""
        artist_id = task.payload.get("artist_id") or task.artist_id
        sample_messages = task.payload.get("sample_messages", [])
        communication_context = task.payload.get("communication_context", "general")

        artist = await self.db_fetchrow(
            "SELECT name, genre, bio, comm_style FROM artists WHERE id = $1::uuid", artist_id
        )
        if not artist:
            return {"error": "Artist not found"}

        artist_name = artist["name"]
        genre = (artist.get("genre") or "pop").lower()
        existing_comm_style = artist.get("comm_style") or "casual"

        # Genre-based communication defaults
        _genre_tone_map = {
            "hip-hop": {"formality": 2, "energy": 9, "verbosity": 4, "emoji_usage": "frequent"},
            "trap": {"formality": 2, "energy": 9, "verbosity": 3, "emoji_usage": "frequent"},
            "classical": {"formality": 9, "energy": 2, "verbosity": 7, "emoji_usage": "none"},
            "jazz": {"formality": 8, "energy": 3, "verbosity": 6, "emoji_usage": "none"},
            "pop": {"formality": 5, "energy": 6, "verbosity": 5, "emoji_usage": "moderate"},
            "rock": {"formality": 3, "energy": 7, "verbosity": 4, "emoji_usage": "minimal"},
            "electronic": {"formality": 4, "energy": 6, "verbosity": 5, "emoji_usage": "minimal"},
            "r&b": {"formality": 4, "energy": 6, "verbosity": 6, "emoji_usage": "moderate"},
            "indie": {"formality": 3, "energy": 5, "verbosity": 7, "emoji_usage": "minimal"},
            "country": {"formality": 5, "energy": 5, "verbosity": 6, "emoji_usage": "minimal"},
        }
        tone = next(
            (v for k, v in _genre_tone_map.items() if k in genre or genre in k),
            {"formality": 5, "energy": 5, "verbosity": 5, "emoji_usage": "moderate"},
        ).copy()

        # Refine with sample messages if provided
        if sample_messages and self.claude:
            try:
                sample_text = "\n".join(str(m)[:200] for m in sample_messages[:5])
                msg = await self.claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=200,
                    system="Analyze communication style. Return JSON only.",
                    messages=[{"role": "user", "content": (
                        f"Analyze these messages from a {genre} artist named {artist_name}:\n{sample_text}\n\n"
                        f"Return JSON: {{\"formality\": int(1-10), \"energy\": int(1-10), "
                        f"\"verbosity\": int(1-10), \"emoji_usage\": \"none|minimal|moderate|frequent\"}}"
                    )}],
                )
                text = msg.content[0].text.strip()
                start, end = text.find("{"), text.rfind("}") + 1
                if start >= 0 and end > start:
                    analyzed = json.loads(text[start:end])
                    tone = {
                        "formality": (tone["formality"] + int(analyzed.get("formality", tone["formality"]))) // 2,
                        "energy": (tone["energy"] + int(analyzed.get("energy", tone["energy"]))) // 2,
                        "verbosity": (tone["verbosity"] + int(analyzed.get("verbosity", tone["verbosity"]))) // 2,
                        "emoji_usage": analyzed.get("emoji_usage", tone["emoji_usage"]),
                    }
            except Exception as e:
                logger.error(f"[Comms] Claude tone analysis error: {e}")

        tone_profile = {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "genre": genre,
            "communication_context": communication_context,
            **tone,
        }

        formality = tone["formality"]
        energy = tone["energy"]
        emoji_str = {"none": "", "minimal": " 🙌", "moderate": " 🔥✨", "frequent": " 🔥🎵💯"}.get(
            tone["emoji_usage"], ""
        )

        # Generate sample messages in artist voice
        sample_greeting = sample_update = sample_milestone = ""
        if self.claude:
            try:
                tone_desc = (
                    f"Formality: {formality}/10, Energy: {energy}/10, "
                    f"Verbosity: {tone['verbosity']}/10, Emoji: {tone['emoji_usage']}"
                )
                msg = await self.claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=400,
                    system="Write in the exact voice and style of a music artist. Match their tone precisely.",
                    messages=[{"role": "user", "content": (
                        f"Write 3 short messages for {artist_name} ({genre} artist). Tone: {tone_desc}\n"
                        f"1. A greeting introducing themselves to their label\n"
                        f"2. A project update (just finished a track)\n"
                        f"3. A milestone celebration (100k streams)\n"
                        f"Return JSON: {{\"greeting\": str, \"update\": str, \"milestone\": str}}"
                    )}],
                )
                text = msg.content[0].text.strip()
                start, end = text.find("{"), text.rfind("}") + 1
                if start >= 0 and end > start:
                    samples = json.loads(text[start:end])
                    sample_greeting = samples.get("greeting", "")
                    sample_update = samples.get("update", "")
                    sample_milestone = samples.get("milestone", "")
            except Exception as e:
                logger.error(f"[Comms] Claude sample messages error: {e}")

        if not sample_greeting:
            if formality <= 3:
                sample_greeting = f"yo what's good{emoji_str}, it's {artist_name} — let's get it{emoji_str}"
                sample_update = f"just wrapped a new one in the lab, hard asf{emoji_str}"
                sample_milestone = f"100k already?? y'all wild fr{emoji_str}"
            elif formality >= 7:
                sample_greeting = f"Hello, I'm {artist_name}. Looking forward to working together."
                sample_update = f"I've completed a new recording and would appreciate your feedback when available."
                sample_milestone = f"Grateful to have reached 100,000 streams. Thank you for your support."
            else:
                sample_greeting = f"Hey! I'm {artist_name} — excited to be here{emoji_str}"
                sample_update = f"Just finished a new track — feeling good about this one{emoji_str}"
                sample_milestone = f"100K streams!! Thank you so much{emoji_str}"

        # Persist updated comm_style if it changed
        comm_style_label = "formal" if formality >= 7 else "casual"
        if existing_comm_style != comm_style_label:
            await self.db_execute(
                "UPDATE artists SET comm_style = $2 WHERE id = $1::uuid",
                artist_id, comm_style_label,
            )

        logger.info(f"[Comms] Tone calibrated for {artist_name}: formality={formality}, energy={energy}")
        return {
            "tone_profile": tone_profile,
            "sample_greeting": sample_greeting,
            "sample_update": sample_update,
            "sample_milestone": sample_milestone,
            "comm_style": comm_style_label,
            "hero_skill": "tone_calibrator",
        }

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _format_message(self, text: str, comm_style: str, context_type: str) -> str:
        tone = TONE_EXAMPLES.get(comm_style, TONE_EXAMPLES["casual"])
        template = tone.get(context_type, "{message}")
        try:
            return template.format(message=text, item=text, question=text)
        except (KeyError, IndexError):
            return text

    async def _get_daily_message_count(self, artist_id: str) -> int:
        row = await self.db_fetchrow(
            """
            SELECT COUNT(*) AS cnt FROM communications
            WHERE artist_id = $1::uuid AND direction = 'outbound'
            AND created_at > CURRENT_DATE::TIMESTAMPTZ
            """,
            artist_id,
        )
        return int(row["cnt"]) if row else 0
