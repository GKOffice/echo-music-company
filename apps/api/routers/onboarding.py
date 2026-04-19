import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, Dict, List

from database import get_db
from routers.auth import get_current_user, TokenData
from services.email import onboarding_welcome_email, demo_received_email

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    genre: Optional[str] = None
    photo_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    name: Optional[str] = None
    stage_name: Optional[str] = None

_PROFILE_UPDATE_ALLOWED = {"bio", "genre", "photo_url", "social_links", "name", "stage_name"}


class DemoUpload(BaseModel):
    title: str
    genre: Optional[str] = None
    audio_url: str


class ConnectSocials(BaseModel):
    spotify_url: Optional[str] = None
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_or_create_artist(db: AsyncSession, user_id: str):
    """Return artist row for user, creating a stub if none exists."""
    result = await db.execute(
        text("SELECT * FROM artists WHERE user_id = :uid"),
        {"uid": user_id},
    )
    artist = result.mappings().fetchone()
    if artist:
        return artist

    artist_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO artists (id, user_id, name, status, onboarding_step)
            VALUES (:id, :uid, '', 'prospect', 0)
        """),
        {"id": artist_id, "uid": user_id},
    )
    await db.commit()
    result = await db.execute(
        text("SELECT * FROM artists WHERE id = :id"),
        {"id": artist_id},
    )
    return result.mappings().fetchone()


async def _get_user_email(db: AsyncSession, user_id: str) -> Optional[str]:
    result = await db.execute(
        text("SELECT email FROM users WHERE id = :id"),
        {"id": user_id},
    )
    row = result.fetchone()
    return row.email if row else None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/profile")
async def update_profile(
    body: ProfileUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    artist = await _get_or_create_artist(db, current_user.user_id)

    updates = {}
    if body.bio is not None:
        updates["bio"] = body.bio
    if body.genre is not None:
        updates["genre"] = body.genre
    if body.photo_url is not None:
        updates["photo_url"] = body.photo_url
    if body.social_links is not None:
        updates["social_links"] = str(body.social_links).replace("'", '"')
    if body.name is not None:
        updates["name"] = body.name
    if body.stage_name is not None:
        updates["stage_name"] = body.stage_name

    if updates:
        # BUG FIX: whitelist column names before building dynamic SET clause
        updates = {k: v for k, v in updates.items() if k in _PROFILE_UPDATE_ALLOWED}
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = str(artist["id"])
        await db.execute(
            text(f"UPDATE artists SET {set_clause}, onboarding_step = GREATEST(COALESCE(onboarding_step, 0), 1), updated_at = NOW() WHERE id = :id"),
            updates,
        )
        await db.commit()

    email = await _get_user_email(db, current_user.user_id)
    if email:
        asyncio.create_task(onboarding_welcome_email(email, body.name or ""))

    return {"status": "ok", "message": "Profile updated", "onboarding_step": 1}


@router.post("/demo")
async def upload_demo(
    body: DemoUpload,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    artist = await _get_or_create_artist(db, current_user.user_id)
    artist_id = str(artist["id"])

    # Get user email for submission record
    email = await _get_user_email(db, current_user.user_id)

    submission_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO submissions (id, artist_name, email, genre, audio_url, channel, created_at)
            VALUES (:id, :artist_name, :email, :genre, :audio_url, 'onboarding', NOW())
        """),
        {
            "id": submission_id,
            "artist_name": body.title,
            "email": email,
            "genre": body.genre,
            "audio_url": body.audio_url,
        },
    )
    await db.execute(
        text("UPDATE artists SET onboarding_step = GREATEST(COALESCE(onboarding_step, 0), 3), updated_at = NOW() WHERE id = :id"),
        {"id": artist_id},
    )
    await db.commit()

    if email:
        asyncio.create_task(demo_received_email(email, body.title))

    return {"status": "ok", "submission_id": submission_id, "onboarding_step": 3}


@router.get("/status")
async def onboarding_status(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT id, name, bio, genre, photo_url, social_links,
                   spotify_url, instagram_url, youtube_url,
                   COALESCE(onboarding_step, 0) as onboarding_step,
                   COALESCE(onboarding_complete, false) as onboarding_complete
            FROM artists WHERE user_id = :uid
        """),
        {"uid": current_user.user_id},
    )
    artist = result.mappings().fetchone()

    if not artist:
        return {
            "onboarding_step": 0,
            "onboarding_complete": False,
            "checklist": {
                "profile": False,
                "socials": False,
                "demo": False,
                "review": False,
            },
        }

    step = artist["onboarding_step"]
    return {
        "onboarding_step": step,
        "onboarding_complete": artist["onboarding_complete"],
        "artist_id": str(artist["id"]),
        "checklist": {
            "profile": step >= 1,
            "socials": step >= 2,
            "demo": step >= 3,
            "review": step >= 4,
        },
        "profile": {
            "name": artist["name"],
            "bio": artist["bio"],
            "genre": artist["genre"],
            "photo_url": artist["photo_url"],
        },
    }


@router.post("/connect-socials")
async def connect_socials(
    body: ConnectSocials,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    artist = await _get_or_create_artist(db, current_user.user_id)

    updates = {}
    if body.spotify_url is not None:
        updates["spotify_url"] = body.spotify_url
    if body.instagram_url is not None:
        updates["instagram_url"] = body.instagram_url
    if body.youtube_url is not None:
        updates["youtube_url"] = body.youtube_url

    if updates:
        # BUG FIX: whitelist socials columns
        _SOCIALS_ALLOWED = {"spotify_url", "instagram_url", "youtube_url"}
        updates = {k: v for k, v in updates.items() if k in _SOCIALS_ALLOWED}
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = str(artist["id"])
        await db.execute(
            text(f"UPDATE artists SET {set_clause}, onboarding_step = GREATEST(COALESCE(onboarding_step, 0), 2), updated_at = NOW() WHERE id = :id"),
            updates,
        )
        await db.commit()

    return {"status": "ok", "message": "Socials connected", "onboarding_step": 2}
