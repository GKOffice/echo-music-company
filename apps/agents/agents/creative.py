"""
Creative Agent
Generates album artwork prompts, lyric video concepts, ad creatives,
brand kits, and merch designs. Validates platform artwork specs.
"""

import json
import logging
import os

from anthropic import AsyncAnthropic
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Platform artwork requirements
ARTWORK_SPECS = {
    "min_size_px": 3000,
    "formats": ["jpg", "jpeg", "png"],
    "color_mode": "RGB",
    "max_size_mb": 10,
    "thumbnail_readable_px": 300,
    "forbidden": ["urls", "social_handles", "pricing"],
}

# Brand color palettes by genre
GENRE_PALETTES = {
    "hip-hop": {"primary": "#1a1a2e", "accent": "#e94560", "text": "#f5f5f5", "vibe": "bold, urban, dark"},
    "pop": {"primary": "#ff6b9d", "accent": "#c44dff", "text": "#ffffff", "vibe": "vibrant, clean, energetic"},
    "r&b": {"primary": "#2d1b4e", "accent": "#c084fc", "text": "#fde68a", "vibe": "soulful, warm, luxe"},
    "electronic": {"primary": "#0f172a", "accent": "#00f5ff", "text": "#e2e8f0", "vibe": "futuristic, neon, dark"},
    "indie": {"primary": "#fef3c7", "accent": "#d97706", "text": "#1c1917", "vibe": "warm, organic, textured"},
    "default": {"primary": "#0a0a0f", "accent": "#8b5cf6", "text": "#f9fafb", "vibe": "dark, minimal, premium"},
}

FONT_PAIRINGS = {
    "hip-hop": {"display": "Bebas Neue", "body": "Inter"},
    "pop": {"display": "Playfair Display", "body": "DM Sans"},
    "r&b": {"display": "Cormorant Garamond", "body": "Lato"},
    "electronic": {"display": "Space Grotesk", "body": "Roboto Mono"},
    "indie": {"display": "Libre Baskerville", "body": "Source Sans Pro"},
    "default": {"display": "Syne", "body": "Inter"},
}


class CreativeAgent(BaseAgent):
    agent_id = "creative"
    agent_name = "Creative Agent"
    subscriptions = ["release.created", "artist.signed"]

    def __init__(self):
        super().__init__()
        self.claude = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Creative] Online. Visual identity engine active.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "generate_artwork": self._generate_artwork,
            "create_brand_kit": self._create_brand_kit,
            "generate_ad_creative": self._generate_ad_creative,
            "create_lyric_video": self._create_lyric_video,
            "design_merch": self._design_merch,
            "check_artwork_specs": self._check_artwork_specs,
            # legacy
            "artwork_review": self._artwork_review,
            "generate_artwork_brief": self._generate_artwork,
            "approve_artwork": self._approve_artwork,
            "brand_audit": self._brand_audit,
            "visual_assets": self._create_visual_assets,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _generate_artwork(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        artist_id = task.payload.get("artist_id") or task.artist_id
        genre = task.payload.get("genre", "")
        mood = task.payload.get("mood", "")
        title = task.payload.get("title", "")

        release = None
        if release_id:
            release = await self.db_fetchrow(
                "SELECT r.title, r.genre, a.name, a.genre AS artist_genre FROM releases r "
                "LEFT JOIN artists a ON r.artist_id = a.id WHERE r.id = $1::uuid",
                release_id,
            )

        if release:
            title = title or release.get("title", "")
            genre = genre or release.get("genre") or release.get("artist_genre") or "default"
            artist_name = release.get("name", "")
        else:
            artist_name = task.payload.get("artist_name", "")

        palette = GENRE_PALETTES.get(genre.lower() if genre else "default", GENRE_PALETTES["default"])
        vibe = mood or palette["vibe"]

        if self.claude:
            try:
                prompt_req = (
                    f"Generate a detailed AI image prompt for album cover art.\n"
                    f"Artist: {artist_name}, Title: '{title}', Genre: {genre}, Mood/vibe: {vibe}\n"
                    f"Color palette: primary {palette['primary']}, accent {palette['accent']}\n"
                    f"Requirements: 3000x3000px square, no text overlay, no URLs or handles, "
                    f"visually striking at thumbnail size.\n"
                    f"Return a single detailed prompt suitable for Midjourney or DALL-E 3."
                )
                msg = await self.claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=300,
                    system="You are a creative director specializing in music album artwork. Write vivid, detailed image generation prompts.",
                    messages=[{"role": "user", "content": prompt_req}],
                )
                ai_prompt = msg.content[0].text.strip()
            except Exception as e:
                logger.error(f"[Creative] Claude artwork error: {e}")
                ai_prompt = self._default_artwork_prompt(artist_name, title, genre, palette, vibe)
        else:
            ai_prompt = self._default_artwork_prompt(artist_name, title, genre, palette, vibe)

        concept = (
            f"Visual concept for '{title}' by {artist_name}: "
            f"A {vibe} composition using {palette['primary']} and {palette['accent']} tones. "
            f"Genre-forward {genre} aesthetic with strong thumbnail clarity."
        )

        await self.log_audit("generate_artwork", "releases", release_id, {"title": title, "genre": genre})
        return {
            "release_id": release_id,
            "title": title,
            "artist": artist_name,
            "genre": genre,
            "ai_prompt": ai_prompt,
            "concept": concept,
            "specs": {"size": "3000x3000px", "format": "JPG or PNG", "color_mode": "RGB", "max_mb": 10},
            "palette": palette,
            "status": "prompt_ready",
        }

    async def _create_brand_kit(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        genre = task.payload.get("genre", "default")

        artist = await self.db_fetchrow("SELECT name, genre FROM artists WHERE id = $1::uuid", artist_id)
        if artist:
            genre = genre or artist.get("genre") or "default"
            artist_name = artist["name"]
        else:
            artist_name = task.payload.get("artist_name", "Artist")

        palette = GENRE_PALETTES.get(genre.lower() if genre else "default", GENRE_PALETTES["default"])
        fonts = FONT_PAIRINGS.get(genre.lower() if genre else "default", FONT_PAIRINGS["default"])

        if self.claude:
            try:
                msg = await self.claude.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=400,
                    system="You create brand guidelines for music artists. Be specific and actionable.",
                    messages=[{"role": "user", "content": (
                        f"Create brand guidelines for {artist_name} ({genre} artist). "
                        f"Include: brand voice, visual direction, logo concept, do/don'ts. "
                        f"Keep it concise. Return as plain text guidelines."
                    )}],
                )
                brand_voice = msg.content[0].text.strip()
            except Exception as e:
                logger.error(f"[Creative] Claude brand kit error: {e}")
                brand_voice = f"{artist_name} brand voice: authentic, {palette['vibe']}, genre-forward."
        else:
            brand_voice = f"{artist_name} brand voice: authentic, {palette['vibe']}, genre-forward."

        brand_kit = {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "genre": genre,
            "colors": {
                "primary": palette["primary"],
                "accent": palette["accent"],
                "text": palette["text"],
                "background": "#0a0a0f",
            },
            "typography": {
                "display_font": fonts["display"],
                "body_font": fonts["body"],
                "weight_display": "700",
                "weight_body": "400",
            },
            "mood_board": palette["vibe"],
            "brand_voice": brand_voice,
            "logo_concept": f"Wordmark in {fonts['display']}, {palette['accent']} on dark background",
            "do": ["consistent color usage", "high-contrast visuals", "square assets for social"],
            "dont": ["clip art", "comic sans", "busy backgrounds that obscure text at thumbnail"],
        }

        await self.log_audit("create_brand_kit", "artists", artist_id, {"genre": genre})
        return brand_kit

    async def _generate_ad_creative(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        platform = task.payload.get("platform", "instagram")
        format_type = task.payload.get("format", "story")  # story, feed, banner

        size_map = {
            ("instagram", "story"): "1080x1920",
            ("instagram", "feed"): "1080x1080",
            ("tiktok", "story"): "1080x1920",
            ("youtube", "banner"): "2560x1440",
            ("meta", "feed"): "1200x628",
        }
        size = size_map.get((platform, format_type), "1080x1080")

        creatives = [
            {
                "variant": "A",
                "concept": "Artist photo center with track name bold overlay, accent color border",
                "size": size,
                "cta": "Stream Now",
                "text_overlay": "minimal — track name + artist only",
            },
            {
                "variant": "B",
                "concept": "Abstract waveform animation still with mood color gradient",
                "size": size,
                "cta": "Listen Now",
                "text_overlay": "none — pure visual",
            },
            {
                "variant": "C",
                "concept": "Lyric snippet in display font on dark background",
                "size": size,
                "cta": "Play Now",
                "text_overlay": "lyric quote + artist name",
            },
        ]

        return {
            "release_id": release_id,
            "platform": platform,
            "format": format_type,
            "size": size,
            "variants": creatives,
            "production_notes": "Export at 2x for retina. MP4 loop for video placements.",
        }

    async def _create_lyric_video(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        style = task.payload.get("style", "kinetic_typography")

        release = await self.db_fetchrow(
            "SELECT r.title, a.name, a.genre FROM releases r LEFT JOIN artists a ON r.artist_id = a.id WHERE r.id = $1::uuid",
            release_id,
        ) if release_id else None

        title = release["title"] if release else task.payload.get("title", "")
        artist_name = release["name"] if release else task.payload.get("artist_name", "")
        genre = release.get("genre") if release else "default"
        palette = GENRE_PALETTES.get(genre.lower() if genre else "default", GENRE_PALETTES["default"])

        concept = {
            "style": style,
            "resolution": "1920x1080 (16:9)",
            "fps": 24,
            "color_scheme": palette,
            "font": FONT_PAIRINGS.get(genre.lower() if genre else "default", FONT_PAIRINGS["default"])["display"],
            "animation_style": "words appear on beat, fade on phrase end",
            "background": f"Looping abstract visuals in {palette['primary']} tones",
            "text_treatment": f"Display font in {palette['text']}, highlight key words in {palette['accent']}",
            "intro": f"Artist name + track title — 3 seconds",
            "outro": f"ECHO logo + streaming platforms — 5 seconds",
            "tools": ["After Effects", "CapCut Pro", "DaVinci Resolve"],
        }

        return {
            "release_id": release_id,
            "title": title,
            "artist": artist_name,
            "lyric_video_concept": concept,
            "estimated_runtime": "match track duration",
            "deliverables": ["YouTube upload (1080p)", "Instagram Reel cut (60s max)", "TikTok cut (30s hook)"],
        }

    async def _design_merch(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        release_id = task.payload.get("release_id") or task.release_id
        item_type = task.payload.get("item_type", "tshirt")

        artist = await self.db_fetchrow("SELECT name, genre FROM artists WHERE id = $1::uuid", artist_id) if artist_id else None
        artist_name = artist["name"] if artist else task.payload.get("artist_name", "Artist")
        genre = (artist.get("genre") if artist else None) or "default"
        palette = GENRE_PALETTES.get(genre.lower(), GENRE_PALETTES["default"])

        designs = {
            "tshirt": {
                "front": f"Oversized artist name wordmark in {palette['accent']} on black",
                "back": f"Album title in small type + ECHO label mark",
                "colors": ["black", "vintage white"],
                "print": "screen print or DTG",
            },
            "hoodie": {
                "front": "Minimal logo left chest",
                "back": "Large album artwork graphic or lyric quote",
                "colors": ["black", "charcoal"],
                "print": "embroidery + screen print combo",
            },
            "poster": {
                "design": f"Album cover art expanded to {palette['vibe']} full bleed, 18x24in",
                "paper": "heavyweight matte 100lb",
                "limited_edition": True,
            },
            "hat": {
                "design": "Structured 6-panel, embroidered artist monogram",
                "colors": ["black", "cream"],
                "closure": "snapback",
            },
        }

        design = designs.get(item_type, designs["tshirt"])

        return {
            "artist_id": artist_id,
            "release_id": release_id,
            "item_type": item_type,
            "design_concept": design,
            "palette": palette,
            "production_notes": "Submit to print partner 3 weeks before sale date. Order minimum 50 units.",
        }

    async def _check_artwork_specs(self, task: AgentTask) -> dict:
        artwork_url = task.payload.get("artwork_url", "")
        width = task.payload.get("width", 0)
        height = task.payload.get("height", 0)
        file_format = task.payload.get("format", "").lower().strip(".")
        file_size_mb = task.payload.get("size_mb", 0.0)
        has_url = task.payload.get("has_url", False)
        has_handle = task.payload.get("has_handle", False)
        has_pricing = task.payload.get("has_pricing", False)

        issues = []
        if width < ARTWORK_SPECS["min_size_px"] or height < ARTWORK_SPECS["min_size_px"]:
            issues.append(f"Image too small: {width}x{height}px. Minimum: {ARTWORK_SPECS['min_size_px']}x{ARTWORK_SPECS['min_size_px']}px")
        if width != height:
            issues.append(f"Image must be square: {width}x{height}px")
        if file_format and file_format not in ARTWORK_SPECS["formats"]:
            issues.append(f"Invalid format: {file_format}. Must be JPG or PNG")
        if file_size_mb > ARTWORK_SPECS["max_size_mb"]:
            issues.append(f"File too large: {file_size_mb}MB. Maximum: {ARTWORK_SPECS['max_size_mb']}MB")
        if has_url:
            issues.append("Artwork must not contain URLs")
        if has_handle:
            issues.append("Artwork must not contain social handles")
        if has_pricing:
            issues.append("Artwork must not contain pricing information")

        passed = len(issues) == 0
        return {
            "artwork_url": artwork_url,
            "passed": passed,
            "issues": issues,
            "specs_checked": ARTWORK_SPECS,
        }

    # ----------------------------------------------------------------
    # Legacy handlers
    # ----------------------------------------------------------------

    async def _artwork_review(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow("SELECT artwork_url, title FROM releases WHERE id = $1::uuid", release_id)
        if not release:
            return {"error": "Release not found"}
        if not release.get("artwork_url"):
            return {"release_id": release_id, "approved": False, "reason": "No artwork uploaded"}
        return {"release_id": release_id, "approved": True, "artwork_url": release["artwork_url"]}

    async def _approve_artwork(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        artwork_url = task.payload.get("artwork_url")
        await self.db_execute(
            "UPDATE releases SET artwork_url = $2, updated_at = NOW() WHERE id = $1::uuid",
            release_id, artwork_url,
        )
        await self.log_audit("approve_artwork", "releases", release_id)
        return {"release_id": release_id, "artwork_approved": True}

    async def _brand_audit(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow("SELECT name, profile_photo_url, brand_guidelines_url FROM artists WHERE id = $1::uuid", artist_id)
        issues = []
        if not artist or not artist.get("profile_photo_url"):
            issues.append("Missing profile photo")
        if not artist or not artist.get("brand_guidelines_url"):
            issues.append("Missing brand guidelines")
        return {"artist_id": artist_id, "brand_issues": issues, "audit_passed": len(issues) == 0}

    async def _create_visual_assets(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        return {
            "release_id": release_id,
            "assets_created": ["instagram_square", "instagram_story", "twitter_header", "youtube_thumbnail"],
            "status": "pending_upload",
        }

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _default_artwork_prompt(self, artist_name: str, title: str, genre: str, palette: dict, vibe: str) -> str:
        return (
            f"Album cover art for '{title}' by {artist_name}. "
            f"Genre: {genre}. Visual style: {vibe}. "
            f"Color palette: deep background {palette['primary']}, accent highlights {palette['accent']}. "
            f"Abstract, evocative, no text, no faces required. "
            f"Cinematic lighting, high contrast, striking at small thumbnail size. "
            f"Square format 3000x3000px. --ar 1:1 --style raw --q 2"
        )
