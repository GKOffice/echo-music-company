import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from database import get_db
from routers.auth import get_current_user, TokenData
from services.isrc import generate_isrc
from services.email import release_submitted_email

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CreateRelease(BaseModel):
    title: str
    type: str = "single"  # single, ep, album
    artist_id: Optional[str] = None  # if omitted, uses current user's artist


class AddTrack(BaseModel):
    title: str
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None


class SetArtwork(BaseModel):
    artwork_url: str


class SetMetadata(BaseModel):
    release_date: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_artist_for_user(db: AsyncSession, user_id: str):
    result = await db.execute(
        text("SELECT id FROM artists WHERE user_id = :uid"),
        {"uid": user_id},
    )
    row = result.fetchone()
    return str(row.id) if row else None


async def _verify_release_owner(db: AsyncSession, release_id: str, user_id: str):
    result = await db.execute(
        text("""
            SELECT r.id FROM releases r
            JOIN artists a ON r.artist_id = a.id
            WHERE r.id = :rid AND a.user_id = :uid
        """),
        {"rid": release_id, "uid": user_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Release not found")


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

@router.post("/create")
async def create_release(
    body: CreateRelease,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    artist_id = body.artist_id
    if not artist_id:
        artist_id = await _get_artist_for_user(db, current_user.user_id)
    if not artist_id:
        raise HTTPException(status_code=400, detail="No artist profile found. Complete onboarding first.")

    if body.type not in ("single", "ep", "album"):
        raise HTTPException(status_code=400, detail="Type must be single, ep, or album")

    release_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO releases (id, artist_id, title, type, status, created_at)
            VALUES (:id, :artist_id, :title, :type, 'draft', NOW())
        """),
        {"id": release_id, "artist_id": artist_id, "title": body.title, "type": body.type},
    )
    await db.commit()

    return {"status": "ok", "release_id": release_id, "title": body.title, "type": body.type}


@router.post("/{release_id}/tracks")
async def add_tracks(
    release_id: str,
    body: AddTrack,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_release_owner(db, release_id, current_user.user_id)

    # Get artist_id from the release
    result = await db.execute(
        text("SELECT artist_id FROM releases WHERE id = :rid"),
        {"rid": release_id},
    )
    release = result.fetchone()

    isrc = await generate_isrc(db)
    track_id = str(uuid.uuid4())

    await db.execute(
        text("""
            INSERT INTO tracks (id, release_id, artist_id, title, isrc, master_url, duration_seconds, created_at)
            VALUES (:id, :release_id, :artist_id, :title, :isrc, :audio_url, :duration, NOW())
        """),
        {
            "id": track_id,
            "release_id": release_id,
            "artist_id": str(release.artist_id),
            "title": body.title,
            "isrc": isrc,
            "audio_url": body.audio_url,
            "duration": body.duration_seconds,
        },
    )
    await db.commit()

    return {"status": "ok", "track_id": track_id, "isrc": isrc}


@router.post("/{release_id}/artwork")
async def set_artwork(
    release_id: str,
    body: SetArtwork,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_release_owner(db, release_id, current_user.user_id)

    await db.execute(
        text("UPDATE releases SET artwork_url = :url, updated_at = NOW() WHERE id = :id"),
        {"url": body.artwork_url, "id": release_id},
    )
    await db.commit()

    return {"status": "ok", "message": "Artwork set"}


@router.post("/{release_id}/metadata")
async def set_metadata(
    release_id: str,
    body: SetMetadata,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_release_owner(db, release_id, current_user.user_id)

    updates = {}
    if body.release_date is not None:
        updates["release_date"] = body.release_date
    if body.genre is not None:
        updates["genre"] = body.genre

    if updates:
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = release_id
        await db.execute(
            text(f"UPDATE releases SET {set_clause}, updated_at = NOW() WHERE id = :id"),
            updates,
        )
        await db.commit()

    return {"status": "ok", "message": "Metadata updated"}


@router.post("/{release_id}/submit")
async def submit_release(
    release_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_release_owner(db, release_id, current_user.user_id)

    # Check release has minimum requirements
    result = await db.execute(
        text("SELECT title, artwork_url, type FROM releases WHERE id = :id"),
        {"id": release_id},
    )
    release = result.mappings().fetchone()

    track_count = await db.execute(
        text("SELECT COUNT(*) as cnt FROM tracks WHERE release_id = :rid"),
        {"rid": release_id},
    )
    count = track_count.scalar()

    if count == 0:
        raise HTTPException(status_code=400, detail="Release must have at least one track")

    await db.execute(
        text("UPDATE releases SET status = 'pending_review', distribution_status = 'pending', updated_at = NOW() WHERE id = :id"),
        {"id": release_id},
    )
    await db.commit()

    email = await _get_user_email(db, current_user.user_id)
    if email:
        asyncio.create_task(release_submitted_email(email, release["title"]))

    return {"status": "ok", "message": "Release submitted for review", "release_status": "pending_review"}


@router.get("/{release_id}/checklist")
async def release_checklist(
    release_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_release_owner(db, release_id, current_user.user_id)

    result = await db.execute(
        text("SELECT title, type, genre, artwork_url, release_date, status FROM releases WHERE id = :id"),
        {"id": release_id},
    )
    release = result.mappings().fetchone()

    track_result = await db.execute(
        text("SELECT id, title, isrc, master_url, duration_seconds FROM tracks WHERE release_id = :rid"),
        {"rid": release_id},
    )
    tracks = [dict(r) for r in track_result.mappings().fetchall()]

    has_tracks = len(tracks) > 0
    has_artwork = bool(release["artwork_url"])
    has_genre = bool(release["genre"])
    has_release_date = bool(release["release_date"])
    ready = has_tracks and has_artwork

    return {
        "release_id": release_id,
        "title": release["title"],
        "type": release["type"],
        "status": release["status"],
        "checklist": {
            "tracks": has_tracks,
            "artwork": has_artwork,
            "genre": has_genre,
            "release_date": has_release_date,
            "ready_to_submit": ready,
        },
        "tracks": tracks,
        "track_count": len(tracks),
    }


@router.get("/my")
async def my_releases(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    artist_id = await _get_artist_for_user(db, current_user.user_id)
    if not artist_id:
        return {"releases": []}

    result = await db.execute(
        text("""
            SELECT r.id, r.title, r.type, r.status, r.genre, r.artwork_url,
                   r.release_date, r.distribution_status, r.created_at,
                   COALESCE((SELECT COUNT(*) FROM tracks t WHERE t.release_id = r.id), 0) as track_count
            FROM releases r
            WHERE r.artist_id = :aid
            ORDER BY r.created_at DESC
        """),
        {"aid": artist_id},
    )
    releases = [dict(r) for r in result.mappings().fetchall()]
    for r in releases:
        r["id"] = str(r["id"])
        if r.get("created_at"):
            r["created_at"] = str(r["created_at"])
        if r.get("release_date"):
            r["release_date"] = str(r["release_date"])

    return {"releases": releases}
