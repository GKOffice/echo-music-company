from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
import uuid

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()


class BeatCreate(BaseModel):
    producer_id: str
    title: str
    type: str = "beat"
    audio_url: Optional[str] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    genre: Optional[List[str]] = None
    mood: Optional[List[str]] = None
    energy: Optional[int] = None
    instruments: Optional[List[str]] = None
    available_as: str = "non_exclusive"
    collaboration_open: bool = True
    price_min: Optional[float] = None
    price_max: Optional[float] = None


class BeatUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    available_as: Optional[str] = None
    collaboration_open: Optional[bool] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    quality_score: Optional[float] = None
    uniqueness_score: Optional[float] = None
    sync_readiness: Optional[float] = None

_BEAT_UPDATE_ALLOWED = {
    "title", "status", "available_as", "collaboration_open",
    "price_min", "price_max", "quality_score", "uniqueness_score", "sync_readiness",
}


@router.get("/beats")
async def list_beats(
    genre: Optional[str] = Query(None),
    bpm_min: Optional[float] = Query(None),
    bpm_max: Optional[float] = Query(None),
    mood: Optional[str] = Query(None),
    available_as: Optional[str] = Query(None),
    status: str = Query("available"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    conditions = ["hb.status = :status"]
    params: dict = {"status": status, "limit": limit, "offset": offset}

    if genre:
        conditions.append(":genre = ANY(hb.genre)")
        params["genre"] = genre
    if bpm_min:
        conditions.append("hb.bpm >= :bpm_min")
        params["bpm_min"] = bpm_min
    if bpm_max:
        conditions.append("hb.bpm <= :bpm_max")
        params["bpm_max"] = bpm_max
    if mood:
        conditions.append(":mood = ANY(hb.mood)")
        params["mood"] = mood
    if available_as:
        conditions.append("hb.available_as = :available_as")
        params["available_as"] = available_as

    where = " AND ".join(conditions)
    result = await db.execute(
        text(
            f"""
            SELECT hb.*, p.name as producer_name, p.tier as producer_tier
            FROM hub_beats hb
            LEFT JOIN producers p ON hb.producer_id = p.id
            WHERE {where}
            ORDER BY hb.quality_score DESC NULLS LAST, hb.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    beats = result.mappings().all()
    return {"beats": [dict(b) for b in beats], "total": len(beats)}


@router.post("/beats", status_code=status.HTTP_201_CREATED)
async def submit_beat(
    beat_in: BeatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    beat_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO hub_beats (id, producer_id, title, type, audio_url, bpm, key,
              genre, mood, energy, instruments, available_as, collaboration_open,
              price_min, price_max)
            VALUES (:id, :producer_id, :title, :type, :audio_url, :bpm, :key,
              :genre, :mood, :energy, :instruments, :available_as, :collaboration_open,
              :price_min, :price_max)
            """
        ),
        {
            "id": beat_id,
            "producer_id": beat_in.producer_id,
            "title": beat_in.title,
            "type": beat_in.type,
            "audio_url": beat_in.audio_url,
            "bpm": beat_in.bpm,
            "key": beat_in.key,
            "genre": beat_in.genre,
            "mood": beat_in.mood,
            "energy": beat_in.energy,
            "instruments": beat_in.instruments,
            "available_as": beat_in.available_as,
            "collaboration_open": beat_in.collaboration_open,
            "price_min": beat_in.price_min,
            "price_max": beat_in.price_max,
        },
    )
    await db.commit()
    return {"id": beat_id, "message": "Beat submitted for review", "status": "pending_review"}


@router.get("/beats/{beat_id}")
async def get_beat(
    beat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text(
            """
            SELECT hb.*, p.name as producer_name
            FROM hub_beats hb
            LEFT JOIN producers p ON hb.producer_id = p.id
            WHERE hb.id = :id
            """
        ),
        {"id": beat_id},
    )
    beat = result.mappings().fetchone()
    if not beat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beat not found")

    await db.execute(
        text("UPDATE hub_beats SET preview_count = preview_count + 1 WHERE id = :id"),
        {"id": beat_id},
    )
    await db.commit()
    return dict(beat)


@router.patch("/beats/{beat_id}")
async def update_beat(
    beat_id: str,
    updates: BeatUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    # BUG FIX: whitelist column names
    update_data = {k: v for k, v in update_data.items() if k in _BEAT_UPDATE_ALLOWED}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    set_clause = ", ".join(f"{k} = :{k}" for k in update_data)
    update_data["id"] = beat_id

    await db.execute(
        text(f"UPDATE hub_beats SET {set_clause} WHERE id = :id"),
        update_data,
    )
    await db.commit()
    return {"message": "Beat updated"}


@router.get("/producers/{producer_id}/beats")
async def get_producer_beats(
    producer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM hub_beats WHERE producer_id = :producer_id ORDER BY created_at DESC"),
        {"producer_id": producer_id},
    )
    beats = result.mappings().all()
    return {"beats": [dict(b) for b in beats]}
