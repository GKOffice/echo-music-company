"""
YouTube Agent
Plans video packages, optimizes SEO, schedules premieres,
seeds reaction channels, and manages the full YouTube presence for each release.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Current year for SEO tags
CURRENT_YEAR = datetime.now().year

# Video package definitions
VIDEO_PACKAGES = {
    "standard": {
        "deliverables": ["lyric_video", "visualizer"],
        "shorts_count": 3,
        "premiere": False,
        "description": "Lyric video + visualizer + 3 Shorts",
    },
    "priority": {
        "deliverables": ["music_video_ai", "lyric_video", "visualizer"],
        "shorts_count": 10,
        "premiere": True,
        "description": "AI music video + lyric video + visualizer + 10 Shorts + premiere",
    },
}

# Reaction channel database (seed list)
REACTION_CHANNELS = [
    {"channel": "JAMAL LISTEN", "genre_focus": ["hip-hop", "r&b"], "subs_estimate": "500k"},
    {"channel": "The Needle Drop", "genre_focus": ["indie", "electronic", "pop"], "subs_estimate": "3M"},
    {"channel": "Anthony Fantano", "genre_focus": ["indie", "electronic"], "subs_estimate": "3M"},
    {"channel": "No Life Shaq", "genre_focus": ["hip-hop", "r&b", "pop"], "subs_estimate": "2.5M"},
    {"channel": "FIRST REACTION", "genre_focus": ["r&b", "hip-hop"], "subs_estimate": "800k"},
    {"channel": "Genius", "genre_focus": ["hip-hop", "r&b", "pop"], "subs_estimate": "5M"},
    {"channel": "Billboard", "genre_focus": ["pop", "hip-hop", "r&b"], "subs_estimate": "2M"},
    {"channel": "Lyric Breakdown", "genre_focus": ["pop", "indie"], "subs_estimate": "300k"},
]


class YouTubeAgent(BaseAgent):
    agent_id = "youtube"
    agent_name = "YouTube Agent"
    subscriptions = ["release.distributed", "release.qc_approved"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "plan_video_package": self._plan_video_package,
            "generate_video_brief": self._generate_video_brief,
            "create_shorts_plan": self._create_shorts_plan,
            "optimize_seo": self._optimize_seo,
            "schedule_premiere": self._schedule_premiere,
            "generate_thumbnail_brief": self._generate_thumbnail_brief,
            "seed_reaction_channels": self._seed_reaction_channels,
            "algorithm_whisper": self._task_algorithm_whisper,
            # Legacy
            "upload_video": self._upload_video,
            "enable_monetization": self._enable_monetization,
            "create_short": self._create_short,
            "content_id_claim": self._content_id_claim,
            "channel_report": self._channel_report,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    # ----------------------------------------------------------------
    # plan_video_package
    # ----------------------------------------------------------------

    async def _plan_video_package(self, task: AgentTask) -> dict:
        p = task.payload
        release_id = p.get("release_id") or task.release_id
        priority = p.get("priority", "standard")

        release = None
        if release_id:
            release = await self.db_fetchrow(
                "SELECT title, artist_id, release_date FROM releases WHERE id = $1::uuid", release_id
            )

        artist_name = p.get("artist_name", "")
        track_name = (release.get("title") if release else None) or p.get("track_name", "")
        release_date = (release.get("release_date") if release else None) or p.get("release_date")

        package = VIDEO_PACKAGES.get(priority, VIDEO_PACKAGES["standard"])

        # Build production schedule relative to release date
        if release_date:
            try:
                if hasattr(release_date, "strftime"):
                    rd = release_date
                else:
                    rd = datetime.fromisoformat(str(release_date).replace("Z", "+00:00"))
            except Exception:
                rd = datetime.now(timezone.utc) + timedelta(weeks=3)
        else:
            rd = datetime.now(timezone.utc) + timedelta(weeks=3)

        schedule = {}
        if "music_video_ai" in package["deliverables"]:
            schedule["ai_music_video"] = {
                "brief_due": (rd - timedelta(weeks=3)).strftime("%Y-%m-%d"),
                "delivery_due": (rd - timedelta(days=5)).strftime("%Y-%m-%d"),
                "description": "AI-generated music video — brief sent to Creative Agent",
            }
        schedule["lyric_video"] = {
            "brief_due": (rd - timedelta(weeks=2)).strftime("%Y-%m-%d"),
            "delivery_due": (rd - timedelta(days=3)).strftime("%Y-%m-%d"),
            "description": "Lyric video with animated text",
        }
        schedule["visualizer"] = {
            "brief_due": (rd - timedelta(weeks=2)).strftime("%Y-%m-%d"),
            "delivery_due": (rd - timedelta(days=3)).strftime("%Y-%m-%d"),
            "description": "Audio-reactive visualizer",
        }
        schedule["shorts"] = {
            "count": package["shorts_count"],
            "due": (rd - timedelta(days=2)).strftime("%Y-%m-%d"),
            "description": f"{package['shorts_count']} Shorts cut from release content",
        }
        if package["premiere"]:
            schedule["premiere"] = {
                "scheduled": rd.strftime("%Y-%m-%d"),
                "description": "YouTube Premiere — live chat + countdown",
            }

        # Dispatch briefs to Creative Agent
        for video_type in package["deliverables"]:
            await self.send_message("creative", "video_brief", {
                "video_type": video_type,
                "release_id": release_id,
                "artist_name": artist_name,
                "track_name": track_name,
                "due_date": schedule.get(video_type, {}).get("delivery_due"),
            })

        return {
            "release_id": release_id,
            "priority": priority,
            "package": package["description"],
            "deliverables": package["deliverables"],
            "shorts_count": package["shorts_count"],
            "premiere": package["premiere"],
            "schedule": schedule,
            "artist_name": artist_name,
            "track_name": track_name,
        }

    # ----------------------------------------------------------------
    # generate_video_brief
    # ----------------------------------------------------------------

    async def _generate_video_brief(self, task: AgentTask) -> dict:
        p = task.payload
        video_type = p.get("video_type", "lyric_video")
        artist_name = p.get("artist_name", "")
        track_name = p.get("track_name", "")
        mood = p.get("mood", "")
        genre = p.get("genre", "")
        artwork_url = p.get("artwork_url", "")
        release_id = p.get("release_id") or task.release_id

        brief_templates = {
            "lyric_video": {
                "format": "Lyric Video (16:9, 1080p)",
                "duration": "Full track duration",
                "style_notes": (
                    f"Kinetic typography that matches the energy of the track. "
                    f"Lyrics appear on beat. Color palette from artwork. "
                    f"Mood: {mood or 'match the song'}. Genre feel: {genre or 'universal'}."
                ),
                "must_include": ["Artist name lower-third", "Track title card", "Melodio logo end card"],
                "avoid": ["Stock footage", "Distracting backgrounds that compete with lyrics"],
            },
            "visualizer": {
                "format": "Audio Visualizer (16:9, 1080p)",
                "duration": "Full track duration",
                "style_notes": (
                    f"Audio-reactive visuals — waveforms, particles, or geometric shapes responding to the mix. "
                    f"Derived from artwork: {artwork_url or 'TBD'}. Dark, premium aesthetic."
                ),
                "must_include": ["Artist name", "Track title", "Static artwork displayed prominently"],
                "avoid": ["Busy or cluttered visuals", "Bright white backgrounds"],
            },
            "music_video_ai": {
                "format": "Music Video (16:9, 1080p, AI-generated)",
                "duration": "3-4 min edit",
                "style_notes": (
                    f"AI-generated cinematic music video. Mood: {mood}. Genre: {genre}. "
                    f"Visual world should reflect the lyrical themes. "
                    f"Premium, editorial quality. Not generic stock AI look."
                ),
                "must_include": ["Opening title card", "Artist name", "Consistent visual language throughout"],
                "avoid": ["AI artifacts", "Uncanny valley faces", "Generic AI aesthetics"],
            },
        }

        brief = brief_templates.get(video_type, brief_templates["lyric_video"])
        brief.update({
            "video_type": video_type,
            "artist_name": artist_name,
            "track_name": track_name,
            "release_id": release_id,
            "source_artwork": artwork_url,
        })

        await self.send_message("creative", "video_brief", {
            "brief": brief,
            "release_id": release_id,
        })

        return {
            "brief": brief,
            "video_type": video_type,
            "release_id": release_id,
            "sent_to_creative": True,
        }

    # ----------------------------------------------------------------
    # create_shorts_plan
    # ----------------------------------------------------------------

    async def _create_shorts_plan(self, task: AgentTask) -> dict:
        p = task.payload
        release_id = p.get("release_id") or task.release_id
        track_name = p.get("track_name", "")
        artist_name = p.get("artist_name", "")
        priority = p.get("priority", "standard")

        count = VIDEO_PACKAGES.get(priority, VIDEO_PACKAGES["standard"])["shorts_count"]

        # Generate Short concepts (hooks, moments, angles)
        short_templates = [
            {
                "index": 1,
                "concept": "Hook clip — the catchiest 30s of the track with lyrics overlay",
                "format": "9:16 vertical",
                "duration_sec": 30,
                "caption": f"The hook hits different 🎵 #{track_name.replace(' ', '')} #{artist_name.replace(' ', '')}",
            },
            {
                "index": 2,
                "concept": "Studio session or making-of teaser",
                "format": "9:16 vertical",
                "duration_sec": 45,
                "caption": f"Built different 🎹 #{artist_name.replace(' ', '')}",
            },
            {
                "index": 3,
                "concept": "Reaction mashup — fan reactions to the drop",
                "format": "9:16 vertical",
                "duration_sec": 30,
                "caption": f"Y'all not ready 🔥 #{track_name.replace(' ', '')}",
            },
        ]

        # For priority releases, add more creative angles
        if count > 3:
            extra = [
                {
                    "index": 4,
                    "concept": "Lyric breakdown — deep dive into a key verse",
                    "format": "9:16 vertical",
                    "duration_sec": 60,
                    "caption": f"The bars on this one... 🧠 #{track_name.replace(' ', '')}",
                },
                {
                    "index": 5,
                    "concept": "Behind-the-scenes studio moment",
                    "format": "9:16 vertical",
                    "duration_sec": 45,
                    "caption": f"From the session to your speakers 🎙️ #{artist_name.replace(' ', '')}",
                },
            ]
            short_templates.extend(extra[:count - 3])

        shorts = short_templates[:count]

        # Schedule shorts across release week
        schedule_notes = (
            f"Post 1-2 Shorts per day starting 3 days before release, "
            f"then daily through release week. Always include link to full track in bio."
        )

        return {
            "release_id": release_id,
            "shorts_count": count,
            "shorts": shorts,
            "schedule_notes": schedule_notes,
            "hashtag_strategy": [
                f"#{track_name.replace(' ', '')}",
                f"#{artist_name.replace(' ', '')}",
                "#NewMusic",
                f"#NewMusic{CURRENT_YEAR}",
                "#Melodio",
            ],
        }

    # ----------------------------------------------------------------
    # optimize_seo
    # ----------------------------------------------------------------

    async def _optimize_seo(self, task: AgentTask) -> dict:
        p = task.payload
        artist_name = p.get("artist_name", "")
        track_name = p.get("track_name", "")
        video_type = p.get("video_type", "Official Music Video")
        genre = p.get("genre", "")
        comparable_artists = p.get("comparable_artists", [])
        listen_link = p.get("listen_link", "")
        instagram_handle = p.get("instagram_handle", "")
        tiktok_handle = p.get("tiktok_handle", "")

        # SEO title
        type_label = {
            "music_video_ai": "Official Music Video",
            "lyric_video": "Official Lyric Video",
            "visualizer": "Official Visualizer",
        }.get(video_type, "Official Music Video")
        title = f"{artist_name} - {track_name} ({type_label})"

        # Description (first 3 lines are key for SEO)
        description_lines = [
            f'"{track_name}" by {artist_name}',
        ]
        if listen_link:
            description_lines.append(f"Stream/Download: {listen_link}")
        if instagram_handle:
            description_lines.append(f"Follow {artist_name}: Instagram @{instagram_handle}")
        if tiktok_handle:
            description_lines.append(f"TikTok @{tiktok_handle}")

        description_lines.extend([
            "",
            f"© {CURRENT_YEAR} Melodio. All rights reserved.",
            "Distributed by Melodio Distribution.",
        ])

        description = "\n".join(description_lines)

        # Tags (15-20)
        tags = [
            artist_name,
            track_name,
            f"{artist_name} {track_name}",
            type_label.lower(),
            genre,
            f"new {genre} {CURRENT_YEAR}",
            f"official music video {CURRENT_YEAR}",
            "new music",
            f"new music {CURRENT_YEAR}",
            "Melodio music",
            "Melodio records",
        ]

        for comp in comparable_artists[:4]:
            tags.append(comp)
            tags.append(f"{comp} type beat")

        # Remove blanks, deduplicate, cap at 20
        tags = list(dict.fromkeys([t for t in tags if t]))[:20]

        return {
            "title": title,
            "description": description,
            "tags": tags,
            "tag_count": len(tags),
            "seo_score_estimate": "optimized" if len(tags) >= 15 and listen_link else "needs_links",
        }

    # ----------------------------------------------------------------
    # schedule_premiere
    # ----------------------------------------------------------------

    async def _schedule_premiere(self, task: AgentTask) -> dict:
        p = task.payload
        release_id = p.get("release_id") or task.release_id
        release_date_str = p.get("release_date")
        artist_name = p.get("artist_name", "")
        track_name = p.get("track_name", "")

        if release_date_str:
            try:
                premiere_time = datetime.fromisoformat(str(release_date_str).replace("Z", "+00:00"))
            except Exception:
                premiere_time = datetime.now(timezone.utc) + timedelta(days=7)
        else:
            premiere_time = datetime.now(timezone.utc) + timedelta(days=7)

        # Premiere goes live at release time
        premiere_config = {
            "premiere_type": "music_video",
            "scheduled_start": premiere_time.isoformat(),
            "countdown_hours": 24,
            "live_chat_enabled": True,
            "auto_chapters": True,
            "premiere_title": f"{artist_name} - {track_name} (World Premiere)",
            "premiere_message": (
                f"🎬 World Premiere: {track_name} by {artist_name}\n"
                f"Join us for the live premiere — drop a 🔥 in the chat!"
            ),
            "pre_premiere_posts": [
                {"hours_before": 24, "message": f"TOMORROW: {track_name} premieres on YouTube. Set your reminder 🔔"},
                {"hours_before": 1, "message": f"1 HOUR until the {track_name} premiere drops. Link in bio."},
            ],
        }

        if release_id:
            await self.db_execute(
                "UPDATE releases SET youtube_url = $2, updated_at = NOW() WHERE id = $1::uuid AND youtube_url IS NULL",
                release_id,
                f"premiere_scheduled_{premiere_time.strftime('%Y%m%d')}",
            )

        return {
            "release_id": release_id,
            "premiere_config": premiere_config,
            "scheduled_at": premiere_time.isoformat(),
            "status": "premiere_scheduled",
        }

    # ----------------------------------------------------------------
    # generate_thumbnail_brief
    # ----------------------------------------------------------------

    async def _generate_thumbnail_brief(self, task: AgentTask) -> dict:
        p = task.payload
        artist_name = p.get("artist_name", "")
        track_name = p.get("track_name", "")
        video_type = p.get("video_type", "music_video")
        mood = p.get("mood", "")
        artwork_url = p.get("artwork_url", "")

        brief = {
            "dimensions": "1280x720px (16:9)",
            "file_format": "JPG, max 2MB",
            "text_overlay": f"{artist_name.upper()} — {track_name.upper()}",
            "text_requirements": "High contrast, readable at 300px. No more than 6 words. Use Impact or bold sans-serif.",
            "visual_concept": (
                f"Thumbnail for {video_type.replace('_', ' ')} — {artist_name}: {track_name}. "
                f"Should feel {'cinematic and dramatic' if mood == 'dark' else 'vibrant and energetic'}. "
                f"Feature artist prominently if photo available. Derive color palette from: {artwork_url or 'track artwork'}."
            ),
            "ctr_principles": [
                "High contrast between subject and background",
                "Emotion visible on face (if person present)",
                "Bold text with drop shadow",
                "Rule of thirds composition",
                "Avoid cluttered layouts",
            ],
            "a_b_variants": 2,
        }

        await self.send_message("creative", "thumbnail_brief", {
            "brief": brief,
            "artist_name": artist_name,
            "track_name": track_name,
        })

        return {
            "brief": brief,
            "artist_name": artist_name,
            "track_name": track_name,
            "sent_to_creative": True,
        }

    # ----------------------------------------------------------------
    # seed_reaction_channels
    # ----------------------------------------------------------------

    async def _seed_reaction_channels(self, task: AgentTask) -> dict:
        p = task.payload
        genre = (p.get("genre") or "").lower()
        release_id = p.get("release_id") or task.release_id
        artist_name = p.get("artist_name", "")
        track_name = p.get("track_name", "")
        youtube_url = p.get("youtube_url", "")

        # Filter channels by genre relevance
        if genre:
            matched = [
                ch for ch in REACTION_CHANNELS
                if any(g in genre or genre in g for g in ch["genre_focus"])
            ]
            if not matched:
                matched = REACTION_CHANNELS[:5]  # Fallback to top 5
        else:
            matched = REACTION_CHANNELS

        outreach_list = []
        for ch in matched:
            outreach = {
                "channel": ch["channel"],
                "subscribers": ch["subs_estimate"],
                "genre_focus": ch["genre_focus"],
                "outreach_status": "pending",
                "message_template": (
                    f"Hey! Thought you might enjoy reacting to {artist_name} - {track_name}. "
                    f"Just dropped — {youtube_url}. "
                    f"Would love to see your reaction. DM for exclusive access or early content."
                ),
            }
            outreach_list.append(outreach)

        # Delegate outreach messages to Comms agent
        await self.send_message("comms", "send_outreach_batch", {
            "type": "reaction_seeding",
            "release_id": release_id,
            "channels": outreach_list,
            "artist_name": artist_name,
            "track_name": track_name,
        })

        await self.log_audit("reaction_seeding", "releases", release_id, {
            "channels_targeted": len(outreach_list),
            "genre": genre,
        })

        return {
            "release_id": release_id,
            "channels_targeted": len(outreach_list),
            "outreach_list": outreach_list,
            "genre_matched": genre,
            "delegated_to_comms": True,
        }

    # ----------------------------------------------------------------
    # Hero Skills
    # ----------------------------------------------------------------

    async def _task_algorithm_whisper(self, task: AgentTask) -> dict:
        """Algorithm Whisperer — scores and optimises a YouTube video for the algorithm."""
        p = task.payload
        artist_id = p.get("artist_id") or task.artist_id
        video_url = p.get("video_url", "")
        video_title = p.get("video_title", "")
        genre = (p.get("genre") or "pop").lower()

        artist = None
        if artist_id:
            artist = await self.db_fetchrow("SELECT name, genre FROM artists WHERE id = $1::uuid", artist_id)

        artist_name = (artist["name"] if artist else "") or p.get("artist_name", "")
        artist_genre = (artist["genre"] if artist else None) or genre

        # ---- Title scoring ----
        title_len = len(video_title)
        title_score = 0
        title_feedback = []

        if 50 <= title_len <= 70:
            title_score += 35
        elif 40 <= title_len < 50 or 70 < title_len <= 80:
            title_score += 20
            title_feedback.append(f"Title is {title_len} chars — aim for 50-70")
        else:
            title_score += 5
            title_feedback.append(f"Title too {'short' if title_len < 40 else 'long'} ({title_len} chars)")

        if video_title and artist_name and artist_name.lower() in video_title[:30].lower():
            title_score += 20
        elif video_title:
            title_score += 10
            title_feedback.append("Place artist name within the first 30 characters")

        power_words = ["official", "music video", "lyric video", "visualizer", "premiere",
                       "ft.", "feat.", str(CURRENT_YEAR)]
        power_hits = sum(1 for w in power_words if w.lower() in video_title.lower())
        title_score += min(25, power_hits * 8)

        if "(" in video_title or "[" in video_title:
            title_score += 10
        else:
            title_feedback.append("Add context in parentheses e.g. (Official Music Video)")

        title_score = min(100, title_score)

        # ---- SEO & clickbait scores ----
        seo_score = min(100, int(title_score * 0.5 + 30))
        click_bait_score = min(100, int(title_score * 0.6 + 20))

        # ---- Retention prediction ----
        _retention_benchmarks = {
            "hip-hop": 42, "pop": 45, "electronic": 38, "r&b": 47,
            "rock": 44, "classical": 35, "jazz": 40, "indie": 43,
        }
        base_retention = next(
            (v for k, v in _retention_benchmarks.items() if k in artist_genre.lower()), 43
        )
        retention_prediction = min(70, base_retention + (title_score - 50) // 10)

        # ---- Optimised title ----
        if video_title and title_score < 80:
            optimized_title = video_title
            if "(" not in optimized_title and "[" not in optimized_title:
                optimized_title = f"{optimized_title} (Official Music Video)"
            if artist_name and artist_name.lower() not in optimized_title[:30].lower():
                optimized_title = f"{artist_name} - {optimized_title}"
            if len(optimized_title) > 80:
                optimized_title = optimized_title[:77] + "..."
        else:
            optimized_title = video_title or f"{artist_name} - [Track Title] (Official Music Video)"

        # ---- Tag strategy: 5 broad + 10 specific + 5 long-tail ----
        _genre_tags = {
            "hip-hop": ["hip hop", "rap music", "new hip hop", "hip hop 2026", "rap 2026"],
            "pop": ["pop music", "new pop", "pop 2026", "pop hits", "popular music"],
            "r&b": ["r&b music", "new r&b", "r&b 2026", "rnb", "soul music"],
            "electronic": ["electronic music", "edm", "electronic 2026", "dance music", "beats"],
            "rock": ["rock music", "new rock", "rock 2026", "guitar", "indie rock"],
        }
        genre_key = next((k for k in _genre_tags if k in artist_genre.lower()), None)
        broad_tags = _genre_tags.get(genre_key, ["new music", "music 2026", "official music video", "musician", "artist"])

        specific_tags: list = []
        if artist_name:
            specific_tags += [artist_name, f"{artist_name} music", f"{artist_name} official"]
        if video_title:
            track_part = video_title.split(" - ")[-1].split("(")[0].strip()
            if track_part:
                specific_tags += [track_part, f"{artist_name} {track_part}".strip()]
        specific_tags += [
            f"new {artist_genre} music", f"{artist_genre} artist", f"official video {CURRENT_YEAR}",
            f"{artist_genre} {CURRENT_YEAR}", f"Melodio {artist_genre}",
        ]
        specific_tags = specific_tags[:10]

        long_tail_tags = [
            f"best new {artist_genre} {CURRENT_YEAR}",
            f"{artist_genre} music video {CURRENT_YEAR}",
            f"emerging {artist_genre} artist",
            f"new {artist_genre} song",
            f"Melodio music {artist_genre}",
        ]

        tag_strategy = list(dict.fromkeys(
            t for t in (broad_tags[:5] + specific_tags + long_tail_tags[:5]) if t
        ))

        # ---- Description template ----
        description_template = (
            f'"{video_title or "[Track Title]"}" by {artist_name or "[Artist Name]"}\n'
            f"Stream/Download: [LINK IN BIO]\n"
            f"Follow {artist_name or '[Artist]'} on Instagram: @[handle] | TikTok: @[handle]\n\n"
            f"[CHAPTERS — improves retention & SEO]\n"
            f"0:00 Intro\n0:30 Verse 1\n1:00 Chorus\n[...]\n\n"
            f"[Tip: first 125 chars are critical — include genre + year + artist name above]\n\n"
            f"© {CURRENT_YEAR} Melodio. All rights reserved.\n"
            f"Distributed by Melodio Distribution."
        )

        # ---- Genre-based upload timing ----
        _upload_timing = {
            "hip-hop": {"best_days": ["Thursday", "Friday"], "best_hour_et": "2pm–4pm", "reason": "Friday streaming surge"},
            "pop": {"best_days": ["Friday", "Thursday"], "best_hour_et": "10am–12pm", "reason": "Afternoon discovery peak"},
            "r&b": {"best_days": ["Friday", "Saturday"], "best_hour_et": "3pm–5pm", "reason": "Weekend chill session peak"},
            "electronic": {"best_days": ["Friday", "Saturday"], "best_hour_et": "4pm–6pm", "reason": "Pre-weekend energy"},
            "rock": {"best_days": ["Thursday", "Friday"], "best_hour_et": "12pm–2pm", "reason": "Lunch discovery window"},
        }
        timing = _upload_timing.get(
            next((k for k in _upload_timing if k in artist_genre.lower()), None),
            {"best_days": ["Friday", "Thursday"], "best_hour_et": "2pm–4pm", "reason": "General peak discovery window"},
        )

        upload_blueprint = {
            "upload_timing": timing,
            "thumbnail_tips": [
                "High contrast — subject vs background (aim for 3:1 contrast ratio)",
                "Visible emotion on face if artist is present",
                "Bold text overlay — max 4 words, Impact or bold sans-serif",
                "Test 2 A/B variants for first 48 hours",
                "Avoid red/green combination (colorblind accessibility)",
            ],
            "description_first_125_chars": (
                f'"{video_title or "[Track]"}" by {artist_name} — '
                f"Official {artist_genre.title()} Music Video. Stream now: [link]"
            ),
            "end_screen_strategy": "Add at 20s before end: 2 video cards + subscribe button",
            "cards_strategy": "Add playlist card at 30% runtime + channel card at 60% runtime",
            "premiere_recommended": True,
            "community_post_schedule": [
                "48h before: teaser still",
                "24h before: countdown post",
                "Launch day: share button push",
            ],
        }

        logger.info(f"[YouTube] Algorithm whisper for {artist_name}: seo={seo_score}, title_score={title_score}")
        return {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "video_url": video_url,
            "video_title_analyzed": video_title,
            "seo_score": seo_score,
            "click_bait_score": click_bait_score,
            "retention_prediction": retention_prediction,
            "title_score": title_score,
            "title_feedback": title_feedback,
            "optimized_title": optimized_title,
            "tag_strategy": tag_strategy,
            "description_template": description_template,
            "upload_blueprint": upload_blueprint,
            "hero_skill": "algorithm_whisperer",
        }

    # ----------------------------------------------------------------
    # Legacy handlers
    # ----------------------------------------------------------------

    async def _upload_video(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow("SELECT title FROM releases WHERE id = $1::uuid", release_id)
        title = release["title"] if release else "New Release"
        youtube_url = f"https://youtube.com/watch?v=placeholder_{(release_id or 'new')[:8]}"
        await self.db_execute(
            "UPDATE releases SET youtube_url = $2, updated_at = NOW() WHERE id = $1::uuid",
            release_id, youtube_url,
        )
        return {"release_id": release_id, "youtube_url": youtube_url, "status": "uploaded"}

    async def _enable_monetization(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        return {"release_id": release_id, "monetization": "enabled", "ad_formats": ["overlay", "skippable"]}

    async def _create_short(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        duration = task.payload.get("clip_duration_seconds", 30)
        return {"release_id": release_id, "short_created": True, "duration": duration, "status": "processing"}

    async def _content_id_claim(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        return {"track_id": track_id, "content_id_registered": True, "policy": "monetize"}

    async def _channel_report(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow("SELECT youtube_channel_id FROM artists WHERE id = $1::uuid", artist_id)
        return {
            "artist_id": artist_id,
            "channel_id": artist["youtube_channel_id"] if artist else None,
            "subscribers": 0,
            "views_30d": 0,
            "revenue_30d": 0.0,
        }

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[YouTube] Online — managing video content pipeline")
