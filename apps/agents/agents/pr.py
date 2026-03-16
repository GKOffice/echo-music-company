"""
PR Agent
Writes and distributes press releases, pitches to music journalists,
manages media contacts, and builds Electronic Press Kits.
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

# Media tier contacts
MEDIA_TIERS = {
    1: [
        {"outlet": "Pitchfork", "contact": "editorial@pitchfork.com", "lead_time_weeks": 6},
        {"outlet": "Rolling Stone", "contact": "music@rollingstone.com", "lead_time_weeks": 6},
        {"outlet": "Billboard", "contact": "tips@billboard.com", "lead_time_weeks": 4},
        {"outlet": "NME", "contact": "music@nme.com", "lead_time_weeks": 4},
    ],
    2: [
        {"outlet": "Complex", "contact": "music@complex.com", "lead_time_weeks": 3},
        {"outlet": "FADER", "contact": "submissions@thefader.com", "lead_time_weeks": 3},
        {"outlet": "Stereogum", "contact": "tips@stereogum.com", "lead_time_weeks": 2},
        {"outlet": "Pigeons & Planes", "contact": "tips@pigeonsandplanes.com", "lead_time_weeks": 2},
    ],
    3: [
        {"outlet": "SubmitHub", "contact": "via_platform", "lead_time_weeks": 1},
        {"outlet": "HipHopDX", "contact": "tips@hiphopdx.com", "lead_time_weeks": 2},
        {"outlet": "The Music", "contact": "news@themusic.com.au", "lead_time_weeks": 2},
        {"outlet": "Earmilk", "contact": "submit@earmilk.com", "lead_time_weeks": 1},
    ],
    4: [
        {"outlet": "YouTube Reactors", "contact": "direct_outreach", "lead_time_weeks": 1},
        {"outlet": "TikTok Reviewers", "contact": "direct_outreach", "lead_time_weeks": 1},
        {"outlet": "Reddit r/indieheads", "contact": "self_post", "lead_time_weeks": 0},
        {"outlet": "Reddit r/hiphopheads", "contact": "self_post", "lead_time_weeks": 0},
    ],
}

AWARD_OPPORTUNITIES = [
    {"name": "Grammy Awards", "category": "Best New Artist", "deadline_month": 9, "min_streams": 1_000_000},
    {"name": "BET Hip Hop Awards", "category": "Best New Hip Hop Artist", "deadline_month": 7, "genres": ["hip-hop"]},
    {"name": "MTV VMAs", "category": "Best New Artist", "deadline_month": 6, "min_streams": 500_000},
    {"name": "Spotify EQUAL", "category": "Equal Artist of the Month", "deadline_month": None, "rolling": True},
]

PRESS_RELEASE_TEMPLATE = """\
FOR IMMEDIATE RELEASE

{artist_name} RELEASES NEW {release_type} "{title}"
{hook}

{city}, {date} — {paragraph_1}

{paragraph_2}

"{artist_quote}"

{background}

LISTEN: {listen_link}
ABOUT {artist_name_upper}: {bio}
CONTACT: press@echo-music.com
"""


class PRAgent(BaseAgent):
    agent_id = "pr"
    agent_name = "PR Agent"
    subscriptions = ["release.distributed", "release.completed", "artist.signed"]

    def __init__(self):
        super().__init__()
        self.claude = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[PR] Online. Media relations engine active.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "write_press_release": self._write_press_release,
            "pitch_media": self._pitch_media,
            "build_epk": self._build_epk,
            "monitor_coverage": self._monitor_coverage,
            "submit_awards": self._submit_awards,
            # legacy
            "announce_release": self._write_press_release,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        payload = message.get("payload", {})
        if topic in ("release.distributed", "release.completed"):
            release_id = payload.get("release_id")
            if release_id:
                await self.send_message("pr", "write_press_release", {"release_id": release_id})
        elif topic == "artist.signed":
            artist_id = payload.get("artist_id")
            if artist_id:
                await self.send_message("pr", "build_epk", {"artist_id": artist_id})

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _write_press_release(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow(
            """
            SELECT r.title, r.release_type, r.release_date, r.genre,
                   a.name, a.bio, a.city
            FROM releases r LEFT JOIN artists a ON r.artist_id = a.id
            WHERE r.id = $1::uuid
            """,
            release_id,
        )
        if not release:
            return {"error": "Release not found", "release_id": release_id}

        artist_name = release["name"] or "Artist"
        title = release["title"] or "Untitled"
        release_type = (release.get("release_type") or "SINGLE").upper()
        city = release.get("city") or "Los Angeles"
        bio = release.get("bio") or f"{artist_name} is an independent artist on the ECHO label."
        genre = release.get("genre") or "music"
        release_date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

        if self.claude:
            try:
                prompt = (
                    f"Write a professional music press release for:\n"
                    f"Artist: {artist_name}\n"
                    f"Title: '{title}' ({release_type})\n"
                    f"Genre: {genre}\n"
                    f"City: {city}\n\n"
                    f"Write in the format:\n"
                    f"- One-line hook (compelling, journalistic)\n"
                    f"- Paragraph 1 (2-3 sentences introducing the release)\n"
                    f"- Paragraph 2 (context, sound, what makes it special)\n"
                    f"- Artist quote (authentic, first person)\n"
                    f"- Background paragraph (artist story)\n\n"
                    f"Return as JSON: {{\"hook\": str, \"p1\": str, \"p2\": str, \"quote\": str, \"background\": str}}"
                )
                msg = await self.claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=600,
                    system="You write compelling, professional music press releases. Avoid corporate jargon.",
                    messages=[{"role": "user", "content": prompt}],
                )
                text = msg.content[0].text.strip()
                start, end = text.find("{"), text.rfind("}") + 1
                content = json.loads(text[start:end]) if start >= 0 and end > start else {}
            except Exception as e:
                logger.error(f"[PR] Claude press release error: {e}")
                content = {}
        else:
            content = {}

        hook = content.get("hook", f"The {genre} artist returns with a bold new {release_type.lower()}.")
        p1 = content.get("p1", f"{artist_name} has released a new {release_type.lower()} titled '{title}' via ECHO.")
        p2 = content.get("p2", f"The track showcases {artist_name}'s evolving sound and artistry.")
        quote = content.get("quote", f"This one means a lot to me. Can't wait for everyone to hear it.")
        background = content.get("background", bio)

        press_release = PRESS_RELEASE_TEMPLATE.format(
            artist_name=artist_name,
            release_type=release_type,
            title=title,
            hook=hook,
            city=city,
            date=release_date_str,
            paragraph_1=p1,
            paragraph_2=p2,
            artist_quote=quote,
            background=background,
            listen_link="linktr.ee/echo",
            artist_name_upper=artist_name.upper(),
            bio=bio[:200],
        )

        await self.log_audit("write_press_release", "releases", release_id)
        logger.info(f"[PR] Press release written for '{title}' by {artist_name}")
        return {
            "release_id": release_id,
            "press_release": press_release,
            "word_count": len(press_release.split()),
            "status": "draft",
        }

    async def _pitch_media(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        tiers = task.payload.get("tiers", [1, 2, 3])

        release = await self.db_fetchrow(
            "SELECT r.title, a.name, a.genre FROM releases r LEFT JOIN artists a ON r.artist_id = a.id WHERE r.id = $1::uuid",
            release_id,
        )
        if not release:
            return {"error": "Release not found"}

        artist_name = release["name"]
        title = release["title"]
        genre = release.get("genre") or "music"

        pitches_sent = []
        for tier_num in tiers:
            outlets = MEDIA_TIERS.get(tier_num, [])
            for outlet in outlets:
                pitch = {
                    "tier": tier_num,
                    "outlet": outlet["outlet"],
                    "contact": outlet["contact"],
                    "subject": f"NEW {genre.upper()}: {artist_name} — '{title}'",
                    "body_preview": (
                        f"Hi, I'm reaching out about {artist_name}'s new release '{title}'. "
                        f"This {genre} track is available now via ECHO. "
                        f"Happy to send over the full EPK and streaming link."
                    ),
                    "lead_time_needed_weeks": outlet["lead_time_weeks"],
                    "status": "queued",
                }
                pitches_sent.append(pitch)

        logger.info(f"[PR] Media pitch queued: {len(pitches_sent)} outlets for '{title}' by {artist_name}")
        await self.log_audit("pitch_media", "releases", release_id, {"outlets": len(pitches_sent)})
        return {
            "release_id": release_id,
            "artist": artist_name,
            "title": title,
            "pitches_queued": len(pitches_sent),
            "pitches": pitches_sent,
        }

    async def _build_epk(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        release_id = task.payload.get("release_id") or task.release_id

        artist = await self.db_fetchrow(
            "SELECT name, bio, genre, city, profile_photo_url, social_links_json FROM artists WHERE id = $1::uuid",
            artist_id,
        )
        if not artist:
            return {"error": "Artist not found"}

        releases = await self.db_fetch(
            "SELECT title, release_type, release_date, streams_total FROM releases WHERE artist_id = $1::uuid ORDER BY release_date DESC LIMIT 5",
            artist_id,
        )

        social_links = artist.get("social_links_json") or {}

        epk = {
            "artist_id": artist_id,
            "artist_name": artist["name"],
            "genre": artist.get("genre"),
            "city": artist.get("city"),
            "bio": artist.get("bio") or f"{artist['name']} is an artist on the ECHO label.",
            "photo_url": artist.get("profile_photo_url"),
            "social_links": social_links,
            "discography": [dict(r) for r in releases],
            "press_contact": "press@echo-music.com",
            "booking_contact": "booking@echo-music.com",
            "label": "ECHO Music Group",
            "sections": [
                "artist_bio",
                "discography",
                "press_photos",
                "social_stats",
                "streaming_links",
                "contact",
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"[PR] EPK built for {artist['name']}")
        return epk

    async def _monitor_coverage(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow("SELECT name FROM artists WHERE id = $1::uuid", artist_id)
        artist_name = artist["name"] if artist else task.payload.get("artist_name", "")

        # In production, integrate with Google News API / mention tracking services
        mock_coverage = [
            {
                "outlet": "Pigeons & Planes",
                "headline": f"{artist_name}'s debut single is one to watch",
                "url": "https://pigeonsandplanes.com/discover",
                "sentiment": "positive",
                "date": datetime.now(timezone.utc).isoformat(),
            },
        ]

        return {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "coverage_found": len(mock_coverage),
            "coverage": mock_coverage,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _submit_awards(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow(
            "SELECT name, genre FROM artists WHERE id = $1::uuid", artist_id
        )
        if not artist:
            return {"error": "Artist not found"}

        genre = (artist.get("genre") or "").lower()
        streams = task.payload.get("streams", 0)

        eligible = []
        for award in AWARD_OPPORTUNITIES:
            min_streams = award.get("min_streams", 0)
            award_genres = award.get("genres", [])

            if streams >= min_streams:
                if not award_genres or genre in award_genres:
                    eligible.append({
                        "award": award["name"],
                        "category": award["category"],
                        "status": "eligible",
                        "deadline_month": award.get("deadline_month"),
                    })

        logger.info(f"[PR] Awards review for {artist['name']}: {len(eligible)} eligible")
        return {
            "artist_id": artist_id,
            "artist_name": artist["name"],
            "streams": streams,
            "eligible_awards": eligible,
            "total_opportunities": len(AWARD_OPPORTUNITIES),
        }
