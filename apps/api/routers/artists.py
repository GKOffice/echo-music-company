from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
import uuid

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()


class ArtistCreate(BaseModel):
    name: str
    stage_name: Optional[str] = None
    genre: Optional[str] = None
    subgenres: Optional[List[str]] = None
    spotify_id: Optional[str] = None
    apple_id: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    twitter: Optional[str] = None
    deal_type: Optional[str] = None
    advance_amount: Optional[float] = 0.0


class ArtistUpdate(BaseModel):
    name: Optional[str] = None
    stage_name: Optional[str] = None
    genre: Optional[str] = None
    subgenres: Optional[List[str]] = None
    status: Optional[str] = None
    tier: Optional[str] = None
    echo_score: Optional[float] = None
    advance_amount: Optional[float] = None
    recoupment_balance: Optional[float] = None
    profile_photo_url: Optional[str] = None
    brand_guidelines_url: Optional[str] = None


@router.get("/")
async def list_artists(
    status: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if status:
        conditions.append("status = :status")
        params["status"] = status
    if tier:
        conditions.append("tier = :tier")
        params["tier"] = tier
    if genre:
        conditions.append("genre ILIKE :genre")
        params["genre"] = f"%{genre}%"

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"SELECT * FROM artists WHERE {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
        params,
    )
    artists = result.mappings().all()
    return {"artists": [dict(a) for a in artists], "total": len(artists)}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_artist(
    artist_in: ArtistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    artist_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO artists (id, name, stage_name, genre, subgenres, spotify_id,
              apple_id, instagram, tiktok, twitter, deal_type, advance_amount)
            VALUES (:id, :name, :stage_name, :genre, :subgenres, :spotify_id,
              :apple_id, :instagram, :tiktok, :twitter, :deal_type, :advance_amount)
            """
        ),
        {
            "id": artist_id,
            "name": artist_in.name,
            "stage_name": artist_in.stage_name,
            "genre": artist_in.genre,
            "subgenres": artist_in.subgenres,
            "spotify_id": artist_in.spotify_id,
            "apple_id": artist_in.apple_id,
            "instagram": artist_in.instagram,
            "tiktok": artist_in.tiktok,
            "twitter": artist_in.twitter,
            "deal_type": artist_in.deal_type,
            "advance_amount": artist_in.advance_amount or 0.0,
        },
    )
    await db.commit()
    return {"id": artist_id, "message": "Artist created"}


@router.get("/{artist_id}")
async def get_artist(
    artist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM artists WHERE id = :id"),
        {"id": artist_id},
    )
    artist = result.mappings().fetchone()
    if not artist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")
    return dict(artist)


@router.patch("/{artist_id}")
async def update_artist(
    artist_id: str,
    updates: ArtistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    set_clause = ", ".join(f"{k} = :{k}" for k in update_data)
    update_data["id"] = artist_id

    await db.execute(
        text(f"UPDATE artists SET {set_clause}, updated_at = NOW() WHERE id = :id"),
        update_data,
    )
    await db.commit()
    return {"message": "Artist updated"}


@router.get("/{artist_id}/releases")
async def get_artist_releases(
    artist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM releases WHERE artist_id = :artist_id ORDER BY created_at DESC"),
        {"artist_id": artist_id},
    )
    releases = result.mappings().all()
    return {"releases": [dict(r) for r in releases]}


@router.get("/{artist_id}/royalties")
async def get_artist_royalties(
    artist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text(
            """
            SELECT r.*, t.title as track_title
            FROM royalties r
            LEFT JOIN tracks t ON r.track_id = t.id
            WHERE r.artist_id = :artist_id
            ORDER BY r.created_at DESC
            LIMIT 100
            """
        ),
        {"artist_id": artist_id},
    )
    royalties = result.mappings().all()

    total = await db.execute(
        text("SELECT COALESCE(SUM(net_amount), 0) as total FROM royalties WHERE artist_id = :artist_id"),
        {"artist_id": artist_id},
    )
    total_row = total.fetchone()

    return {
        "royalties": [dict(r) for r in royalties],
        "total_earned": float(total_row.total) if total_row else 0.0,
    }
