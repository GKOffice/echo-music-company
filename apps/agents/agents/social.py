"""
Social Media Agent
Posts daily content across TikTok/Instagram/YouTube/Twitter per artist,
monitors trends, responds to comments, and detects UGC.
"""

import json
import logging
import os
from datetime import datetime, timezone

import httpx

from anthropic import AsyncAnthropic
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Content pillar weights: 40% music, 25% BTS, 15% fan, 10% trending, 10% promo
CONTENT_PILLARS = ["music", "bts", "fan_engagement", "trending", "promo"]
PILLAR_WEIGHTS = [0.40, 0.25, 0.15, 0.10, 0.10]

CAPTION_TEMPLATES = {
    "release": "🚨 {track_name} is OUT NOW 🚨\n{snippet}\n{link}",
    "snippet_tease": "{snippet}\nName this vibe 👇",
    "milestone": "{streams}M streams on {track} 🎉 Thank you for real.",
    "fan_engagement": "What's your favorite track off {album}? Wrong answers only 😂",
    "bts": "Studio sessions been different lately 🎛️ {detail}",
    "promo": "🔥 {track_name} — streaming everywhere now. Link in bio.",
}

RELEASE_DAY_SCHEDULE = [
    {"hour": 0, "platform": "all", "type": "midnight_drop", "caption_key": "release"},
    {"hour": 8, "platform": "instagram", "type": "morning_push", "caption_key": "release"},
    {"hour": 12, "platform": "tiktok", "type": "midday_snippet", "caption_key": "snippet_tease"},
    {"hour": 17, "platform": "twitter", "type": "streaming_push", "caption_key": "promo"},
    {"hour": 20, "platform": "instagram", "type": "evening_story", "caption_key": "fan_engagement"},
]

TRENDING_HASHTAGS_BY_GENRE = {
    "hip-hop": ["#hiphop", "#rap", "#newmusic", "#trapmusic", "#bars"],
    "pop": ["#pop", "#newmusic", "#popmusic", "#vibes", "#trending"],
    "r&b": ["#rnb", "#soul", "#newmusic", "#vibes", "#smoothgrooves"],
    "electronic": ["#edm", "#electronic", "#producer", "#newmusic", "#rave"],
    "default": ["#newmusic", "#music", "#vibes", "#nowplaying", "#streaming"],
}


class SocialAgent(BaseAgent):
    agent_id = "social"
    agent_name = "Social Agent"
    subscriptions = ["release.distributed", "marketing.campaign_started", "artist.signed"]

    def __init__(self):
        super().__init__()
        self.claude = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Social] Online. Managing social media for all artists.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "schedule_content": self._schedule_content,
            "post_release_day": self._post_release_day,
            "monitor_trends": self._monitor_trends,
            "engage_comments": self._engage_comments,
            "detect_ugc": self._detect_ugc,
            "generate_caption": self._generate_caption,
            "trend_surf": self._task_trend_surf,
            # legacy handlers kept for compatibility
            "create_content_calendar": self._create_content_calendar,
            "generate_post": self._generate_post,
            "schedule_post": self._schedule_content,
            "monitor_engagement": self._monitor_engagement,
            "tiktok_campaign": self._tiktok_campaign,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        payload = message.get("payload", {})
        if topic == "release.distributed":
            release_id = payload.get("release_id")
            artist_id = payload.get("artist_id")
            if release_id:
                await self.send_message("social", "post_release_day", {
                    "release_id": release_id,
                    "artist_id": artist_id,
                })

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _schedule_content(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        content_type = task.payload.get("content_type", "music")
        platform = task.payload.get("platform", "instagram")
        scheduled_at = task.payload.get("scheduled_at", datetime.now(timezone.utc).isoformat())

        artist = await self.db_fetchrow("SELECT name, genre FROM artists WHERE id = $1::uuid", artist_id)
        artist_name = artist["name"] if artist else "Artist"
        genre = artist["genre"] if artist else "default"

        caption_result = await self._generate_caption(AgentTask(
            task_id=task.task_id,
            task_type="generate_caption",
            payload={
                "artist_id": artist_id,
                "artist_name": artist_name,
                "content_type": content_type,
                "platform": platform,
            },
        ))
        caption = caption_result.get("caption", "")

        hashtags = TRENDING_HASHTAGS_BY_GENRE.get(genre.lower() if genre else "default",
                                                   TRENDING_HASHTAGS_BY_GENRE["default"])

        post = {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "platform": platform,
            "content_type": content_type,
            "caption": caption,
            "hashtags": hashtags[:5],
            "scheduled_at": scheduled_at,
            "status": "scheduled",
            "pillar": content_type,
        }
        logger.info(f"[Social] Scheduled {content_type} post for {artist_name} on {platform} at {scheduled_at}")
        return post

    async def _post_release_day(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        artist_id = task.payload.get("artist_id") or task.artist_id

        release = await self.db_fetchrow(
            "SELECT r.title, a.name, a.genre FROM releases r LEFT JOIN artists a ON r.artist_id = a.id WHERE r.id = $1::uuid",
            release_id,
        )
        if not release:
            return {"error": "Release not found", "release_id": release_id}

        track_name = release["title"]
        artist_name = release["name"]
        genre = release.get("genre") or "default"
        hashtags = TRENDING_HASHTAGS_BY_GENRE.get(genre.lower(), TRENDING_HASHTAGS_BY_GENRE["default"])

        posts = []
        for slot in RELEASE_DAY_SCHEDULE:
            template_key = slot["caption_key"]
            caption = CAPTION_TEMPLATES[template_key].format(
                track_name=track_name,
                artist=artist_name,
                snippet=f"The new {genre} record from {artist_name}",
                link="linktr.ee/echo",
                album=track_name,
                streams="",
                track=track_name,
                detail="",
            )
            platforms = ["instagram", "tiktok", "twitter", "youtube"] if slot["platform"] == "all" else [slot["platform"]]
            for p in platforms:
                posts.append({
                    "platform": p,
                    "type": slot["type"],
                    "caption": caption,
                    "hashtags": hashtags[:5],
                    "hour": slot["hour"],
                    "status": "queued",
                })

        logger.info(f"[Social] Release day blitz queued: {len(posts)} posts for '{track_name}' by {artist_name}")
        await self.log_audit("release_day_blitz", "releases", release_id, {"posts_queued": len(posts)})
        return {
            "release_id": release_id,
            "artist": artist_name,
            "track": track_name,
            "posts_queued": len(posts),
            "posts": posts,
        }

    async def _monitor_trends(self, task: AgentTask) -> dict:
        genre = task.payload.get("genre", "pop")
        platform = task.payload.get("platform", "tiktok")

        # In production, call TikTok/Instagram API; return structured opportunities
        trending_sounds = [
            {"sound": "Lo-fi Beat #42", "views_7d": 48_000_000, "fit_genres": ["pop", "r&b"]},
            {"sound": "Drill 808 Pack", "views_7d": 22_000_000, "fit_genres": ["hip-hop", "trap"]},
            {"sound": "Emotional Piano Loop", "views_7d": 15_000_000, "fit_genres": ["pop", "r&b", "indie"]},
        ]
        trending_hashtags = [
            {"tag": "#newmusic", "posts_7d": 5_200_000},
            {"tag": "#indiesound", "posts_7d": 890_000},
            {"tag": "#viralmusic", "posts_7d": 3_100_000},
        ]

        opportunities = []
        for sound in trending_sounds:
            if genre.lower() in sound["fit_genres"]:
                opportunities.append({
                    "type": "trending_sound",
                    "sound": sound["sound"],
                    "views": sound["views_7d"],
                    "action": "create_reaction_content",
                })

        logger.info(f"[Social] Trend scan on {platform}: {len(opportunities)} opportunities found")
        return {
            "platform": platform,
            "genre": genre,
            "trending_sounds": trending_sounds,
            "trending_hashtags": trending_hashtags,
            "opportunities": opportunities,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _engage_comments(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        comments = task.payload.get("comments", [
            {"id": "c1", "text": "This song is fire 🔥", "likes": 342},
            {"id": "c2", "text": "Can't stop listening", "likes": 211},
            {"id": "c3", "text": "When's the next drop?", "likes": 178},
        ])

        responses = []
        if self.claude:
            for comment in comments[:5]:
                try:
                    msg = await self.claude.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=100,
                        system=(
                            "You manage social media for an artist. Reply to fan comments in a genuine, "
                            "casual tone. Keep it short (1-2 sentences). No corporate speak. No emojis overload."
                        ),
                        messages=[{"role": "user", "content": f"Fan comment: {comment['text']}"}],
                    )
                    responses.append({
                        "comment_id": comment["id"],
                        "original": comment["text"],
                        "response": msg.content[0].text.strip(),
                    })
                except Exception as e:
                    logger.error(f"[Social] Claude comment error: {e}")
        else:
            default_responses = [
                "🔥🔥 appreciate that!", "This means everything fr",
                "More on the way, stay tuned 👀", "Love the support 🙏",
            ]
            for i, comment in enumerate(comments[:5]):
                responses.append({
                    "comment_id": comment["id"],
                    "original": comment["text"],
                    "response": default_responses[i % len(default_responses)],
                })

        logger.info(f"[Social] Generated {len(responses)} comment responses for artist {artist_id}")
        return {
            "artist_id": artist_id,
            "responses_generated": len(responses),
            "responses": responses,
            "sla_hours": 2,
        }

    async def _detect_ugc(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        track_name = task.payload.get("track_name", "")
        platforms = task.payload.get("platforms", ["tiktok", "instagram", "youtube"])

        # In production, call platform APIs to search hashtags/sounds
        mock_ugc = [
            {
                "platform": "tiktok",
                "user": "@musicfan99",
                "type": "cover",
                "url": f"https://tiktok.com/@musicfan99/video/123",
                "views": 45_000,
                "action": "repost",
            },
            {
                "platform": "instagram",
                "user": "@reactionking",
                "type": "reaction",
                "url": f"https://instagram.com/p/abc123",
                "views": 12_000,
                "action": "repost",
            },
        ]

        logger.info(f"[Social] UGC scan: found {len(mock_ugc)} fan posts for '{track_name}'")
        return {
            "artist_id": artist_id,
            "track_name": track_name,
            "platforms_scanned": platforms,
            "ugc_found": len(mock_ugc),
            "ugc_queue": mock_ugc,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _generate_caption(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist_name = task.payload.get("artist_name", "")
        content_type = task.payload.get("content_type", "music")
        platform = task.payload.get("platform", "instagram")
        track_name = task.payload.get("track_name", "the new track")
        album = task.payload.get("album", "the project")
        detail = task.payload.get("detail", "")

        if not artist_name and artist_id:
            row = await self.db_fetchrow("SELECT name FROM artists WHERE id = $1::uuid", artist_id)
            if row:
                artist_name = row["name"]

        if self.claude:
            try:
                prompt = (
                    f"Write a social media caption for {artist_name} for a {content_type} post on {platform}. "
                    f"Track: '{track_name}'. Keep it authentic, short, and engaging. "
                    f"Max 3 sentences. No hashtags (added separately). "
                    f"Match the energy of modern music artists on {platform}."
                )
                msg = await self.claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=150,
                    system="You write social media captions for music artists. Be authentic, not corporate.",
                    messages=[{"role": "user", "content": prompt}],
                )
                caption = msg.content[0].text.strip()
                return {"caption": caption, "source": "claude", "platform": platform, "content_type": content_type}
            except Exception as e:
                logger.error(f"[Social] Claude caption error: {e}")

        # Fallback templates
        template_map = {
            "music": CAPTION_TEMPLATES["release"],
            "bts": CAPTION_TEMPLATES["bts"],
            "fan_engagement": CAPTION_TEMPLATES["fan_engagement"],
            "trending": CAPTION_TEMPLATES["snippet_tease"],
            "promo": CAPTION_TEMPLATES["promo"],
            "release": CAPTION_TEMPLATES["release"],
        }
        template = template_map.get(content_type, CAPTION_TEMPLATES["release"])
        caption = template.format(
            track_name=track_name,
            artist=artist_name,
            snippet=f"New music from {artist_name}",
            link="linktr.ee/echo",
            album=album,
            streams="",
            track=track_name,
            detail=detail,
        )
        return {"caption": caption, "source": "template", "platform": platform, "content_type": content_type}

    # ----------------------------------------------------------------
    # Legacy handlers (kept for backward compatibility)
    # ----------------------------------------------------------------

    async def _create_content_calendar(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        posts = [
            {"day": -14, "type": "tease", "platforms": ["instagram", "tiktok"]},
            {"day": -7, "type": "snippet", "platforms": ["instagram", "tiktok", "twitter"]},
            {"day": -3, "type": "cover_reveal", "platforms": ["instagram"]},
            {"day": 0, "type": "release_day", "platforms": ["instagram", "tiktok", "twitter"]},
            {"day": 3, "type": "streaming_push", "platforms": ["instagram", "twitter"]},
            {"day": 7, "type": "milestone", "platforms": ["instagram", "tiktok"]},
        ]
        return {"release_id": release_id, "calendar": posts, "total_posts": len(posts)}

    async def _generate_post(self, task: AgentTask) -> dict:
        return await self._generate_caption(task)

    async def _monitor_engagement(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        return {
            "artist_id": artist_id,
            "instagram_engagement_rate": 0.0,
            "tiktok_views_7d": 0,
            "twitter_impressions_7d": 0,
            "status": "monitoring",
        }

    async def _tiktok_campaign(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        budget = task.payload.get("budget_usd", 500)
        return {"release_id": release_id, "tiktok_budget": budget, "status": "campaign_live"}

    # ----------------------------------------------------------------
    # Hero Skills
    # ----------------------------------------------------------------

    async def _task_trend_surf(self, task: AgentTask) -> dict:
        """Trend Surfer — identifies rising trends and generates content briefs."""
        artist_id = task.payload.get("artist_id") or task.artist_id
        genre = task.payload.get("genre", "pop")
        platforms = task.payload.get("platforms", ["tiktok", "instagram", "youtube"])

        artist = await self.db_fetchrow("SELECT name, genre FROM artists WHERE id = $1::uuid", artist_id)
        artist_name = artist["name"] if artist else ""
        artist_genre = (artist["genre"] if artist else None) or genre

        # Fetch iTunes RSS trending albums
        chart_entries = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://rss.applemarketingtools.com/api/v2/us/music/most-played/10/albums.json"
                )
                if resp.status_code == 200:
                    feed = resp.json().get("feed", {})
                    for entry in feed.get("results", []):
                        chart_entries.append({
                            "name": entry.get("name", ""),
                            "artist": entry.get("artistName", ""),
                            "genre": entry.get("genres", [{}])[0].get("name", "") if entry.get("genres") else "",
                        })
        except Exception as e:
            logger.warning(f"[Social] iTunes RSS fetch failed: {e}")

        # Identify rising genres from chart
        genre_counts: dict = {}
        for entry in chart_entries:
            g = entry.get("genre", "").lower()
            if g:
                genre_counts[g] = genre_counts.get(g, 0) + 1

        rising_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)

        # Infer trending formats from chart genres
        format_map = {
            "hip-hop/rap": "drill", "r&b/soul": "bedroom pop", "pop": "hyperpop",
            "alternative": "lo-fi beats", "electronic": "ambient beats",
            "country": "country pop", "latin": "reggaeton",
        }
        trending_formats = list({format_map[g] for g in genre_counts if g in format_map})
        if not trending_formats:
            trending_formats = ["lo-fi beats", "bedroom pop", "drill"]

        # Research-backed optimal post times per platform
        optimal_post_times = {
            "tiktok": {"best_days": ["Tuesday", "Thursday", "Friday"], "best_hours": ["7pm", "9pm", "11am"]},
            "instagram": {"best_days": ["Monday", "Wednesday", "Friday"], "best_hours": ["11am", "1pm", "7pm"]},
            "youtube": {"best_days": ["Thursday", "Friday", "Saturday"], "best_hours": ["2pm", "4pm", "8pm"]},
            "twitter": {"best_days": ["Wednesday", "Friday"], "best_hours": ["9am", "12pm", "5pm"]},
        }
        schedule = {p: optimal_post_times.get(p, optimal_post_times["instagram"]) for p in platforms}

        # Trend alignment score
        genre_lower = (artist_genre or "").lower()
        trend_score = 50
        for g, count in genre_counts.items():
            if g in genre_lower or genre_lower in g:
                trend_score = min(100, 50 + count * 15)
                break

        # Generate content briefs via Claude or fallback
        content_briefs = []
        if self.claude and chart_entries:
            try:
                chart_summary = ", ".join([f"{e['artist']} - {e['name']}" for e in chart_entries[:5]])
                prompt = (
                    f"Artist genre: {artist_genre}. Top chart entries right now: {chart_summary}. "
                    f"Trending formats: {', '.join(trending_formats)}. "
                    f"Generate 3 content ideas for a {artist_genre} artist. "
                    f"Each idea must have: format, hook, hashtags (list), platform. "
                    f"Return a JSON array of 3 objects."
                )
                msg = await self.claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=400,
                    system="You create viral social media content strategies for music artists. Be specific and platform-native.",
                    messages=[{"role": "user", "content": prompt}],
                )
                text = msg.content[0].text.strip()
                start, end = text.find("["), text.rfind("]") + 1
                if start >= 0 and end > start:
                    content_briefs = json.loads(text[start:end])
            except Exception as e:
                logger.error(f"[Social] Claude trend brief error: {e}")

        if not content_briefs:
            genre_hashtags = TRENDING_HASHTAGS_BY_GENRE.get(genre_lower, TRENDING_HASHTAGS_BY_GENRE["default"])
            content_briefs = [
                {
                    "format": "Trending Sound Overlay",
                    "hook": f"Use a top trending audio clip with your {artist_genre} aesthetic",
                    "hashtags": genre_hashtags[:3] + ["#trending", "#fyp"],
                    "platform": "tiktok",
                },
                {
                    "format": "Studio Reel",
                    "hook": "Behind-the-scenes production moment with caption referencing a current trend",
                    "hashtags": genre_hashtags[:3] + ["#bts", "#studio"],
                    "platform": "instagram",
                },
                {
                    "format": "Vertical Short",
                    "hook": f"30-second hook clip timed with trending {trending_formats[0]}",
                    "hashtags": genre_hashtags[:3] + ["#shorts", "#newmusic"],
                    "platform": "youtube",
                },
            ]

        rising_trends = [{"genre": g, "chart_appearances": c} for g, c in rising_genres[:5]]

        logger.info(f"[Social] Trend surf for {artist_name}: score={trend_score}, {len(rising_trends)} rising genres")
        return {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "trend_score": trend_score,
            "rising_trends": rising_trends,
            "trending_formats": trending_formats,
            "content_briefs": content_briefs,
            "optimal_schedule": schedule,
            "chart_entries_analyzed": len(chart_entries),
            "hero_skill": "trend_surfer",
        }
