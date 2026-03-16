"""
Sync Agent
Pitches catalog to music supervisors, ad agencies, gaming companies.
Manages sync briefs, one-stop clearance (master + publishing), and fee quoting.
"""

import json
import logging
import random
import uuid
from datetime import datetime, timezone

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Sync fee ranges by usage type (min, max in USD)
SYNC_FEES = {
    "local_tv_ad": (5_000, 25_000),
    "national_tv_ad": (25_000, 250_000),
    "digital_social_ad": (2_000, 15_000),
    "tv_show_network": (5_000, 50_000),
    "streaming_series": (10_000, 75_000),
    "indie_film": (1_000, 10_000),
    "video_game": (5_000, 100_000),
    "trailer": (15_000, 100_000),
    "documentary": (3_000, 30_000),
}

# CRM contacts for sync pitching
SYNC_CONTACTS = [
    {"name": "Alex Rivera", "company": "Beats & Screens", "role": "Music Supervisor", "specialties": ["drama", "thriller"]},
    {"name": "Jamie Chen", "company": "Adwave Music", "role": "Ad Agency Music Lead", "specialties": ["auto", "tech", "food"]},
    {"name": "Sam Torres", "company": "Level Up Audio", "role": "Game Audio Director", "specialties": ["action", "rpg", "indie"]},
    {"name": "Morgan Ellis", "company": "Netflix Music Licensing", "role": "Music Supervisor", "specialties": ["drama", "comedy", "documentary"]},
    {"name": "Drew Nakamura", "company": "Filmtracks Agency", "role": "Film Music Supervisor", "specialties": ["indie film", "feature film"]},
]


class SyncAgent(BaseAgent):
    agent_id = "sync"
    agent_name = "Sync Agent"
    subscriptions = ["release.distributed", "sync.brief_received"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Sync] Online. Catalog licensing engine active.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "pitch_catalog": self._pitch_catalog,
            "submit_pitch": self._submit_pitch,
            "process_brief": self._process_brief,
            "quote_sync_fee": self._quote_sync_fee,
            "clear_sync": self._clear_sync,
            "tag_catalog": self._tag_catalog,
            # legacy
            "tag_for_sync": self._tag_for_sync,
            "pitch_sync": self._pitch_sync,
            "catalog_search": self._catalog_search,
            "report_sync_revenue": self._report_sync_revenue,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        payload = message.get("payload", {})
        if topic == "release.distributed":
            release_id = payload.get("release_id")
            if release_id:
                # Auto-tag newly distributed releases for sync
                tracks = await self.db_fetch(
                    "SELECT id FROM tracks WHERE release_id = $1::uuid", release_id
                )
                for track in tracks:
                    await self.send_message("sync", "tag_catalog", {"track_id": track["id"]})
        elif topic == "sync.brief_received":
            await self._process_brief(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="process_brief",
                payload=payload,
            ))

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _pitch_catalog(self, task: AgentTask) -> dict:
        brief = task.payload.get("brief", {})
        mood = brief.get("mood", [])
        genre = brief.get("genre", "")
        energy_min = brief.get("energy_min", 0)
        energy_max = brief.get("energy_max", 10)
        usage_type = brief.get("usage_type", "")

        # Search catalog using sync tags
        tracks = await self.db_fetch(
            """
            SELECT t.id, t.title, t.bpm, t.key, t.genre, t.sync_tags_json, a.name AS artist_name
            FROM tracks t
            LEFT JOIN artists a ON t.artist_id = a.id
            WHERE t.sync_tags_json IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 20
            """,
        )

        scored = []
        for track in tracks:
            tags = track.get("sync_tags_json") or {}
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except Exception:
                    tags = {}

            score = 0
            track_moods = tags.get("mood", [])
            if any(m in track_moods for m in (mood if isinstance(mood, list) else [mood])):
                score += 3
            if genre and genre.lower() in [g.lower() for g in tags.get("genre", [])]:
                score += 2
            track_energy = tags.get("energy", 5)
            if energy_min <= track_energy <= energy_max:
                score += 2
            if usage_type and usage_type in tags.get("use_cases", []):
                score += 3
            if tags.get("sync_ready", False):
                score += 1

            scored.append({**track, "match_score": score})

        top_5 = sorted(scored, key=lambda x: x["match_score"], reverse=True)[:5]

        logger.info(f"[Sync] Catalog pitch: {len(top_5)} top matches for brief")
        return {
            "brief": brief,
            "catalog_searched": len(tracks),
            "top_matches": top_5,
        }

    async def _submit_pitch(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        contact_name = task.payload.get("contact_name", "")
        contact_company = task.payload.get("contact_company", "")
        opportunity = task.payload.get("opportunity", "")
        usage_type = task.payload.get("usage_type", "")

        track = await self.db_fetchrow(
            "SELECT t.title, a.name FROM tracks t LEFT JOIN artists a ON t.artist_id = a.id WHERE t.id = $1::uuid",
            track_id,
        )

        pitch_id = str(uuid.uuid4())
        pitch = {
            "pitch_id": pitch_id,
            "track_id": track_id,
            "track_title": track["title"] if track else "",
            "artist": track["name"] if track else "",
            "contact_name": contact_name,
            "contact_company": contact_company,
            "opportunity": opportunity,
            "usage_type": usage_type,
            "status": "submitted",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "one_stop": True,  # ECHO owns both master + publishing
        }

        await self.log_audit("sync_pitch_submitted", "tracks", track_id, {
            "contact": contact_name,
            "company": contact_company,
            "opportunity": opportunity,
        })
        logger.info(f"[Sync] Pitch submitted: '{track['title'] if track else track_id}' → {contact_company}")
        return pitch

    async def _process_brief(self, task: AgentTask) -> dict:
        brief = task.payload.get("brief", task.payload)
        brief_id = task.payload.get("brief_id", str(uuid.uuid4()))

        usage_type = brief.get("usage_type", "")
        mood = brief.get("mood", [])
        genre = brief.get("genre", "")
        budget = brief.get("budget_usd", 0)
        deadline = brief.get("deadline", "")
        client = brief.get("client", "Unknown")

        # Match catalog
        match_result = await self._pitch_catalog(AgentTask(
            task_id=task.task_id,
            task_type="pitch_catalog",
            payload={"brief": brief},
        ))

        # Quote fee range
        fee_result = await self._quote_sync_fee(AgentTask(
            task_id=task.task_id,
            task_type="quote_sync_fee",
            payload={"usage_type": usage_type, "budget": budget},
        ))

        # Select relevant contacts for follow-up pitch
        contacts = [c for c in SYNC_CONTACTS if any(s in usage_type for s in c["specialties"])]
        if not contacts:
            contacts = SYNC_CONTACTS[:2]

        logger.info(f"[Sync] Brief processed for '{client}': {len(match_result['top_matches'])} matches found")
        return {
            "brief_id": brief_id,
            "client": client,
            "usage_type": usage_type,
            "top_matches": match_result["top_matches"],
            "recommended_fee": fee_result,
            "contacts_notified": [c["name"] for c in contacts],
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _quote_sync_fee(self, task: AgentTask) -> dict:
        usage_type = task.payload.get("usage_type", "digital_social_ad")
        budget = task.payload.get("budget", 0)
        territory = task.payload.get("territory", "worldwide")
        term_years = task.payload.get("term_years", 1)
        exclusivity = task.payload.get("exclusivity", False)

        usage_key = usage_type.lower().replace(" ", "_").replace("-", "_")
        fee_range = SYNC_FEES.get(usage_key, SYNC_FEES["digital_social_ad"])
        fee_min, fee_max = fee_range

        # Adjust for territory and exclusivity
        if territory == "worldwide":
            fee_min = int(fee_min * 1.5)
            fee_max = int(fee_max * 1.5)
        if exclusivity:
            fee_min = int(fee_min * 2)
            fee_max = int(fee_max * 2)
        if term_years > 1:
            fee_min = int(fee_min * (1 + (term_years - 1) * 0.3))
            fee_max = int(fee_max * (1 + (term_years - 1) * 0.3))

        recommended = int((fee_min + fee_max) / 2)
        in_budget = budget >= fee_min if budget > 0 else None

        return {
            "usage_type": usage_type,
            "territory": territory,
            "term_years": term_years,
            "exclusivity": exclusivity,
            "fee_range": {"min": fee_min, "max": fee_max},
            "recommended_fee": recommended,
            "budget_provided": budget,
            "in_budget": in_budget,
            "note": "ECHO provides one-stop clearance (master + publishing) — single invoice, no split rights.",
        }

    async def _clear_sync(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        usage_type = task.payload.get("usage_type", "")
        licensee = task.payload.get("licensee", "")
        fee_usd = task.payload.get("fee_usd", 0)
        territory = task.payload.get("territory", "worldwide")
        term_years = task.payload.get("term_years", 1)

        track = await self.db_fetchrow(
            "SELECT t.title, t.artist_id, a.name FROM tracks t LEFT JOIN artists a ON t.artist_id = a.id WHERE t.id = $1::uuid",
            track_id,
        )
        if not track:
            return {"error": "Track not found", "track_id": track_id}

        clearance_id = str(uuid.uuid4())
        label_share = round(fee_usd * 0.50, 2)
        artist_share = round(fee_usd * 0.50, 2)

        clearance = {
            "clearance_id": clearance_id,
            "track_id": track_id,
            "track_title": track["title"],
            "artist": track["name"],
            "licensee": licensee,
            "usage_type": usage_type,
            "territory": territory,
            "term_years": term_years,
            "sync_fee_usd": fee_usd,
            "master_cleared": True,
            "publishing_cleared": True,
            "one_stop": True,
            "label_share": label_share,
            "artist_share": artist_share,
            "status": "cleared",
            "cleared_at": datetime.now(timezone.utc).isoformat(),
        }

        # Log royalty entry
        if fee_usd > 0 and track.get("artist_id"):
            await self.db_execute(
                """
                INSERT INTO royalties (artist_id, release_id, source, gross_amount, net_amount, period_start, period_end)
                SELECT $1::uuid, r.id, 'sync', $2, $3, CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year'
                FROM tracks t LEFT JOIN releases r ON t.release_id = r.id WHERE t.id = $4::uuid
                """,
                track["artist_id"], fee_usd, artist_share, track_id,
            )

        await self.log_audit("sync_cleared", "tracks", track_id, {
            "licensee": licensee,
            "fee": fee_usd,
            "clearance_id": clearance_id,
        })
        logger.info(f"[Sync] Cleared: '{track['title']}' for {licensee} — ${fee_usd}")
        return clearance

    async def _tag_catalog(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        track = await self.db_fetchrow(
            "SELECT t.title, t.bpm, t.key, t.genre FROM tracks WHERE id = $1::uuid",
            track_id,
        )
        if not track:
            return {"error": "Track not found", "track_id": track_id}

        genre = (track.get("genre") or "pop").lower()
        bpm = track.get("bpm") or 120

        # Infer mood and energy from genre/bpm
        mood_map = {
            "hip-hop": ["confident", "urban", "gritty"],
            "pop": ["uplifting", "feel-good", "energetic"],
            "r&b": ["soulful", "smooth", "romantic"],
            "electronic": ["euphoric", "driving", "hypnotic"],
            "indie": ["introspective", "dreamy", "nostalgic"],
            "default": ["neutral", "versatile"],
        }
        use_case_map = {
            "hip-hop": ["montage", "sports", "lifestyle_ad"],
            "pop": ["lifestyle_ad", "romance", "celebration"],
            "r&b": ["love_scene", "montage", "fashion"],
            "electronic": ["action", "title_sequence", "tech_ad"],
            "indie": ["travel", "coming_of_age", "drama"],
            "default": ["background", "montage"],
        }

        energy = min(10, max(1, int((bpm - 60) / 15) + 3))
        genre_key = genre if genre in mood_map else "default"

        tags = {
            "mood": mood_map[genre_key],
            "genre": [genre],
            "energy": energy,
            "bpm": bpm,
            "vocal": "unknown",
            "instruments": [],
            "use_cases": use_case_map[genre_key],
            "sync_ready": True,
        }

        await self.db_execute(
            "UPDATE tracks SET sync_tags_json = $2::jsonb WHERE id = $1::uuid",
            track_id, json.dumps(tags),
        )

        return {"track_id": track_id, "title": track["title"], "tags": tags}

    # ----------------------------------------------------------------
    # Legacy handlers
    # ----------------------------------------------------------------

    async def _tag_for_sync(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        tags = task.payload.get("tags", {})
        await self.db_execute(
            "UPDATE tracks SET sync_tags_json = $2::jsonb WHERE id = $1::uuid",
            track_id, json.dumps(tags),
        )
        return {"track_id": track_id, "tags_applied": tags}

    async def _pitch_sync(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        opportunity = task.payload.get("opportunity", "")
        return await self._submit_pitch(AgentTask(
            task_id=task.task_id,
            task_type="submit_pitch",
            payload={"track_id": track_id, "opportunity": opportunity},
        ))

    async def _catalog_search(self, task: AgentTask) -> dict:
        query = task.payload.get("query", "")
        bpm_min = task.payload.get("bpm_min")
        bpm_max = task.payload.get("bpm_max")
        params = [f"%{query}%"]
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
            "SELECT COALESCE(SUM(net_amount), 0) AS total FROM royalties WHERE source = 'sync'"
        )
        return {"sync_revenue_total": float(revenue["total"]) if revenue else 0.0}
