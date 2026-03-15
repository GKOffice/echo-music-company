from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import uuid
import json
import random
import string
import re
from datetime import datetime, timezone, timedelta

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()

PLATFORMS = [
    "spotify", "apple_music", "amazon_music", "tidal",
    "youtube_music", "deezer", "tiktok_sound", "instagram_music",
]


# ----------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------

class ScheduleReleaseRequest(BaseModel):
    target_date: str  # YYYY-MM-DD

class ISRCRequest(BaseModel):
    track_id: str

class PresaveRequest(BaseModel):
    release_id: str


# ----------------------------------------------------------------
# List Releases with Distribution Status
# ----------------------------------------------------------------

@router.get("/releases")
async def list_releases(
    status_filter: Optional[str] = Query(None, alias="status"),
    artist_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """List all releases with distribution status."""
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if status_filter:
        conditions.append("r.status = :status")
        params["status"] = status_filter
    if artist_id:
        conditions.append("r.artist_id = :artist_id")
        params["artist_id"] = artist_id

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"""
            SELECT r.id, r.title, r.status, r.release_date, r.upc,
                   r.master_audio_url, r.artwork_url, r.genre,
                   a.name as artist_name, a.stage_name,
                   (SELECT COUNT(*) FROM release_platforms rp WHERE rp.release_id = r.id) as platform_count,
                   (SELECT tracking_id FROM distribution_submissions ds
                    WHERE ds.release_id = r.id ORDER BY submitted_at DESC LIMIT 1) as tracking_id
            FROM releases r
            LEFT JOIN artists a ON r.artist_id = a.id
            WHERE {where}
            ORDER BY r.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    releases = [dict(r) for r in result.mappings().all()]

    total_result = await db.execute(
        text(f"SELECT COUNT(*) FROM releases r WHERE {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    total = total_result.scalar()

    return {"releases": releases, "total": total, "limit": limit, "offset": offset}


# ----------------------------------------------------------------
# Release Distribution Detail
# ----------------------------------------------------------------

@router.get("/releases/{release_id}")
async def get_release_distribution(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Release distribution detail with platform-by-platform status."""
    result = await db.execute(
        text("""SELECT r.*, a.name as artist_name, a.stage_name
               FROM releases r LEFT JOIN artists a ON r.artist_id = a.id
               WHERE r.id = :id"""),
        {"id": release_id},
    )
    release = result.mappings().fetchone()
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    platforms_result = await db.execute(
        text("SELECT platform, status, platform_url, platform_id, went_live_at, created_at FROM release_platforms WHERE release_id = :id"),
        {"id": release_id},
    )
    platforms = [dict(r) for r in platforms_result.mappings().all()]

    # Fill in any missing platforms
    existing_platforms = {p["platform"] for p in platforms}
    for plat in PLATFORMS:
        if plat not in existing_platforms:
            platforms.append({"platform": plat, "status": "not_submitted", "platform_url": None, "went_live_at": None})

    submissions_result = await db.execute(
        text("""SELECT id, distributor, status, tracking_id, submitted_at, expected_live_at, confirmed_live_at, notes
               FROM distribution_submissions WHERE release_id = :id ORDER BY submitted_at DESC"""),
        {"id": release_id},
    )
    submissions = [dict(r) for r in submissions_result.mappings().all()]

    tracks_result = await db.execute(
        text("SELECT id, title, isrc, duration_seconds FROM tracks WHERE release_id = :id"),
        {"id": release_id},
    )
    tracks = [dict(r) for r in tracks_result.mappings().all()]

    return {
        "release_id": release_id,
        "title": release["title"],
        "artist": release.get("stage_name") or release.get("artist_name"),
        "status": release["status"],
        "release_date": str(release["release_date"]) if release.get("release_date") else None,
        "upc": release.get("upc"),
        "genre": release.get("genre"),
        "artwork_url": release.get("artwork_url"),
        "master_audio_url": release.get("master_audio_url"),
        "tracks": tracks,
        "platform_status": platforms,
        "submissions": submissions,
    }


# ----------------------------------------------------------------
# Submit to Distributor
# ----------------------------------------------------------------

@router.post("/releases/{release_id}/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit_to_distributor(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Submit release to distributor (DistroKid). Builds payload, logs submission, records platform entries."""
    release_result = await db.execute(
        text("""SELECT r.*, a.name as artist_name, a.stage_name
               FROM releases r LEFT JOIN artists a ON r.artist_id = a.id
               WHERE r.id = :id"""),
        {"id": release_id},
    )
    release = release_result.mappings().fetchone()
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    tracks_result = await db.execute(
        text("SELECT id, title, isrc, duration_seconds FROM tracks WHERE release_id = :id"),
        {"id": release_id},
    )
    tracks = [dict(r) for r in tracks_result.mappings().all()]

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

    tracking_id = "DK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    submission_id = str(uuid.uuid4())
    expected_live = datetime.now(timezone.utc) + timedelta(days=3)

    await db.execute(
        text("""INSERT INTO distribution_submissions
                    (id, release_id, distributor, status, submission_payload, tracking_id, expected_live_at)
               VALUES (:id, :release_id, 'distrokid', 'submitted', :payload, :tracking, :expected)"""),
        {
            "id": submission_id,
            "release_id": release_id,
            "payload": json.dumps(payload),
            "tracking": tracking_id,
            "expected": expected_live,
        },
    )

    for platform in PLATFORMS:
        await db.execute(
            text("""INSERT INTO release_platforms (id, release_id, platform, status)
                    VALUES (:id, :release_id, :platform, 'submitted')
                    ON CONFLICT DO NOTHING"""),
            {"id": str(uuid.uuid4()), "release_id": release_id, "platform": platform},
        )

    await db.execute(
        text("UPDATE releases SET status = 'submitted', updated_at = NOW() WHERE id = :id"),
        {"id": release_id},
    )
    await db.commit()

    return {
        "release_id": release_id,
        "submission_id": submission_id,
        "tracking_id": tracking_id,
        "distributor": "distrokid",
        "status": "submitted",
        "platforms": PLATFORMS,
        "expected_live_at": expected_live.isoformat(),
        "note": "DistroKid API call would fire here in production",
    }


# ----------------------------------------------------------------
# Playlist Pitch
# ----------------------------------------------------------------

@router.post("/releases/{release_id}/pitch", status_code=status.HTTP_201_CREATED)
async def submit_playlist_pitch(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Submit editorial playlist pitch. Requires 28+ days lead time."""
    result = await db.execute(
        text("""SELECT r.*, a.name as artist_name, a.stage_name, a.bio
               FROM releases r LEFT JOIN artists a ON r.artist_id = a.id
               WHERE r.id = :id"""),
        {"id": release_id},
    )
    release = result.mappings().fetchone()
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    release_date = release.get("release_date")
    days_until = None
    if release_date:
        delta = release_date - datetime.now(timezone.utc).date()
        days_until = delta.days
        if days_until < 28:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Playlist pitch requires 28+ days lead time. Only {days_until} days until release.",
            )

    artist_name = release.get("stage_name") or release.get("artist_name") or "Unknown Artist"
    bio = release.get("bio") or f"{artist_name} is a recording artist on ECHO Records."
    streaming_url = release.get("spotify_url") or f"echo-music.com/releases/{release_id}"

    pitch_text = (
        f"PLAYLIST PITCH — {artist_name}: '{release.get('title')}'\n\n"
        f"Artist: {artist_name}\nGenre: {release.get('genre', 'N/A')}\n"
        f"Release Date: {release_date}\nStreaming Link: {streaming_url}\n\n"
        f"About the Artist:\n{bio}\n\n"
        f"'{release.get('title')}' is a {release.get('genre', 'genre-defining')} track with strong momentum. "
        f"We believe it's a perfect fit for your editorial playlist."
    )

    await db.execute(
        text("""INSERT INTO contacts (id, name, contact_type, notes, created_by)
               VALUES (:id, :name, 'playlist_curator', :notes, 'distribution_api')"""),
        {
            "id": str(uuid.uuid4()),
            "name": f"Editorial Pitch: {release.get('title')}",
            "notes": pitch_text[:500],
        },
    )
    await db.commit()

    return {
        "release_id": release_id,
        "pitch_submitted": True,
        "days_until_release": days_until,
        "pitch_summary": {
            "artist": artist_name,
            "title": release.get("title"),
            "genre": release.get("genre"),
            "release_date": str(release_date) if release_date else None,
        },
    }


# ----------------------------------------------------------------
# Schedule Release
# ----------------------------------------------------------------

@router.post("/releases/{release_id}/schedule")
async def schedule_release(
    release_id: str,
    body: ScheduleReleaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Schedule a release date. Minimum 28 days lead time. Returns full timeline."""
    result = await db.execute(
        text("SELECT id, title FROM releases WHERE id = :id"),
        {"id": release_id},
    )
    release = result.mappings().fetchone()
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    try:
        target_date = datetime.strptime(body.target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="target_date must be YYYY-MM-DD")

    today = datetime.now(timezone.utc).date()
    days_ahead = (target_date - today).days
    if days_ahead < 28:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum 28 days lead time required. Target is {days_ahead} days away.",
        )

    timeline = [
        {"date": str(target_date - timedelta(days=28)), "milestone": "T-28", "action": "Upload masters + metadata to distributor"},
        {"date": str(target_date - timedelta(days=21)), "milestone": "T-21", "action": "Submit editorial playlist pitch"},
        {"date": str(target_date - timedelta(days=14)), "milestone": "T-14", "action": "Contingency / asset fixes window"},
        {"date": str(target_date - timedelta(days=7)), "milestone": "T-7", "action": "Marketing campaign launch + social posts"},
        {"date": str(target_date), "milestone": "T-0", "action": "Release day — confirm live on all platforms"},
    ]

    await db.execute(
        text("UPDATE releases SET release_date = :date, status = 'scheduled', updated_at = NOW() WHERE id = :id"),
        {"date": target_date, "id": release_id},
    )
    await db.commit()

    return {
        "release_id": release_id,
        "title": release["title"],
        "release_date": str(target_date),
        "days_lead_time": days_ahead,
        "timeline": timeline,
        "status": "scheduled",
    }


# ----------------------------------------------------------------
# Pre-Release Checklist
# ----------------------------------------------------------------

@router.get("/releases/{release_id}/checklist")
async def get_release_checklist(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Pre-release readiness checklist — assets, metadata, ISRC, UPC, lead time."""
    result = await db.execute(
        text("""SELECT r.*, a.name as artist_name, a.stage_name
               FROM releases r LEFT JOIN artists a ON r.artist_id = a.id
               WHERE r.id = :id"""),
        {"id": release_id},
    )
    release = result.mappings().fetchone()
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    tracks_result = await db.execute(
        text("SELECT id, title, isrc, credits FROM tracks WHERE release_id = :id"),
        {"id": release_id},
    )
    tracks = [dict(r) for r in tracks_result.mappings().all()]

    missing = []
    warnings = []
    checks = []

    def check(name: str, passed: bool, detail: str = ""):
        checks.append({"check": name, "passed": passed, "detail": detail})
        if not passed:
            missing.append(name)

    check("master_audio", bool(release.get("master_audio_url")), "Master audio file uploaded")
    check("artwork", bool(release.get("artwork_url")), "Artwork uploaded (3000x3000 recommended)")
    check("title", bool(release.get("title")), "Release title present")
    check("genre", bool(release.get("genre")), "Genre assigned")
    check("upc", bool(release.get("upc")), "UPC barcode assigned")
    check("tracks", len(tracks) > 0, f"{len(tracks)} track(s) linked")

    tracks_without_isrc = [t["title"] for t in tracks if not t.get("isrc")]
    check("isrc", len(tracks_without_isrc) == 0,
          "All tracks have ISRC" if not tracks_without_isrc else f"Missing ISRC: {tracks_without_isrc}")

    # Lead time check
    release_date = release.get("release_date")
    days_ahead = None
    if release_date:
        days_ahead = (release_date - datetime.now(timezone.utc).date()).days
        check("lead_time", days_ahead >= 28, f"{days_ahead} days until release (need 28+)")
    else:
        check("lead_time", False, "No release date set")

    # Presave link
    metadata = release.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            metadata = {}
    has_presave = bool(metadata.get("presave_url"))
    if not has_presave:
        warnings.append("No presave link created yet")

    return {
        "release_id": release_id,
        "title": release.get("title"),
        "ready": len(missing) == 0,
        "checks": checks,
        "missing": missing,
        "warnings": warnings,
        "days_until_release": days_ahead,
    }


# ----------------------------------------------------------------
# Generate ISRC
# ----------------------------------------------------------------

@router.post("/isrc", status_code=status.HTTP_201_CREATED)
async def generate_isrc(
    body: ISRCRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Generate and assign an ISRC code to a track."""
    track_result = await db.execute(
        text("SELECT id, title, isrc FROM tracks WHERE id = :id"),
        {"id": body.track_id},
    )
    track = track_result.mappings().fetchone()
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    if track.get("isrc"):
        return {"track_id": body.track_id, "isrc": track["isrc"], "generated": False}

    seq_result = await db.execute(text("SELECT COUNT(*) as cnt FROM tracks WHERE isrc IS NOT NULL"))
    seq = int((seq_result.mappings().fetchone() or {}).get("cnt") or 0) + 1

    year_2digit = datetime.now(timezone.utc).strftime("%y")
    isrc = f"US-ECH-{year_2digit}-{seq:05d}"

    await db.execute(
        text("UPDATE tracks SET isrc = :isrc, updated_at = NOW() WHERE id = :id"),
        {"isrc": isrc, "id": body.track_id},
    )
    await db.commit()

    return {"track_id": body.track_id, "title": track["title"], "isrc": isrc, "generated": True}


# ----------------------------------------------------------------
# Create Presave Link
# ----------------------------------------------------------------

@router.post("/presave", status_code=status.HTTP_201_CREATED)
async def create_presave_link(
    body: PresaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Create a presave link for a release."""
    result = await db.execute(
        text("SELECT id, title FROM releases WHERE id = :id"),
        {"id": body.release_id},
    )
    release = result.mappings().fetchone()
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    presave_url = f"https://echo-music.com/presave/{body.release_id}"

    await db.execute(
        text("""UPDATE releases
               SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('presave_url', :url::text),
                   updated_at = NOW()
               WHERE id = :id"""),
        {"url": presave_url, "id": body.release_id},
    )
    await db.commit()

    return {
        "release_id": body.release_id,
        "title": release["title"],
        "presave_url": presave_url,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
