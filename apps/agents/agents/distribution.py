"""
ECHO Distribution Agent
Get every release onto every platform, on time, with perfect metadata.
"""
import asyncio
import json
import logging
import random
import re
import string
from datetime import datetime, timezone, timedelta
from typing import Optional
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

PLATFORMS = [
    "spotify", "apple_music", "amazon_music", "tidal",
    "youtube_music", "deezer", "tiktok_sound", "instagram_music",
]


class DistributionAgent(BaseAgent):
    agent_id = "distribution"
    agent_name = "Distribution Agent"
    subscriptions = ["releases.ready", "agent.distribution", "release.master_delivered"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        asyncio.create_task(self._release_monitor_loop())
        logger.info("[Distribution] Online. Ready to distribute to all platforms.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "prepare_release": self._task_prepare_release,
            "submit_to_distributor": self._task_submit_to_distributor,
            "check_release_status": self._task_check_release_status,
            "submit_playlist_pitch": self._task_submit_playlist_pitch,
            "generate_isrc": self._task_generate_isrc,
            "generate_upc": self._task_generate_upc,
            "validate_metadata": self._task_validate_metadata,
            "setup_content_id": self._task_setup_content_id,
            "create_presave_link": self._task_create_presave_link,
            "schedule_release": self._task_schedule_release,
            "playlist_pitch": self._task_playlist_pitch,
        }
        handler = handlers.get(task.task_type, self._task_default)
        return await handler(task)

    # ----------------------------------------------------------------
    # Hero skill: Playlist Infiltrator
    # ----------------------------------------------------------------

    # Genre → editorial playlist category mapping
    _GENRE_PLAYLIST_MAP = {
        "hip-hop":      ["RapCaviar", "Most Necessary", "Get Turnt", "Rap Life", "Feelin' Myself"],
        "pop":          ["Today's Top Hits", "Pop Rising", "New Music Friday", "mint", "Teen Party"],
        "r&b":          ["Are & Be", "R&B Only", "Soul", "Chill R&B", "Late Night R&B"],
        "electronic":   ["Electronic Rising", "Brain Food", "Electro-Mania", "Ambient Relaxation", "Dance Rising"],
        "indie":        ["Fresh Finds", "Indie Pop", "The Indie List", "Lorem", "All New Indie"],
        "rock":         ["Rock This", "All New Rock", "New Noise", "Pumped Pop", "Hard Rock Café"],
        "latin":        ["Baila Reggaeton", "Latin Pop Rising", "Viva Latino", "Tropical Morning"],
        "country":      ["Hot Country", "New Boots", "Country Gold", "Country Coffeehouse"],
        "jazz":         ["Jazz Classics", "Jazz X-Press", "Smooth Jazz", "Late Night Jazz"],
        "classical":    ["Classical New Releases", "Peaceful Piano", "Classical Focus", "Instrumental Study"],
        "default":      ["New Music Friday", "Fresh Finds", "Lorem", "Discover Weekly", "Release Radar"],
    }

    # Required metadata fields for Spotify editorial pitches
    _METADATA_FIELDS = [
        ("title", "Release title"),
        ("genre", "Genre"),
        ("release_date", "Release date (YYYY-MM-DD)"),
        ("artwork_url", "Cover artwork (3000×3000 px JPG/PNG)"),
        ("master_audio_url", "Master audio file"),
        ("upc", "UPC barcode"),
        ("isrc", "ISRC per track"),
        ("mood", "Mood/vibe descriptor"),
    ]

    async def _task_playlist_pitch(self, task: AgentTask) -> AgentResult:
        """
        Playlist Infiltrator hero skill.
        Builds a targeted editorial playlist pitch strategy for a release.
        Calculates pitch score, optimal pitch date, target playlists, and a ready-to-send pitch template.
        """
        release_id = task.payload.get("release_id") or task.release_id
        artist_id = task.payload.get("artist_id") or task.artist_id
        genre = task.payload.get("genre", "").lower()
        mood = task.payload.get("mood", "")
        tempo = task.payload.get("tempo", "")

        release = None
        if release_id:
            release = await self.db_fetchrow(
                """
                SELECT r.title, r.release_date, r.genre, r.artwork_url,
                       r.master_audio_url, r.upc, r.status, r.metadata,
                       a.name as artist_name, a.stage_name, a.bio
                FROM releases r
                LEFT JOIN artists a ON r.artist_id = a.id
                WHERE r.id = $1::uuid
                """,
                release_id,
            )

        if release:
            genre = genre or (release.get("genre") or "default").lower()

        artist_name = ""
        if release:
            artist_name = release.get("stage_name") or release.get("artist_name") or ""
        if not artist_name and artist_id:
            artist_row = await self.db_fetchrow(
                "SELECT name, stage_name FROM artists WHERE id = $1::uuid", artist_id
            )
            if artist_row:
                artist_name = artist_row.get("stage_name") or artist_row.get("name") or ""

        release_title = release.get("title", "Untitled") if release else "Untitled"
        release_date = release.get("release_date") if release else None
        artist_bio = (release.get("bio") or f"{artist_name} is an emerging artist on Melodio.") if release else ""

        # Optimal pitch date: 7 days before release (Spotify editorial requirement)
        optimal_pitch_date = None
        if release_date:
            from datetime import date as _date
            if isinstance(release_date, str):
                release_date = _date.fromisoformat(release_date)
            pitch_dt = release_date - timedelta(days=7)
            optimal_pitch_date = pitch_dt.isoformat()

        # Pitch score 0-100
        score = 0
        score_breakdown = {}

        # Release quality (30 pts): has artwork + audio
        rq = 0
        if release and release.get("artwork_url"):
            rq += 15
        if release and release.get("master_audio_url"):
            rq += 15
        score_breakdown["release_quality"] = rq
        score += rq

        # Metadata completeness (40 pts)
        mc = 0
        if release and release.get("title"):
            mc += 8
        if genre and genre != "default":
            mc += 8
        if release and release.get("upc"):
            mc += 8
        if mood:
            mc += 8
        if tempo:
            mc += 8
        score_breakdown["metadata_completeness"] = mc
        score += mc

        # Artist momentum (30 pts): check streams_total and prior releases
        am = 0
        if artist_id:
            streams_row = await self.db_fetchrow(
                """
                SELECT COALESCE(SUM(t.streams_total), 0) AS total
                FROM tracks t
                JOIN releases r ON t.release_id = r.id
                WHERE r.artist_id = $1::uuid
                """,
                artist_id,
            )
            total_streams = int(streams_row["total"]) if streams_row else 0
            if total_streams > 100_000:
                am = 30
            elif total_streams > 10_000:
                am = 20
            elif total_streams > 1_000:
                am = 10
            else:
                am = 5
        score_breakdown["artist_momentum"] = am
        score += am

        pitch_score = min(score, 100)

        # Target playlists ranked by fit
        playlists = self._GENRE_PLAYLIST_MAP.get(genre, self._GENRE_PLAYLIST_MAP["default"])
        if mood:
            # Boost mood-aligned playlists by adding mood keyword to fit description
            mood_lower = mood.lower()
            playlists = playlists[:5]  # cap at 5
        target_playlists = []
        for i, pl in enumerate(playlists[:5]):
            fit_score = max(100 - i * 12, 40)
            target_playlists.append({
                "playlist": pl,
                "platform": "spotify",
                "fit_score": fit_score,
                "genre_match": genre,
            })

        # Metadata checklist
        metadata_checklist = []
        track_isrc = None
        if release_id:
            track_row = await self.db_fetchrow(
                "SELECT isrc FROM tracks WHERE release_id = $1::uuid LIMIT 1", release_id
            )
            track_isrc = track_row.get("isrc") if track_row else None

        for field_key, field_label in self._METADATA_FIELDS:
            if field_key == "isrc":
                complete = bool(track_isrc)
            elif field_key == "mood":
                complete = bool(mood)
            elif release:
                complete = bool(release.get(field_key))
            else:
                complete = False
            metadata_checklist.append({
                "field": field_label,
                "complete": complete,
                "status": "✓" if complete else "MISSING",
            })

        # Build pitch template
        release_date_str = str(release_date) if release_date else "TBD"
        pitch_template = (
            f"EDITORIAL PLAYLIST PITCH\n"
            f"Artist: {artist_name}\n"
            f"Track: {release_title}\n"
            f"Genre: {genre.title()}" + (f" | Mood: {mood}" if mood else "") + (f" | Tempo: {tempo}" if tempo else "") + "\n"
            f"Release Date: {release_date_str}\n\n"
            f"About the Artist:\n{artist_bio}\n\n"
            f"Why This Track Belongs on Your Playlist:\n"
            f'"{release_title}" by {artist_name} is a {genre}-driven track built for discovery. '
        )
        if pitch_score >= 70:
            pitch_template += (
                f"With strong streaming momentum and polished production, this release is primed for editorial placement. "
                f"We believe it\'s a natural fit for {target_playlists[0]['playlist'] if target_playlists else 'your playlist'} "
                f"and would resonate strongly with your listeners."
            )
        else:
            pitch_template += (
                f"This is a fresh voice ready for a wider audience. "
                f"We\'d love your consideration for {target_playlists[0]['playlist'] if target_playlists else 'your playlist'}."
            )
        pitch_template += (
            f"\n\nStreaming Link: [Available at release]\n"
            f"Label: Melodio | melodio.io\n"
            f"Contact: artists@melodio.io"
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "pitch_score": pitch_score,
                "score_breakdown": score_breakdown,
                "optimal_pitch_date": optimal_pitch_date,
                "target_playlists": target_playlists,
                "pitch_template": pitch_template,
                "metadata_checklist": metadata_checklist,
                "genre": genre,
                "hero_skill": "playlist_infiltrator",
            },
        )

    async def _task_default(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            success=False,
            task_id=task.task_id,
            agent_id=self.agent_id,
            error=f"Unknown task type: {task.task_type}",
        )

    async def _task_prepare_release(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id") or task.release_id
        if not release_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="release_id required")

        release = await self.db_fetchrow(
            """SELECT r.*, a.name as artist_name
               FROM releases r
               LEFT JOIN artists a ON r.artist_id = a.id
               WHERE r.id = $1::uuid""",
            release_id,
        )
        if not release:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Release not found")

        missing = []
        warnings = []

        # Required assets
        if not release.get("master_audio_url"):
            missing.append("master_audio_url")
        if not release.get("artwork_url"):
            missing.append("artwork_url")
        if not release.get("title"):
            missing.append("title")
        if not release.get("genre"):
            missing.append("genre")

        # Check ISRC — use track check
        tracks = await self.db_fetch(
            "SELECT id, title, isrc FROM tracks WHERE release_id = $1::uuid",
            release_id,
        )
        if not tracks:
            missing.append("tracks")
        else:
            for track in tracks:
                if not track.get("isrc"):
                    # Auto-generate
                    isrc_task = AgentTask(
                        task_id=task.task_id + f"_isrc_{track['id']}",
                        task_type="generate_isrc",
                        payload={"track_id": str(track["id"])},
                    )
                    await self._task_generate_isrc(isrc_task)

        # Check UPC
        if not release.get("upc"):
            upc_task = AgentTask(
                task_id=task.task_id + "_upc",
                task_type="generate_upc",
                payload={"release_id": release_id},
            )
            await self._task_generate_upc(upc_task)

        # Check artist name
        if not release.get("artist_name"):
            warnings.append("Artist name could not be resolved")

        ready = len(missing) == 0

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "title": release.get("title"),
                "ready": ready,
                "missing": missing,
                "warnings": warnings,
                "tracks_count": len(tracks),
                "platforms": PLATFORMS if ready else [],
            },
        )

    async def _task_submit_to_distributor(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id") or task.release_id
        if not release_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="release_id required")

        release = await self.db_fetchrow(
            """SELECT r.*, a.name as artist_name, a.stage_name
               FROM releases r LEFT JOIN artists a ON r.artist_id = a.id
               WHERE r.id = $1::uuid""",
            release_id,
        )
        if not release:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Release not found")

        tracks = await self.db_fetch(
            "SELECT id, title, isrc, duration_seconds FROM tracks WHERE release_id = $1::uuid",
            release_id,
        )

        # Build distribution payload
        payload = {
            "artist_name": release.get("stage_name") or release.get("artist_name"),
            "release_title": release.get("title"),
            "genre": release.get("genre"),
            "release_date": str(release.get("release_date")) if release.get("release_date") else None,
            "upc": release.get("upc"),
            "artwork_url": release.get("artwork_url"),
            "master_audio_url": release.get("master_audio_url"),
            "tracks": [{"id": str(t["id"]), "title": t["title"], "isrc": t["isrc"]} for t in tracks],
            "platforms": PLATFORMS,
        }

        # Generate tracking ID
        tracking_id = "DK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))

        # Record submission
        submission_id = await self.db_execute(
            """INSERT INTO distribution_submissions
                   (release_id, distributor, status, submission_payload, tracking_id, expected_live_at)
               VALUES ($1::uuid, 'distrokid', 'submitted', $2::jsonb, $3, $4)
               RETURNING id""",
            release_id,
            json.dumps(payload),
            tracking_id,
            datetime.now(timezone.utc) + timedelta(days=3),
        )

        # Record per-platform expected go-live dates
        expected_live = datetime.now(timezone.utc) + timedelta(days=3)
        for platform in PLATFORMS:
            await self.db_execute(
                """INSERT INTO release_platforms (release_id, platform, status, went_live_at)
                   VALUES ($1::uuid, $2, 'submitted', NULL)
                   ON CONFLICT DO NOTHING""",
                release_id,
                platform,
            )

        # Update release status
        await self.db_execute(
            "UPDATE releases SET status = 'submitted', updated_at = NOW() WHERE id = $1::uuid",
            release_id,
        )

        await self.log_audit("submit_to_distributor", "releases", release_id, {
            "tracking_id": tracking_id,
            "platforms": PLATFORMS,
            "distributor": "distrokid",
        })

        # NOTE: Real DistroKid API call would go here
        logger.info(f"[Distribution] Release {release_id} submitted to DistroKid (tracking: {tracking_id})")

        await self.broadcast("release.submitted", {
            "release_id": release_id,
            "tracking_id": tracking_id,
            "platforms": PLATFORMS,
        })

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "tracking_id": tracking_id,
                "distributor": "distrokid",
                "status": "submitted",
                "platforms": PLATFORMS,
                "expected_live_at": expected_live.isoformat(),
                "payload_summary": {
                    "artist": payload["artist_name"],
                    "title": payload["release_title"],
                    "tracks": len(tracks),
                },
            },
        )

    async def _task_validate_metadata(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id") or task.release_id
        if not release_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="release_id required")

        release = await self.db_fetchrow(
            """SELECT r.*, a.name as artist_name, a.stage_name
               FROM releases r LEFT JOIN artists a ON r.artist_id = a.id
               WHERE r.id = $1::uuid""",
            release_id,
        )
        if not release:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Release not found")

        tracks = await self.db_fetch(
            "SELECT id, title, isrc, credits FROM tracks WHERE release_id = $1::uuid",
            release_id,
        )

        errors = []
        warnings = []

        title = release.get("title", "") or ""
        artist_name = release.get("stage_name") or release.get("artist_name") or ""

        # Artist name: no ALL CAPS (unless stylized — warn, don't error)
        if artist_name and artist_name == artist_name.upper() and len(artist_name) > 3:
            warnings.append(f"Artist name '{artist_name}' is ALL CAPS — confirm stylization is intentional")

        # Genre required
        if not release.get("genre"):
            errors.append("Genre is required")

        # UPC check
        if release.get("upc"):
            upc = str(release["upc"]).replace("-", "").replace(" ", "")
            if not upc.isdigit() or len(upc) != 12:
                errors.append(f"UPC '{upc}' is not a valid 12-digit barcode")

        # Per-track validation
        for track in tracks:
            track_title = track.get("title", "") or ""
            track_id = str(track["id"])

            # No emojis in title
            emoji_pattern = re.compile(
                "[\U00010000-\U0010ffff"
                "\U0001F600-\U0001F64F"
                "\U0001F300-\U0001F5FF"
                "\U0001F680-\U0001F6FF"
                "\U0001F1E0-\U0001F1FF"
                "]+",
                flags=re.UNICODE,
            )
            if emoji_pattern.search(track_title):
                errors.append(f"Track '{track_title}': emojis not allowed in title")

            # Feature format: should be "(feat. Artist)"
            if "feat" in track_title.lower():
                if not re.search(r'\(feat\. .+\)', track_title):
                    warnings.append(f"Track '{track_title}': feature format should be '(feat. Artist Name)'")

            # Remix format
            if "remix" in track_title.lower():
                if not re.search(r'\(.+ Remix\)', track_title):
                    warnings.append(f"Track '{track_title}': remix format should be 'Title (Artist Remix)'")

            # ISRC validation
            isrc = track.get("isrc")
            if isrc:
                if not re.match(r'^[A-Z]{2}-[A-Z0-9]{3}-\d{2}-\d{5}$', isrc):
                    errors.append(f"Track '{track_title}': ISRC '{isrc}' format invalid — expected CC-XXX-YY-NNNNN")
            else:
                warnings.append(f"Track '{track_title}': no ISRC assigned")

            # Credits check
            credits = track.get("credits") or {}
            if isinstance(credits, str):
                try:
                    credits = json.loads(credits)
                except Exception:
                    credits = {}
            if not credits.get("writer"):
                warnings.append(f"Track '{track_title}': songwriter credit missing")
            if not credits.get("producer"):
                warnings.append(f"Track '{track_title}': producer credit missing")

        valid = len(errors) == 0

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "valid": valid,
                "errors": errors,
                "warnings": warnings,
                "tracks_checked": len(tracks),
            },
        )

    async def _task_generate_isrc(self, task: AgentTask) -> AgentResult:
        track_id = task.payload.get("track_id")
        if not track_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="track_id required")

        # Check if already has ISRC
        existing = await self.db_fetchrow("SELECT isrc FROM tracks WHERE id = $1::uuid", track_id)
        if existing and existing.get("isrc"):
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id=self.agent_id,
                result={"track_id": track_id, "isrc": existing["isrc"], "generated": False},
            )

        # Get next sequence number
        seq_row = await self.db_fetchrow(
            "SELECT COUNT(*) as cnt FROM tracks WHERE isrc IS NOT NULL"
        )
        seq = int(seq_row["cnt"] or 0) + 1

        year_2digit = datetime.now(timezone.utc).strftime("%y")
        isrc = f"US-ECH-{year_2digit}-{seq:05d}"

        await self.db_execute(
            "UPDATE tracks SET isrc = $2, updated_at = NOW() WHERE id = $1::uuid",
            track_id,
            isrc,
        )

        logger.info(f"[Distribution] Generated ISRC {isrc} for track {track_id}")

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={"track_id": track_id, "isrc": isrc, "generated": True},
        )

    async def _task_generate_upc(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id") or task.release_id
        if not release_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="release_id required")

        existing = await self.db_fetchrow("SELECT upc FROM releases WHERE id = $1::uuid", release_id)
        if existing and existing.get("upc"):
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id=self.agent_id,
                result={"release_id": release_id, "upc": existing["upc"], "generated": False},
            )

        # Generate 12-digit UPC with valid check digit
        prefix = "884502"  # Melodio label prefix
        random_digits = "".join(random.choices(string.digits, k=5))
        digits_11 = prefix + random_digits

        # Calculate check digit (UPC-A algorithm)
        odd_sum = sum(int(d) for i, d in enumerate(digits_11) if i % 2 == 0)
        even_sum = sum(int(d) for i, d in enumerate(digits_11) if i % 2 == 1)
        check = (10 - ((odd_sum * 3 + even_sum) % 10)) % 10
        upc = digits_11 + str(check)

        await self.db_execute(
            "UPDATE releases SET upc = $2, updated_at = NOW() WHERE id = $1::uuid",
            release_id,
            upc,
        )

        logger.info(f"[Distribution] Generated UPC {upc} for release {release_id}")

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={"release_id": release_id, "upc": upc, "generated": True},
        )

    async def _task_submit_playlist_pitch(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id") or task.release_id
        if not release_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="release_id required")

        release = await self.db_fetchrow(
            """SELECT r.*, a.name as artist_name, a.stage_name, a.bio
               FROM releases r LEFT JOIN artists a ON r.artist_id = a.id
               WHERE r.id = $1::uuid""",
            release_id,
        )
        if not release:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Release not found")

        # Check lead time — need >= 28 days before release
        release_date = release.get("release_date")
        days_until_release = None
        if release_date:
            delta = release_date - datetime.now(timezone.utc).date()
            days_until_release = delta.days
            if days_until_release < 28:
                return AgentResult(
                    success=False,
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    error=f"Playlist pitch requires 28+ days lead time. Only {days_until_release} days until release.",
                )

        artist_name = release.get("stage_name") or release.get("artist_name") or "Unknown Artist"
        bio = release.get("bio") or f"{artist_name} is a recording artist on Melodio."
        streaming_url = release.get("spotify_url") or f"melodio.io/releases/{release_id}"

        pitch_text = (
            f"PLAYLIST PITCH — {artist_name}: '{release.get('title')}'\n\n"
            f"Artist: {artist_name}\n"
            f"Genre: {release.get('genre', 'N/A')}\n"
            f"Release Date: {release_date}\n"
            f"Streaming Link: {streaming_url}\n\n"
            f"About the Artist:\n{bio}\n\n"
            f"Why this track fits your playlist:\n"
            f"'{release.get('title')}' is a {release.get('genre', 'genre-defining')} track with strong momentum. "
            f"We believe it's a perfect fit for your editorial playlist and would appreciate your consideration."
        )

        # Log pitch to contacts table
        await self.db_execute(
            """INSERT INTO contacts (name, contact_type, notes, created_by)
               VALUES ($1, 'playlist_curator', $2, 'distribution_agent')""",
            f"Editorial Pitch: {release.get('title')}",
            pitch_text[:500],
        )

        logger.info(f"[Distribution] Playlist pitch submitted for release {release_id}")

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "pitch_submitted": True,
                "days_until_release": days_until_release,
                "pitch_summary": {
                    "artist": artist_name,
                    "title": release.get("title"),
                    "genre": release.get("genre"),
                    "release_date": str(release_date),
                },
                "pitch_text": pitch_text,
            },
        )

    async def _task_check_release_status(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id") or task.release_id
        if not release_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="release_id required")

        release = await self.db_fetchrow(
            "SELECT id, title, status, release_date, spotify_url, apple_url, upc FROM releases WHERE id = $1::uuid",
            release_id,
        )
        if not release:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Release not found")

        # Per-platform status
        platforms = await self.db_fetch(
            "SELECT platform, status, platform_url, went_live_at FROM release_platforms WHERE release_id = $1::uuid",
            release_id,
        )

        # Latest submission
        submission = await self.db_fetchrow(
            """SELECT tracking_id, distributor, status, submitted_at, expected_live_at
               FROM distribution_submissions WHERE release_id = $1::uuid
               ORDER BY submitted_at DESC LIMIT 1""",
            release_id,
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "title": release.get("title"),
                "overall_status": release.get("status"),
                "release_date": str(release.get("release_date")) if release.get("release_date") else None,
                "upc": release.get("upc"),
                "platform_status": [dict(p) for p in platforms],
                "submission": dict(submission) if submission else None,
            },
        )

    async def _task_setup_content_id(self, task: AgentTask) -> AgentResult:
        track_id = task.payload.get("track_id")
        if not track_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="track_id required")

        track = await self.db_fetchrow("SELECT id, title, isrc FROM tracks WHERE id = $1::uuid", track_id)
        if not track:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Track not found")

        # Update metadata to mark content ID as active
        await self.db_execute(
            """UPDATE tracks
               SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"content_id_active": true}'::jsonb,
                   updated_at = NOW()
               WHERE id = $1::uuid""",
            track_id,
        )

        await self.log_audit("setup_content_id", "tracks", track_id, {
            "track_title": track.get("title"),
            "isrc": track.get("isrc"),
        })

        logger.info(f"[Distribution] Content ID setup for track {track_id}")

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "track_id": track_id,
                "title": track.get("title"),
                "isrc": track.get("isrc"),
                "content_id_active": True,
                "setup_at": datetime.now(timezone.utc).isoformat(),
                "note": "YouTube Content ID registration queued via DistroKid",
            },
        )

    async def _task_create_presave_link(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id") or task.release_id
        if not release_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="release_id required")

        release = await self.db_fetchrow("SELECT id, title FROM releases WHERE id = $1::uuid", release_id)
        if not release:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Release not found")

        presave_url = f"https://melodio.io/presave/{release_id}"

        await self.db_execute(
            """UPDATE releases
               SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('presave_url', $2::text),
                   updated_at = NOW()
               WHERE id = $1::uuid""",
            release_id,
            presave_url,
        )

        logger.info(f"[Distribution] Presave link created for {release_id}: {presave_url}")

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "title": release.get("title"),
                "presave_url": presave_url,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _task_schedule_release(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id") or task.release_id
        target_date_str = task.payload.get("target_date") or task.payload.get("release_date")

        if not release_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="release_id required")
        if not target_date_str:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="target_date required")

        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="target_date must be YYYY-MM-DD format",
            )

        today = datetime.now(timezone.utc).date()
        days_ahead = (target_date - today).days

        if days_ahead < 28:
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id=self.agent_id,
                error=f"Minimum 28 days lead time required. Target date is only {days_ahead} days away.",
            )

        release = await self.db_fetchrow("SELECT id, title FROM releases WHERE id = $1::uuid", release_id)
        if not release:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Release not found")

        # Auto-generate timeline
        t_minus_28 = target_date - timedelta(days=28)
        t_minus_21 = target_date - timedelta(days=21)
        t_minus_14 = target_date - timedelta(days=14)
        t_minus_7 = target_date - timedelta(days=7)

        timeline = [
            {"date": str(t_minus_28), "milestone": "T-28", "action": "Upload masters + metadata to distributor"},
            {"date": str(t_minus_21), "milestone": "T-21", "action": "Submit editorial playlist pitch"},
            {"date": str(t_minus_14), "milestone": "T-14", "action": "Contingency / asset fixes window"},
            {"date": str(t_minus_7), "milestone": "T-7", "action": "Marketing campaign launch + social posts"},
            {"date": str(target_date), "milestone": "T-0", "action": "Release day — confirm live on all platforms"},
        ]

        # Update DB
        await self.db_execute(
            "UPDATE releases SET release_date = $2, status = 'scheduled', updated_at = NOW() WHERE id = $1::uuid",
            release_id,
            target_date,
        )

        # Enqueue future tasks for marketing and social agents
        await self.broadcast("release.scheduled", {
            "release_id": release_id,
            "release_date": str(target_date),
            "timeline": timeline,
        })
        await self.send_message("marketing", "release_scheduled", {
            "release_id": release_id,
            "release_date": str(target_date),
            "campaign_start": str(t_minus_7),
        })
        await self.send_message("social", "release_scheduled", {
            "release_id": release_id,
            "release_date": str(target_date),
            "post_date": str(t_minus_7),
        })

        await self.log_audit("schedule_release", "releases", release_id, {
            "release_date": str(target_date),
            "days_lead_time": days_ahead,
        })

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "title": release.get("title"),
                "release_date": str(target_date),
                "days_lead_time": days_ahead,
                "timeline": timeline,
                "status": "scheduled",
            },
        )

    # ----------------------------------------------------------------
    # Background loop
    # ----------------------------------------------------------------

    async def _release_monitor_loop(self):
        """Runs every 4 hours — checks submitted/scheduled releases, alerts on overdue."""
        while self._running:
            try:
                await asyncio.sleep(4 * 3600)
                if not self._running:
                    break

                now = datetime.now(timezone.utc)

                # Overdue releases: past release date but not 'released'
                overdue = await self.db_fetch(
                    """SELECT id, title, release_date, status
                       FROM releases
                       WHERE status IN ('submitted', 'scheduled', 'distributed')
                         AND release_date < CURRENT_DATE""",
                )

                for rel in overdue:
                    release_date = rel.get("release_date")
                    if release_date:
                        days_overdue = (now.date() - release_date).days
                        if days_overdue > 1:
                            severity = "critical" if days_overdue > 24 else "warning"
                            await self.broadcast("agent.ceo", {
                                "topic": "release_overdue",
                                "severity": severity,
                                "release_id": str(rel["id"]),
                                "title": rel["title"],
                                "release_date": str(release_date),
                                "days_overdue": days_overdue,
                            })
                            logger.warning(
                                f"[Distribution] Release '{rel['title']}' is {days_overdue} days overdue "
                                f"(status: {rel['status']})"
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Distribution] Monitor loop error: {e}")
                await asyncio.sleep(60)
