from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
import uuid

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()


class ReleaseCreate(BaseModel):
    artist_id: str
    title: str
    type: str = "single"
    genre: Optional[str] = None
    release_date: Optional[str] = None
    priority: str = "standard"


class ReleaseUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    genre: Optional[str] = None
    isrc: Optional[str] = None
    upc: Optional[str] = None
    release_date: Optional[str] = None
    master_audio_url: Optional[str] = None
    artwork_url: Optional[str] = None
    spotify_url: Optional[str] = None
    apple_url: Optional[str] = None
    youtube_url: Optional[str] = None


class TrackCreate(BaseModel):
    release_id: str
    artist_id: str
    title: str
    isrc: Optional[str] = None
    duration_seconds: Optional[int] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    genre: Optional[str] = None
    master_url: Optional[str] = None
    lyrics: Optional[str] = None


@router.get("/")
async def list_releases(
    artist_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if artist_id:
        conditions.append("r.artist_id = :artist_id")
        params["artist_id"] = artist_id
    if status:
        conditions.append("r.status = :status")
        params["status"] = status
    if type:
        conditions.append("r.type = :type")
        params["type"] = type

    where = " AND ".join(conditions)
    result = await db.execute(
        text(
            f"""
            SELECT r.*, a.name as artist_name
            FROM releases r
            LEFT JOIN artists a ON r.artist_id = a.id
            WHERE {where}
            ORDER BY r.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    releases = result.mappings().all()
    return {"releases": [dict(r) for r in releases]}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_release(
    release_in: ReleaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    valid_types = {"single", "ep", "album"}
    if release_in.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"type must be one of: {', '.join(valid_types)}",
        )

    release_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO releases (id, artist_id, title, type, genre, release_date, priority)
            VALUES (:id, :artist_id, :title, :type, :genre, :release_date, :priority)
            """
        ),
        {
            "id": release_id,
            "artist_id": release_in.artist_id,
            "title": release_in.title,
            "type": release_in.type,
            "genre": release_in.genre,
            "release_date": release_in.release_date,
            "priority": release_in.priority,
        },
    )
    await db.commit()
    return {"id": release_id, "message": "Release created"}


@router.get("/{release_id}")
async def get_release(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text(
            """
            SELECT r.*, a.name as artist_name
            FROM releases r
            LEFT JOIN artists a ON r.artist_id = a.id
            WHERE r.id = :id
            """
        ),
        {"id": release_id},
    )
    release = result.mappings().fetchone()
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return dict(release)


@router.patch("/{release_id}")
async def update_release(
    release_id: str,
    updates: ReleaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    set_clause = ", ".join(f"{k} = :{k}" for k in update_data)
    update_data["id"] = release_id

    await db.execute(
        text(f"UPDATE releases SET {set_clause}, updated_at = NOW() WHERE id = :id"),
        update_data,
    )
    await db.commit()
    return {"message": "Release updated"}


@router.get("/{release_id}/tracks")
async def get_release_tracks(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM tracks WHERE release_id = :release_id ORDER BY created_at ASC"),
        {"release_id": release_id},
    )
    tracks = result.mappings().all()
    return {"tracks": [dict(t) for t in tracks]}


@router.post("/{release_id}/tracks", status_code=status.HTTP_201_CREATED)
async def add_track(
    release_id: str,
    track_in: TrackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    track_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO tracks (id, release_id, artist_id, title, isrc, duration_seconds,
              bpm, key, genre, master_url, lyrics)
            VALUES (:id, :release_id, :artist_id, :title, :isrc, :duration_seconds,
              :bpm, :key, :genre, :master_url, :lyrics)
            """
        ),
        {
            "id": track_id,
            "release_id": release_id,
            "artist_id": track_in.artist_id,
            "title": track_in.title,
            "isrc": track_in.isrc,
            "duration_seconds": track_in.duration_seconds,
            "bpm": track_in.bpm,
            "key": track_in.key,
            "genre": track_in.genre,
            "master_url": track_in.master_url,
            "lyrics": track_in.lyrics,
        },
    )
    await db.commit()
    return {"id": track_id, "message": "Track added"}
