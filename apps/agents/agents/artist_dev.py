"""
Artist Development Agent
Manages 12-month career roadmaps, coordinates release pipelines,
monitors artist wellness/churn risk, and handles full onboarding.
"""

import json
import logging
import uuid
from datetime import datetime, date, timedelta, timezone

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Churn risk score thresholds
CHURN_ALERT_CEO = 60
CHURN_ALERT_BOTH = 80

# Release checklist milestones (weeks before release day = 0)
RELEASE_CHECKLIST = [
    {"week": -6, "milestone": "Master delivered", "owner": "production", "critical": True},
    {"week": -6, "milestone": "Artwork finalized", "owner": "creative", "critical": True},
    {"week": -6, "milestone": "Metadata prepared (ISRC, UPC, credits)", "owner": "distribution", "critical": True},
    {"week": -4, "milestone": "Uploaded to distributor", "owner": "distribution", "critical": True},
    {"week": -4, "milestone": "Playlist pitch submitted", "owner": "marketing", "critical": False},
    {"week": -4, "milestone": "Pre-save page live", "owner": "marketing", "critical": False},
    {"week": -2, "milestone": "Teasers posted to social", "owner": "social", "critical": False},
    {"week": -2, "milestone": "Pre-save ad campaign running", "owner": "marketing", "critical": False},
    {"week": -2, "milestone": "Press outreach started", "owner": "pr", "critical": False},
    {"week": 0, "milestone": "Verify live on all platforms", "owner": "distribution", "critical": True},
    {"week": 0, "milestone": "Full ad campaign activated", "owner": "marketing", "critical": True},
    {"week": 0, "milestone": "Release day social blitz", "owner": "social", "critical": True},
    {"week": 0, "milestone": "Email blast sent", "owner": "comms", "critical": False},
]

ROADMAP_QUARTERS = {
    "Q1": {
        "focus": "Foundation & First Release",
        "goals": [
            "Complete brand kit and visual identity",
            "Record and master debut single",
            "Build social media presence (1K+ followers)",
            "Release debut single",
        ],
        "agents": ["creative", "production", "marketing", "social"],
    },
    "Q2": {
        "focus": "Momentum Building",
        "goals": [
            "Release second single",
            "Sync licensing pitch — 3 catalogs submitted",
            "Grow streaming to 10K monthly listeners",
            "First press coverage secured",
        ],
        "agents": ["marketing", "social", "sync", "pr"],
    },
    "Q3": {
        "focus": "Scale & EP Release",
        "goals": [
            "Release 4-6 track EP",
            "Hit 50K monthly listeners",
            "Merch launch",
            "Feature collaboration with roster artist",
        ],
        "agents": ["production", "marketing", "social", "merch", "artist_dev"],
    },
    "Q4": {
        "focus": "Year-End Push & Plan Next Year",
        "goals": [
            "Year-end editorial pitches",
            "100K monthly listener target",
            "Plan full album for next year",
            "Royalty review and reinvestment",
        ],
        "agents": ["marketing", "social", "finance", "analytics", "ceo"],
    },
}


class ArtistDevAgent(BaseAgent):
    agent_id = "artist_dev"
    agent_name = "Artist Development Agent"
    subscriptions = ["artist.signed", "release.completed", "alert.churn_risk"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[ArtistDev] Online. Career management system active.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "create_roadmap": self._create_roadmap,
            "plan_release": self._plan_release,
            "check_artist_health": self._check_artist_health,
            "find_collaborations": self._find_collaborations,
            "onboard_artist": self._onboard_artist,
            "generate_career_milestone": self._generate_career_milestone,
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
                await self.send_message("artist_dev", "onboard_artist", {"artist_id": artist_id})
        elif topic == "release.completed":
            release_id = payload.get("release_id")
            artist_id = payload.get("artist_id")
            if artist_id:
                await self.send_message("artist_dev", "generate_career_milestone", {
                    "artist_id": artist_id,
                    "release_id": release_id,
                    "event": "release_completed",
                })

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _create_roadmap(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow(
            "SELECT name, genre, echo_score FROM artists WHERE id = $1::uuid", artist_id
        )
        if not artist:
            return {"error": "Artist not found", "artist_id": artist_id}

        artist_name = artist["name"]
        start_date = date.today()

        roadmap = {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=365)).isoformat(),
            "quarters": {},
        }

        for quarter, data in ROADMAP_QUARTERS.items():
            q_num = int(quarter[1])
            q_start = start_date + timedelta(days=(q_num - 1) * 91)
            roadmap["quarters"][quarter] = {
                **data,
                "start_date": q_start.isoformat(),
                "end_date": (q_start + timedelta(days=90)).isoformat(),
                "status": "planned",
            }

        await self.log_audit("create_roadmap", "artists", artist_id, {"quarters": 4})
        logger.info(f"[ArtistDev] 12-month roadmap created for {artist_name}")
        return roadmap

    async def _plan_release(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        artist_id = task.payload.get("artist_id") or task.artist_id

        release = await self.db_fetchrow(
            "SELECT r.title, r.release_date, a.name FROM releases r "
            "LEFT JOIN artists a ON r.artist_id = a.id WHERE r.id = $1::uuid",
            release_id,
        )
        if not release:
            return {"error": "Release not found", "release_id": release_id}

        release_date = release.get("release_date") or date.today() + timedelta(weeks=6)
        if isinstance(release_date, str):
            release_date = date.fromisoformat(release_date)

        checklist = []
        for item in RELEASE_CHECKLIST:
            due_date = release_date + timedelta(weeks=item["week"])
            checklist.append({
                **item,
                "due_date": due_date.isoformat(),
                "status": "pending",
            })

        # Coordinate agents
        delegations = [
            ("creative", "generate_artwork", {"release_id": release_id}),
            ("marketing", "create_campaign", {"release_id": release_id}),
            ("pr", "write_press_release", {"release_id": release_id}),
            ("social", "create_content_calendar", {"release_id": release_id}),
            ("distribution", "prepare_distribution", {"release_id": release_id}),
        ]
        for agent_id, task_type, payload in delegations:
            await self.send_message(agent_id, task_type, {**payload, "release_id": release_id})

        logger.info(f"[ArtistDev] Release plan created for '{release['title']}' — {len(checklist)} checklist items")
        return {
            "release_id": release_id,
            "release_title": release["title"],
            "artist": release["name"],
            "release_date": release_date.isoformat(),
            "checklist": checklist,
            "agents_notified": [a for a, _, _ in delegations],
        }

    async def _check_artist_health(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow(
            "SELECT name, status, created_at FROM artists WHERE id = $1::uuid", artist_id
        )
        if not artist:
            return {"error": "Artist not found", "artist_id": artist_id}

        # Pull signals from communications + tasks
        recent_comms = await self.db_fetch(
            """
            SELECT created_at, direction FROM communications
            WHERE artist_id = $1::uuid AND created_at > NOW() - INTERVAL '30 days'
            ORDER BY created_at DESC LIMIT 20
            """,
            artist_id,
        )

        recent_tasks = await self.db_fetch(
            """
            SELECT status, created_at FROM agent_tasks
            WHERE artist_id = $1::uuid AND created_at > NOW() - INTERVAL '30 days'
            ORDER BY created_at DESC LIMIT 20
            """,
            artist_id,
        )

        churn_score = 0
        signals = []

        # Signal: low comms activity
        if len(recent_comms) < 3:
            churn_score += 20
            signals.append("Low communication activity in last 30 days")

        # Signal: missing tasks / failed tasks
        failed = sum(1 for t in recent_tasks if t["status"] == "failed")
        if failed > 2:
            churn_score += 15
            signals.append(f"{failed} failed tasks in last 30 days")

        # Signal: no recent inbound comms
        inbound = [c for c in recent_comms if c.get("direction") == "inbound"]
        if len(inbound) == 0:
            churn_score += 25
            signals.append("No inbound messages from artist in 30 days")

        churn_score = min(churn_score, 100)
        risk_level = "low" if churn_score < 40 else ("medium" if churn_score < CHURN_ALERT_CEO else "high")

        if churn_score >= CHURN_ALERT_BOTH:
            await self.send_message("ceo", "alert.churn_risk", {
                "artist_id": artist_id,
                "artist_name": artist["name"],
                "churn_score": churn_score,
                "signals": signals,
            })
            await self.send_message("comms", "escalate_issue", {
                "artist_id": artist_id,
                "issue": "High churn risk detected",
                "churn_score": churn_score,
                "signals": signals,
            })
        elif churn_score >= CHURN_ALERT_CEO:
            await self.send_message("ceo", "alert.churn_risk", {
                "artist_id": artist_id,
                "artist_name": artist["name"],
                "churn_score": churn_score,
                "signals": signals,
            })

        logger.info(f"[ArtistDev] Health check for {artist['name']}: score={churn_score} ({risk_level})")
        return {
            "artist_id": artist_id,
            "artist_name": artist["name"],
            "churn_risk_score": churn_score,
            "risk_level": risk_level,
            "signals": signals,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _find_collaborations(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow(
            "SELECT name, genre, echo_score FROM artists WHERE id = $1::uuid", artist_id
        )
        if not artist:
            return {"error": "Artist not found"}

        # Find roster artists in same/adjacent genre
        roster = await self.db_fetch(
            """
            SELECT id, name, genre, echo_score
            FROM artists
            WHERE status = 'signed' AND id != $1::uuid
            ORDER BY echo_score DESC
            LIMIT 10
            """,
            artist_id,
        )

        same_genre = [a for a in roster if a.get("genre", "").lower() == (artist.get("genre") or "").lower()]
        cross_genre = [a for a in roster if a not in same_genre]

        collab_suggestions = []
        for collab in same_genre[:3]:
            collab_suggestions.append({
                "artist_id": str(collab["id"]),
                "name": collab["name"],
                "genre": collab["genre"],
                "type": "same_genre_feature",
                "rationale": f"Similar genre match — natural audience crossover",
            })
        for collab in cross_genre[:2]:
            collab_suggestions.append({
                "artist_id": str(collab["id"]),
                "name": collab["name"],
                "genre": collab["genre"],
                "type": "cross_genre_experiment",
                "rationale": f"Cross-genre experiment — expands reach to new audiences",
            })

        return {
            "artist_id": artist_id,
            "artist_name": artist["name"],
            "roster_size": len(roster),
            "collaboration_suggestions": collab_suggestions,
        }

    async def _onboard_artist(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow("SELECT name, genre FROM artists WHERE id = $1::uuid", artist_id)
        if not artist:
            return {"error": "Artist not found", "artist_id": artist_id}

        artist_name = artist["name"]

        # Kick off all onboarding tasks in parallel
        onboarding_steps = [
            ("comms", "onboard_artist", {"artist_id": artist_id, "artist_name": artist_name}),
            ("creative", "create_brand_kit", {"artist_id": artist_id, "genre": artist.get("genre")}),
            ("artist_dev", "create_roadmap", {"artist_id": artist_id}),
            ("legal", "review_contracts", {"artist_id": artist_id}),
        ]

        for agent, task_type, payload in onboarding_steps:
            await self.send_message(agent, task_type, payload)

        await self.log_audit("onboard_artist", "artists", artist_id, {"steps": len(onboarding_steps)})
        logger.info(f"[ArtistDev] Onboarding initiated for {artist_name}")
        return {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "onboarding_steps": [{"agent": a, "task": t} for a, t, _ in onboarding_steps],
            "status": "onboarding_started",
        }

    async def _generate_career_milestone(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        event = task.payload.get("event", "milestone")
        release_id = task.payload.get("release_id")
        streams = task.payload.get("streams")
        custom_note = task.payload.get("note", "")

        artist = await self.db_fetchrow("SELECT name FROM artists WHERE id = $1::uuid", artist_id)
        artist_name = artist["name"] if artist else "Artist"

        milestone_messages = {
            "release_completed": f"🎉 {artist_name} — Release is live! First 48 hours are critical. Watch the numbers.",
            "100k_streams": f"💯 {artist_name} just crossed 100K streams! Big milestone.",
            "1m_streams": f"🔥 {artist_name} — 1 MILLION streams. That's a real moment.",
            "first_sync": f"🎬 {artist_name}'s first sync placement secured. Revenue diversification begins.",
            "first_press": f"📰 First press feature live for {artist_name}. Momentum building.",
        }

        message = milestone_messages.get(event, f"🌟 Milestone reached: {event} — {artist_name}")
        if custom_note:
            message += f" {custom_note}"

        await self.send_message("comms", "send_milestone_celebration", {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "event": event,
            "message": message,
            "release_id": release_id,
        })

        await self.log_audit("career_milestone", "artists", artist_id, {"event": event})
        return {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "event": event,
            "milestone_message": message,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
