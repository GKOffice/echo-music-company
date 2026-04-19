"""
Melodio Artist Growth Recommendation Engine
Generates personalized growth reports for artists using Claude AI.
"""

import json
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers.auth import get_current_user, TokenData

logger = logging.getLogger(__name__)

router = APIRouter()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

GROWTH_SYSTEM_PROMPT = """You are the Growth Strategy Engine at Melodio, an autonomous AI music company with 21 specialized agents.

Your job: Generate a brutally honest, personalized growth report for an artist.
- Analyze whatever data is available — do NOT fabricate metrics
- Score strengths and gaps honestly (0-100 per area)
- Map every gap to a specific Melodio agent that fixes it
- Generate concrete, actionable steps

Scoring areas:
- Platform Presence: DSP availability, branding consistency
- Release Strategy: cadence, timing, catalog depth
- Fanbase Quality: engagement rate, not just follower count
- Live Performance: touring, show history
- Sync Readiness: instrumentals, metadata, licensing readiness
- Social Media: content quality, posting consistency, growth rate
- Revenue Diversification: merch, sync, live, points, royalties

Tier thresholds:
- Emerging: 0-49
- Rising: 50-74
- Breaking: 75-89
- Established: 90+

You MUST return valid JSON matching this exact structure (no markdown, no commentary):
{
  "artist_name": str,
  "overall_score": int,
  "tier": str,
  "strengths": [{"area": str, "score": int, "detail": str}],
  "gaps": [{"area": str, "score": int, "detail": str, "fixable": bool}],
  "melodio_action_plan": {
    "immediate": [{"action": str, "agent": str, "what_we_do": str, "your_result": str, "auto": bool}],
    "week_1_to_4": [{"action": str, "agent": str, "what_we_do": str, "your_result": str, "auto": bool}],
    "month_2_to_6": [{"action": str, "agent": str, "what_we_do": str, "your_result": str, "auto": bool}],
    "artist_action_steps": [{"step": int, "action": str, "why": str, "time": str}]
  },
  "melodio_advantage": {
    "agents_working_for_you": 21,
    "estimated_monthly_value": str,
    "what_you_pay": "Nothing upfront — we invest in you",
    "revenue_split": "60% to you, always",
    "masters": "Revert to you in 5 years",
    "contract": "1 song at a time — leave whenever you want"
  },
  "hero_skill": "artist_growth_report"
}

IMPORTANT:
- Be honest about gaps — artists respect honesty over flattery
- Every gap must have fixable=true and map to a real Melodio agent
- Action plan must be personalized to the artist's genre and goals
- Include at least 3 strengths and 3 gaps
- Artist action steps should be specific and achievable (with time estimates)
"""


class GrowthReportRequest(BaseModel):
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    genre: Optional[str] = None
    social_links: Optional[dict] = None
    streams_estimate: Optional[str] = None
    goals: Optional[list] = None


def _build_fallback_report(name: str, genre: str, goals: list, social_links: dict, streams: str) -> dict:
    """Template-based report when Claude is unavailable."""
    has_spotify = bool(social_links.get("spotify"))
    has_instagram = bool(social_links.get("instagram"))
    has_youtube = bool(social_links.get("youtube"))
    has_tiktok = bool(social_links.get("tiktok"))
    platform_count = sum([has_spotify, has_instagram, has_youtube, has_tiktok])

    platform_score = min(80, 30 + platform_count * 12)
    release_score = 45
    fanbase_score = 35
    live_score = 20
    sync_score = 40
    social_score = min(70, 25 + platform_count * 11)
    revenue_score = 30

    overall = int(
        platform_score * 0.20 + release_score * 0.15 + fanbase_score * 0.20
        + live_score * 0.10 + sync_score * 0.10 + social_score * 0.15 + revenue_score * 0.10
    )

    tier = "Emerging" if overall < 50 else "Rising" if overall < 75 else "Breaking" if overall < 90 else "Established"

    strengths = []
    gaps = []

    if platform_score >= 50:
        strengths.append({"area": "Platform Presence", "score": platform_score, "detail": f"Active on {platform_count} platforms — solid foundation for distribution"})
    else:
        gaps.append({"area": "Platform Presence", "score": platform_score, "detail": "Limited platform presence — need to establish on more DSPs and social channels", "fixable": True})

    if social_score >= 50:
        strengths.append({"area": "Social Media", "score": social_score, "detail": "Social accounts connected — ready for coordinated campaign strategies"})
    else:
        gaps.append({"area": "Social Media", "score": social_score, "detail": "Social presence needs growth — consistent content and engagement strategy required", "fixable": True})

    strengths.append({"area": "Genre Focus", "score": 65, "detail": f"{genre or 'Your genre'} is a growing market with strong playlist ecosystem"})

    if goals:
        strengths.append({"area": "Goal Clarity", "score": 70, "detail": f"Clear career goals defined: {', '.join(goals[:2])}. This drives focused agent strategy"})

    gaps.extend([
        {"area": "Fanbase Quality", "score": fanbase_score, "detail": "Followers exist but engagement rate needs improvement — quality over quantity", "fixable": True},
        {"area": "Live Performance", "score": live_score, "detail": "No live data found — this limits booking potential and fan connection", "fixable": True},
        {"area": "Sync Readiness", "score": sync_score, "detail": "Missing instrumental versions and metadata for sync pitching", "fixable": True},
        {"area": "Revenue Diversification", "score": revenue_score, "detail": "Revenue concentrated in streaming — need merch, sync, and points income", "fixable": True},
    ])

    return {
        "artist_name": name or "Artist",
        "overall_score": overall,
        "tier": tier,
        "strengths": strengths[:4],
        "gaps": gaps[:5],
        "melodio_action_plan": {
            "immediate": [
                {
                    "action": "Distribution Optimization",
                    "agent": "Distribution Agent",
                    "what_we_do": "Submit your catalog to 150+ DSPs with optimized metadata, ISRC codes, and release timing",
                    "your_result": "Your music available everywhere within 48 hours",
                    "auto": True,
                },
                {
                    "action": "Playlist Infiltrator activated",
                    "agent": "Distribution Agent",
                    "what_we_do": "AI analyzes editorial playlist patterns and pitches your tracks at optimal timing",
                    "your_result": "Higher chance of editorial playlist placement",
                    "auto": True,
                },
                {
                    "action": "Brand Identity Generation",
                    "agent": "Creative Agent — Brand Oracle",
                    "what_we_do": "Generate your complete visual identity: color palette, typography, social templates",
                    "your_result": "Professional branding across all platforms in 24 hours",
                    "auto": True,
                },
            ],
            "week_1_to_4": [
                {
                    "action": "Fan Engagement Campaign",
                    "agent": "Marketing Agent — ROAS Oracle",
                    "what_we_do": "Design and run targeted ad campaigns with predicted ROI before spending",
                    "your_result": "Grow real fans, not just numbers. Projected 500-2000 new engaged listeners",
                    "auto": True,
                },
                {
                    "action": "Press & Coverage Push",
                    "agent": "PR Agent — Coverage Predictor",
                    "what_we_do": "Score your pitch likelihood per outlet tier, target the ones most likely to cover you",
                    "your_result": "First press feature within 30 days",
                    "auto": True,
                },
                {
                    "action": "YouTube Algorithm Optimization",
                    "agent": "YouTube Agent — Algorithm Whisperer",
                    "what_we_do": "Optimize titles, thumbnails, descriptions, tags for maximum YouTube discovery",
                    "your_result": "Higher click-through rate and better algorithmic recommendations",
                    "auto": True,
                },
            ],
            "month_2_to_6": [
                {
                    "action": "Sync Pitching",
                    "agent": "Sync Agent — Placement Matchmaker",
                    "what_we_do": "Match your songs to film/TV/ad opportunities based on mood, tempo, and genre",
                    "your_result": "Passive income from sync placements ($500-$50,000 per placement)",
                    "auto": True,
                },
                {
                    "action": "Royalty Collection Worldwide",
                    "agent": "Finance Agent — Royalty Auditor",
                    "what_we_do": "Register with 60+ PROs worldwide, audit every DSP statement, flag underpayments",
                    "your_result": "Never miss a dollar. 90% of revenue goes to you.",
                    "auto": True,
                },
                {
                    "action": "Melodio Points Drop",
                    "agent": "Vault Agent — Points Demand Engine",
                    "what_we_do": "Let fans buy fractional royalty rights on your songs — predicts demand and optimal pricing",
                    "your_result": "Upfront revenue from fans who believe in you + quarterly royalty sharing",
                    "auto": True,
                },
            ],
            "artist_action_steps": [
                {"step": 1, "action": "Upload 3 best tracks to your Melodio artist dashboard", "why": "Our A&R Agent needs material to score and build your Melodio Score", "time": "10 minutes"},
                {"step": 2, "action": "Connect your Spotify, Instagram, and YouTube accounts", "why": "Feeds real data into our Analytics Agent for accurate growth tracking", "time": "5 minutes"},
                {"step": 3, "action": "Write a 2-sentence artist bio and set your genre", "why": "Our PR Agent and Comms Agent tailor all outreach to your voice", "time": "5 minutes"},
                {"step": 4, "action": "Set your top 3 career goals", "why": "Career GPS builds your personalized 12-month roadmap based on YOUR goals", "time": "3 minutes"},
                {"step": 5, "action": "Create instrumental versions of your top tracks", "why": "Doubles your sync licensing potential — instrumentals are preferred for film/TV", "time": "Your pace"},
            ],
        },
        "melodio_advantage": {
            "agents_working_for_you": 21,
            "estimated_monthly_value": "$3,000-5,000",
            "what_you_pay": "Nothing upfront — we invest in you",
            "revenue_split": "60% to you, always",
            "masters": "Revert to you in 5 years",
            "contract": "1 song at a time — leave whenever you want",
        },
        "hero_skill": "artist_growth_report",
    }


@router.get("/report")
async def get_growth_report_status(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get current artist growth summary (quick read)."""
    result = await db.execute(
        text("SELECT name, genre, streams_total, revenue_total FROM artists WHERE user_id = :uid LIMIT 1"),
        {"uid": current_user.user_id},
    )
    artist = result.mappings().fetchone()
    return {
        "status": "ok",
        "artist": dict(artist) if artist else None,
        "message": "POST /api/v1/growth/report with artist details to generate a full AI growth report",
    }


@router.post("/report")
async def generate_growth_report(
    req: GrowthReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Generate a personalized artist growth report."""
    artist_name = req.artist_name or ""
    genre = req.genre or ""
    social_links = req.social_links or {}
    streams_estimate = req.streams_estimate or "unknown"
    goals = req.goals or []

    # If artist_id provided, pull data from DB
    if req.artist_id:
        result = await db.execute(
            text("SELECT * FROM artists WHERE id = :id"),
            {"id": req.artist_id},
        )
        artist = result.mappings().fetchone()
        if not artist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")
        artist_name = artist_name or artist.get("name", "")
        genre = genre or artist.get("genre", "")

    if not artist_name:
        # Try to get from user's own artist profile
        result = await db.execute(
            text("SELECT name, genre FROM artists WHERE user_id = :uid LIMIT 1"),
            {"uid": current_user.user_id},
        )
        own_artist = result.mappings().fetchone()
        if own_artist:
            artist_name = artist_name or own_artist.get("name", "")
            genre = genre or own_artist.get("genre", "")

    if not artist_name:
        artist_name = current_user.email.split("@")[0].title() if hasattr(current_user, "email") and current_user.email else "New Artist"

    # Try Claude AI generation
    if ANTHROPIC_API_KEY:
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

            user_prompt = f"""Generate a growth report for this artist:

Artist Name: {artist_name}
Genre: {genre or 'Not specified'}
Social Links: {json.dumps(social_links) if social_links else 'None provided'}
Estimated Streams: {streams_estimate}
Career Goals: {json.dumps(goals) if goals else 'Not specified'}

Based on what's provided, generate an honest, personalized growth report.
If data is limited, acknowledge that and base the report on the genre and goals.
Return ONLY valid JSON — no markdown fences, no commentary."""

            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                system=GROWTH_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            text_response = response.content[0].text.strip()
            # Extract JSON
            start = text_response.find("{")
            end = text_response.rfind("}") + 1
            if start >= 0 and end > start:
                report = json.loads(text_response[start:end])
                # Ensure required fields
                report.setdefault("hero_skill", "artist_growth_report")
                report.setdefault("melodio_advantage", {
                    "agents_working_for_you": 21,
                    "estimated_monthly_value": "$3,000-5,000",
                    "what_you_pay": "Nothing upfront — we invest in you",
                    "revenue_split": "60% to you, always",
                    "masters": "Revert to you in 5 years",
                    "contract": "1 song at a time — leave whenever you want",
                })
                return report

        except Exception as e:
            logger.error(f"[Growth] Claude generation failed: {e}")

    # Fallback to template
    return _build_fallback_report(artist_name, genre, goals, social_links, streams_estimate)
