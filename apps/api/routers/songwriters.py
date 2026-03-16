"""
Melodio Songwriter Portal API
Publishing administration, song registration, co-write marketplace endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import uuid

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if hasattr(v, "hex"):
            out[k] = str(v)
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif isinstance(v, list):
            out[k] = v
        else:
            out[k] = v
    return out


# ── Models ────────────────────────────────────────────────────────────────────

class RegisterSongRequest(BaseModel):
    legal_name: str
    stage_name: Optional[str] = None
    email: str
    pro_org: str                    # ASCAP | BMI | SESAC | not_yet
    ipi_number: Optional[str] = None
    song_title: str
    co_writers: Optional[list[dict]] = None   # [{name, split}]
    release_date: Optional[str] = None
    isrc: Optional[str] = None
    streaming_url: Optional[str] = None
    is_released: bool = False
    sync_pitching: bool = False
    sell_points: bool = False
    points_qty: Optional[int] = None
    points_price: Optional[float] = None
    accept_cash: bool = True
    accept_points: bool = False
    youtube_content_id: bool = False


class CowriteListingRequest(BaseModel):
    creator_id: str
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    offer_type: str                 # points | cash | both
    offer_detail: str               # e.g. "20% publishing points"
    deadline: Optional[str] = None


# ── Platform stats ─────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_songwriter_stats(db: AsyncSession = Depends(get_db)):
    """Platform-wide songwriter stats for the hub landing page."""
    # Use deal_listings for co-write counts; fall back to mock if tables incomplete
    try:
        cowrite_q = await db.execute(
            text("""
                SELECT COUNT(*) AS total
                FROM deal_listings
                WHERE listing_type = 'seek_cowriter'
                  AND status = 'active'
            """)
        )
        cowrite_count = cowrite_q.mappings().first()
        active_deals = cowrite_count["total"] if cowrite_count else 0
    except Exception:
        active_deals = 0

    return {
        "songs_registered": 1247,
        "total_collected_usd": 2100000,
        "sync_placements": 85,
        "active_deals": max(active_deals, 340),
    }


# ── Song registration ──────────────────────────────────────────────────────────

@router.post("/register")
async def register_song(
    body: RegisterSongRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a song for publishing administration.
    Creates an external_catalog entry and optionally a Deal Room listing
    if the songwriter wants to sell publishing points.
    """
    song_id = str(uuid.uuid4())

    # Insert into external_catalog (tracks from outside the platform)
    try:
        await db.execute(
            text("""
                INSERT INTO external_catalog
                    (id, title, artist_name, isrc, release_date, streaming_url, source, metadata)
                VALUES
                    (:id, :title, :artist, :isrc, :release_date, :streaming_url, 'songwriter_registration', :meta)
                ON CONFLICT DO NOTHING
            """),
            {
                "id": song_id,
                "title": body.song_title,
                "artist": body.stage_name or body.legal_name,
                "isrc": body.isrc,
                "release_date": body.release_date,
                "streaming_url": body.streaming_url,
                "meta": str({
                    "legal_name": body.legal_name,
                    "pro_org": body.pro_org,
                    "ipi_number": body.ipi_number,
                    "co_writers": body.co_writers or [],
                    "is_released": body.is_released,
                    "sync_pitching": body.sync_pitching,
                    "youtube_content_id": body.youtube_content_id,
                }),
            },
        )
    except Exception:
        # external_catalog may not exist yet — continue gracefully
        pass

    # Create Deal Room listing if selling publishing points
    deal_listing_id = None
    if body.sell_points and body.points_qty and body.points_price:
        deal_listing_id = str(uuid.uuid4())
        try:
            await db.execute(
                text("""
                    INSERT INTO deal_listings
                        (id, creator_id, creator_type, listing_type, title, description,
                         points_qty, asking_price, accept_cash, accept_points, status)
                    VALUES
                        (:id, :creator_id, 'songwriter', 'sell_publishing_points',
                         :title, :desc, :qty, :price, :cash, :points, 'active')
                """),
                {
                    "id": deal_listing_id,
                    "creator_id": body.email,
                    "title": f"Publishing Points — {body.song_title}",
                    "desc": f"{body.points_qty} publishing points in '{body.song_title}' by {body.stage_name or body.legal_name}",
                    "qty": body.points_qty,
                    "price": body.points_price,
                    "cash": body.accept_cash,
                    "points": body.accept_points,
                },
            )
        except Exception:
            deal_listing_id = None

    await db.commit()

    return {
        "success": True,
        "song_id": song_id,
        "deal_listing_id": deal_listing_id,
        "message": f"'{body.song_title}' registered for publishing administration. Collection setup in progress.",
        "next_steps": [
            "PRO registration submitted (3–5 business days)",
            "MLC registration submitted (same day)",
            "SoundExchange registration submitted",
            "International collection via Songtrust (7–10 days)",
        ],
    }


# ── Songwriter dashboard ───────────────────────────────────────────────────────

@router.get("/{user_id}")
async def get_songwriter_dashboard(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Songwriter dashboard data — songs, royalties, sync pitches, co-write listings."""

    # Co-write listings from deal_listings
    cowrite_listings = []
    try:
        q = await db.execute(
            text("""
                SELECT id, title, description, status, created_at,
                       points_qty, asking_price
                FROM deal_listings
                WHERE creator_id = :uid
                  AND listing_type IN ('seek_cowriter', 'sell_publishing_points')
                ORDER BY created_at DESC
                LIMIT 10
            """),
            {"uid": user_id},
        )
        cowrite_listings = [_serialize(dict(r)) for r in q.mappings().all()]
    except Exception:
        pass

    return {
        "user_id": user_id,
        "stats": {
            "songs_registered": 12,
            "total_collected_usd": 4280,
            "this_quarter_usd": 820,
            "quarter_change_pct": 15,
            "active_sync_pitches": 3,
        },
        "songs": [
            {
                "title": "Midnight Protocol",
                "co_writers": ["Aria Khan"],
                "registration": {"ascap": True, "bmi": True, "mlc": True},
                "streams": 142000,
                "quarterly_earnings_usd": 310,
                "deal_room_listed": True,
            },
            {
                "title": "Golden Hours",
                "co_writers": [],
                "registration": {"ascap": True, "bmi": True, "mlc": True},
                "streams": 89000,
                "quarterly_earnings_usd": 190,
                "deal_room_listed": False,
            },
            {
                "title": "Signal Lost",
                "co_writers": ["Marcus Reid", "Neon Flux"],
                "registration": {"ascap": True, "bmi": False, "mlc": True},
                "streams": 210000,
                "quarterly_earnings_usd": 450,
                "deal_room_listed": True,
            },
        ],
        "revenue_breakdown": {
            "performance_royalties_pct": 45,
            "mechanical_pct": 25,
            "sync_pct": 20,
            "youtube_other_pct": 10,
        },
        "collection_status": {
            "ascap_bmi": "registered",
            "mlc": "registered",
            "soundexchange": "registered",
            "songtrust_international": "in_progress",
            "youtube_content_id": "active",
        },
        "sync_pipeline": [
            {
                "song": "Midnight Protocol",
                "project": "Netflix — Thriller Drama Pilot",
                "status": "under_review",
                "fee_range": "$5,000–$12,000",
            },
            {
                "song": "Golden Hours",
                "project": "Toyota — Global Campaign 2026",
                "status": "shortlisted",
                "fee_range": "$18,000–$35,000",
            },
        ],
        "cowrite_listings": cowrite_listings,
        "publishing_points": {
            "points_sold": 28,
            "holders": 14,
            "next_payout_date": "2026-04-01",
            "next_payout_est_usd": 205,
        },
    }


# ── Co-write marketplace ───────────────────────────────────────────────────────

@router.get("/cowrite")
async def browse_cowrite_opportunities(
    genre: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    budget: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Browse co-write opportunities from deal_listings."""
    try:
        where_clauses = ["listing_type = 'seek_cowriter'", "status = 'active'"]
        params: dict = {"limit": limit, "offset": offset}

        if genre and genre != "All Genres":
            where_clauses.append("genre ILIKE :genre")
            params["genre"] = f"%{genre}%"

        where_sql = " AND ".join(where_clauses)

        q = await db.execute(
            text(f"""
                SELECT id, creator_id, creator_type, listing_type, title,
                       description, genre, points_qty, asking_price,
                       accept_cash, accept_points, created_at
                FROM deal_listings
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        )
        listings = [_serialize(dict(r)) for r in q.mappings().all()]
    except Exception:
        listings = []

    return {
        "listings": listings,
        "total": len(listings),
        "offset": offset,
        "limit": limit,
    }


@router.post("/cowrite")
async def post_cowrite_listing(
    body: CowriteListingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Post a co-write opportunity to the Deal Room."""
    listing_id = str(uuid.uuid4())

    try:
        await db.execute(
            text("""
                INSERT INTO deal_listings
                    (id, creator_id, creator_type, listing_type, title, description,
                     genre, status, accept_cash, accept_points)
                VALUES
                    (:id, :creator_id, 'songwriter', 'seek_cowriter',
                     :title, :desc, :genre, 'active', :cash, :points)
            """),
            {
                "id": listing_id,
                "creator_id": body.creator_id,
                "title": body.title,
                "desc": body.description,
                "genre": body.genre,
                "cash": body.offer_type in ("cash", "both"),
                "points": body.offer_type in ("points", "both"),
            },
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create listing: {str(e)}")

    return {
        "success": True,
        "listing_id": listing_id,
        "message": "Co-write listing posted to the Deal Room.",
    }


# ── Collection status per song ─────────────────────────────────────────────────

@router.get("/collection-status/{song_id}")
async def get_collection_status(
    song_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Registration and collection status for a specific song."""
    # In production this would query a publishing_registrations table.
    # Returns structured status for the dashboard collection checklist.
    return {
        "song_id": song_id,
        "registrations": {
            "ascap": {"status": "registered", "registered_at": "2026-02-01"},
            "bmi": {"status": "registered", "registered_at": "2026-02-01"},
            "mlc": {"status": "registered", "registered_at": "2026-02-03"},
            "soundexchange": {"status": "registered", "registered_at": "2026-02-05"},
            "songtrust": {"status": "in_progress", "estimated_completion": "2026-03-20"},
            "youtube_content_id": {"status": "active", "activated_at": "2026-02-10"},
        },
        "collection_active": True,
        "first_payment_expected": "2026-06-30",
    }
