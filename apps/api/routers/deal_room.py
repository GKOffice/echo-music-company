"""
Melodio Deal Room API
Creator-to-creator rights trading marketplace endpoints.
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


# ── Helpers ──────────────────────────────────────────────────────────────────

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

class CreateListingRequest(BaseModel):
    creator_id: str
    creator_type: str       # artist | producer | songwriter
    listing_type: str       # sell_master_points | sell_publishing_points | buy_master_points |
                            # seek_cowriter | seek_producer | offer_beat
    title: str
    description: Optional[str] = None
    track_id: Optional[str] = None
    release_id: Optional[str] = None
    points_qty: Optional[float] = None
    asking_price: Optional[float] = None
    accept_points: bool = False
    accept_cash: bool = True
    points_price: Optional[float] = None
    genre: Optional[str] = None
    mood: Optional[list[str]] = None
    bpm_min: Optional[int] = None
    bpm_max: Optional[int] = None
    expires_days: Optional[int] = 30  # default 30-day listing


class MakeOfferRequest(BaseModel):
    listing_id: str
    offerer_id: str
    offer_type: str          # cash | points | hybrid
    cash_amount: Optional[float] = None
    points_offered: Optional[float] = None
    points_track_id: Optional[str] = None
    message: Optional[str] = None


class CounterOfferRequest(BaseModel):
    offer_id: str
    counter_cash: Optional[float] = None
    counter_points: Optional[float] = None
    counter_message: Optional[str] = None


class SendMessageRequest(BaseModel):
    deal_offer_id: str
    sender_id: str
    message: str
    attachment_url: Optional[str] = None


# ── Listings ──────────────────────────────────────────────────────────────────

@router.get("/listings")
async def browse_listings(
    listing_type: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    creator_type: Optional[str] = Query(None),
    accept_points: Optional[bool] = Query(None),
    accept_cash: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    sort: str = Query("newest", enum=["newest", "price_low", "price_high", "most_viewed"]),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Browse all active Deal Room listings with optional filters."""
    conditions = ["dl.status = 'active'"]
    params: dict = {"limit": limit, "offset": offset}

    if listing_type:
        conditions.append("dl.listing_type = :listing_type")
        params["listing_type"] = listing_type
    if genre:
        conditions.append("dl.genre ILIKE :genre")
        params["genre"] = f"%{genre}%"
    if creator_type:
        conditions.append("dl.creator_type = :creator_type")
        params["creator_type"] = creator_type
    if accept_points is not None:
        conditions.append("dl.accept_points = :accept_points")
        params["accept_points"] = accept_points
    if accept_cash is not None:
        conditions.append("dl.accept_cash = :accept_cash")
        params["accept_cash"] = accept_cash
    if min_price is not None:
        conditions.append("dl.asking_price >= :min_price")
        params["min_price"] = min_price
    if max_price is not None:
        conditions.append("dl.asking_price <= :max_price")
        params["max_price"] = max_price

    order_map = {
        "newest": "dl.created_at DESC",
        "price_low": "dl.asking_price ASC NULLS LAST",
        "price_high": "dl.asking_price DESC NULLS LAST",
        "most_viewed": "dl.views DESC",
    }
    order = order_map.get(sort, "dl.created_at DESC")
    where = " AND ".join(conditions)

    result = await db.execute(
        text(f"""
            SELECT
                dl.id, dl.creator_id, dl.creator_type, dl.listing_type,
                dl.title, dl.description, dl.track_id, dl.release_id,
                dl.points_qty, dl.asking_price, dl.accept_points, dl.accept_cash,
                dl.points_price, dl.genre, dl.mood, dl.bpm_min, dl.bpm_max,
                dl.status, dl.views, dl.created_at, dl.expires_at,
                t.title AS track_title, t.genre AS track_genre, t.bpm,
                r.title AS release_title
            FROM deal_listings dl
            LEFT JOIN tracks t ON dl.track_id = t.id
            LEFT JOIN releases r ON dl.release_id = r.id
            WHERE {where}
            ORDER BY {order}
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    rows = result.mappings().all()

    # Increment views for returned listings
    if rows:
        ids = [str(r["id"]) for r in rows]
        placeholders = ", ".join(f"'{i}'" for i in ids)
        await db.execute(
            text(f"UPDATE deal_listings SET views = views + 1 WHERE id::text IN ({placeholders})")
        )

    count_result = await db.execute(
        text(f"SELECT COUNT(*) as total FROM deal_listings dl WHERE {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    total = count_result.scalar()

    await db.commit()
    return {
        "listings": [_serialize(dict(r)) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/listings/{listing_id}")
async def get_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single listing with its active offers count."""
    result = await db.execute(
        text("""
            SELECT
                dl.*,
                t.title AS track_title, t.genre AS track_genre, t.bpm,
                r.title AS release_title, r.artwork_url,
                (SELECT COUNT(*) FROM deal_offers WHERE listing_id = dl.id AND status = 'pending') AS pending_offers
            FROM deal_listings dl
            LEFT JOIN tracks t ON dl.track_id = t.id
            LEFT JOIN releases r ON dl.release_id = r.id
            WHERE dl.id = :listing_id
        """),
        {"listing_id": listing_id},
    )
    row = result.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _serialize(dict(row))


@router.post("/listings", status_code=201)
async def create_listing(
    req: CreateListingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Create a new Deal Room listing."""
    from datetime import datetime, timezone, timedelta

    # Validate point ownership for sell listings
    if req.listing_type in ("sell_master_points", "sell_publishing_points") and req.points_qty:
        point_type = "master" if req.listing_type == "sell_master_points" else "publishing"
        owned_result = await db.execute(
            text("""
                SELECT COALESCE(SUM(points_purchased), 0) as total
                FROM echo_points
                WHERE buyer_user_id = :user_id
                  AND track_id = :track_id
                  AND point_type = :point_type
                  AND status IN ('active', 'tradeable')
            """),
            {"user_id": req.creator_id, "track_id": req.track_id, "point_type": point_type},
        )
        owned = float(owned_result.scalar() or 0)
        if req.points_qty > owned:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient points. You own {owned} {point_type} points for this track.",
            )

    expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_days or 30)
    listing_id = str(uuid.uuid4())

    await db.execute(
        text("""
            INSERT INTO deal_listings (
                id, creator_id, creator_type, listing_type,
                title, description, track_id, release_id,
                points_qty, asking_price, accept_points, accept_cash,
                points_price, genre, mood, bpm_min, bpm_max, expires_at
            ) VALUES (
                :id, :creator_id, :creator_type, :listing_type,
                :title, :description, :track_id, :release_id,
                :points_qty, :asking_price, :accept_points, :accept_cash,
                :points_price, :genre, :mood, :bpm_min, :bpm_max, :expires_at
            )
        """),
        {
            "id": listing_id,
            "creator_id": req.creator_id,
            "creator_type": req.creator_type,
            "listing_type": req.listing_type,
            "title": req.title,
            "description": req.description,
            "track_id": req.track_id,
            "release_id": req.release_id,
            "points_qty": req.points_qty,
            "asking_price": req.asking_price,
            "accept_points": req.accept_points,
            "accept_cash": req.accept_cash,
            "points_price": req.points_price,
            "genre": req.genre,
            "mood": req.mood or [],
            "bpm_min": req.bpm_min,
            "bpm_max": req.bpm_max,
            "expires_at": expires_at,
        },
    )
    await db.commit()
    return {"listing_id": listing_id, "status": "active", "expires_at": expires_at.isoformat()}


@router.delete("/listings/{listing_id}")
async def close_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Close / withdraw a listing (creator only)."""
    result = await db.execute(
        text("SELECT creator_id FROM deal_listings WHERE id = :id"),
        {"id": listing_id},
    )
    listing = result.mappings().fetchone()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if str(listing["creator_id"]) != current_user.user_id and current_user.role not in ("owner",):
        raise HTTPException(status_code=403, detail="Access denied")

    await db.execute(
        text("UPDATE deal_listings SET status = 'withdrawn', closed_at = NOW() WHERE id = :id"),
        {"id": listing_id},
    )
    await db.commit()
    return {"listing_id": listing_id, "status": "withdrawn"}


# ── My Listings ───────────────────────────────────────────────────────────────

@router.get("/my/listings")
async def my_listings(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get the current user's listings."""
    query = """
        SELECT dl.*, t.title AS track_title
        FROM deal_listings dl
        LEFT JOIN tracks t ON dl.track_id = t.id
        WHERE dl.creator_id = :user_id
    """
    params: dict = {"user_id": current_user.user_id}
    if status:
        query += " AND dl.status = :status"
        params["status"] = status
    query += " ORDER BY dl.created_at DESC LIMIT 50"

    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    return {"listings": [_serialize(dict(r)) for r in rows]}


# ── Offers ────────────────────────────────────────────────────────────────────

@router.get("/listings/{listing_id}/offers")
async def get_listing_offers(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get all offers on a listing (listing creator only)."""
    listing_result = await db.execute(
        text("SELECT creator_id FROM deal_listings WHERE id = :id"),
        {"id": listing_id},
    )
    listing = listing_result.mappings().fetchone()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if str(listing["creator_id"]) != current_user.user_id and current_user.role not in ("owner",):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        text("""
            SELECT do2.*, u.name AS offerer_name
            FROM deal_offers do2
            JOIN users u ON do2.offerer_id = u.id
            WHERE do2.listing_id = :listing_id
            ORDER BY do2.created_at DESC
        """),
        {"listing_id": listing_id},
    )
    rows = result.mappings().all()
    return {"offers": [_serialize(dict(r)) for r in rows]}


@router.post("/offers", status_code=201)
async def make_offer(
    req: MakeOfferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Place an offer on a Deal Room listing."""
    from datetime import datetime, timezone, timedelta

    # Validate listing
    listing_result = await db.execute(
        text("SELECT id, creator_id, status, title FROM deal_listings WHERE id = :id"),
        {"id": req.listing_id},
    )
    listing = listing_result.mappings().fetchone()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing["status"] != "active":
        raise HTTPException(status_code=400, detail=f"Listing is {listing['status']}")
    if str(listing["creator_id"]) == req.offerer_id:
        raise HTTPException(status_code=400, detail="Cannot offer on your own listing")

    # Validate point balance if paying with points
    if req.offer_type in ("points", "hybrid") and req.points_offered and req.points_track_id:
        owned_result = await db.execute(
            text("""
                SELECT COALESCE(SUM(points_purchased), 0) as total
                FROM echo_points
                WHERE buyer_user_id = :user_id AND track_id = :track_id
                  AND status IN ('active', 'tradeable')
            """),
            {"user_id": req.offerer_id, "track_id": req.points_track_id},
        )
        owned = float(owned_result.scalar() or 0)
        if req.points_offered > owned:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient points. You own {owned} points for that track.",
            )

    offer_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    await db.execute(
        text("""
            INSERT INTO deal_offers (
                id, listing_id, offerer_id, offer_type,
                cash_amount, points_offered, points_track_id,
                message, expires_at
            ) VALUES (
                :id, :listing_id, :offerer_id, :offer_type,
                :cash_amount, :points_offered, :points_track_id,
                :message, :expires_at
            )
        """),
        {
            "id": offer_id,
            "listing_id": req.listing_id,
            "offerer_id": req.offerer_id,
            "offer_type": req.offer_type,
            "cash_amount": req.cash_amount,
            "points_offered": req.points_offered,
            "points_track_id": req.points_track_id,
            "message": req.message,
            "expires_at": expires_at,
        },
    )
    await db.commit()
    return {
        "offer_id": offer_id,
        "listing_id": req.listing_id,
        "status": "pending",
        "expires_at": expires_at.isoformat(),
    }


@router.post("/offers/{offer_id}/counter")
async def counter_offer(
    offer_id: str,
    req: CounterOfferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Counter an offer (listing creator only)."""
    result = await db.execute(
        text("""
            SELECT do2.id, do2.offerer_id, do2.status, dl.creator_id, dl.title
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.id = :offer_id
        """),
        {"offer_id": offer_id},
    )
    offer = result.mappings().fetchone()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if str(offer["creator_id"]) != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if offer["status"] not in ("pending",):
        raise HTTPException(status_code=400, detail=f"Cannot counter an offer in '{offer['status']}' state")

    await db.execute(
        text("""
            UPDATE deal_offers
            SET status = 'countered',
                counter_cash = :counter_cash,
                counter_points = :counter_points,
                counter_message = :counter_message,
                responded_at = NOW()
            WHERE id = :offer_id
        """),
        {
            "offer_id": offer_id,
            "counter_cash": req.counter_cash,
            "counter_points": req.counter_points,
            "counter_message": req.counter_message,
        },
    )
    await db.commit()
    return {
        "offer_id": offer_id,
        "status": "countered",
        "counter_cash": req.counter_cash,
        "counter_points": req.counter_points,
    }


@router.post("/offers/{offer_id}/accept")
async def accept_offer(
    offer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Accept an offer and create a deal (listing creator only)."""
    result = await db.execute(
        text("""
            SELECT do2.id, do2.offerer_id, do2.listing_id, do2.offer_type,
                   do2.cash_amount, do2.points_offered, do2.status,
                   do2.counter_cash, do2.counter_points,
                   dl.creator_id, dl.title, dl.listing_type, dl.track_id
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.id = :offer_id
        """),
        {"offer_id": offer_id},
    )
    offer = result.mappings().fetchone()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if str(offer["creator_id"]) != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if offer["status"] not in ("pending", "countered"):
        raise HTTPException(status_code=400, detail=f"Cannot accept offer in '{offer['status']}' state")

    final_cash = offer["counter_cash"] if offer["status"] == "countered" else offer["cash_amount"]
    final_points = offer["counter_points"] if offer["status"] == "countered" else offer["points_offered"]

    await db.execute(
        text("UPDATE deal_offers SET status = 'accepted', responded_at = NOW() WHERE id = :id"),
        {"id": offer_id},
    )
    await db.execute(
        text("UPDATE deal_listings SET status = 'closed', closed_at = NOW() WHERE id = :id"),
        {"id": str(offer["listing_id"])},
    )

    deal_id = str(uuid.uuid4())
    contract_type_map = {
        "sell_master_points": "points_assignment",
        "sell_publishing_points": "points_assignment",
        "buy_master_points": "points_assignment",
        "seek_cowriter": "cowrite_agreement",
        "seek_producer": "beat_license",
        "offer_beat": "beat_license",
    }
    contract_type = contract_type_map.get(offer["listing_type"], "points_assignment")

    await db.execute(
        text("""
            INSERT INTO deals (
                id, listing_id, offer_id, seller_id, buyer_id,
                deal_type, track_id, cash_paid, points_paid, status
            ) VALUES (
                :id, :listing_id, :offer_id, :seller_id, :buyer_id,
                :deal_type, :track_id, :cash_paid, :points_paid, 'pending_contract'
            )
        """),
        {
            "id": deal_id,
            "listing_id": str(offer["listing_id"]),
            "offer_id": offer_id,
            "seller_id": str(offer["creator_id"]),
            "buyer_id": str(offer["offerer_id"]),
            "deal_type": offer["listing_type"],
            "track_id": str(offer["track_id"]) if offer["track_id"] else None,
            "cash_paid": final_cash,
            "points_paid": final_points,
        },
    )
    await db.commit()
    return {
        "deal_id": deal_id,
        "offer_id": offer_id,
        "status": "pending_contract",
        "contract_type": contract_type,
    }


@router.post("/offers/{offer_id}/reject")
async def reject_offer(
    offer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Reject an offer (listing creator only)."""
    result = await db.execute(
        text("""
            SELECT do2.id, dl.creator_id
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.id = :offer_id
        """),
        {"offer_id": offer_id},
    )
    offer = result.mappings().fetchone()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if str(offer["creator_id"]) != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.execute(
        text("UPDATE deal_offers SET status = 'rejected', responded_at = NOW() WHERE id = :id"),
        {"id": offer_id},
    )
    await db.commit()
    return {"offer_id": offer_id, "status": "rejected"}


@router.post("/offers/{offer_id}/withdraw")
async def withdraw_offer(
    offer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Withdraw your own offer."""
    result = await db.execute(
        text("SELECT id, offerer_id, status FROM deal_offers WHERE id = :id"),
        {"id": offer_id},
    )
    offer = result.mappings().fetchone()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if str(offer["offerer_id"]) != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if offer["status"] not in ("pending", "countered"):
        raise HTTPException(status_code=400, detail=f"Cannot withdraw offer in '{offer['status']}' state")

    await db.execute(
        text("UPDATE deal_offers SET status = 'withdrawn' WHERE id = :id"),
        {"id": offer_id},
    )
    await db.commit()
    return {"offer_id": offer_id, "status": "withdrawn"}


# ── My Offers / Deals ─────────────────────────────────────────────────────────

@router.get("/my/offers")
async def my_offers(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get all offers the current user has made."""
    result = await db.execute(
        text("""
            SELECT do2.*, dl.title AS listing_title, dl.listing_type
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.offerer_id = :user_id
            ORDER BY do2.created_at DESC LIMIT 50
        """),
        {"user_id": current_user.user_id},
    )
    rows = result.mappings().all()
    return {"offers": [_serialize(dict(r)) for r in rows]}


@router.get("/my/deals")
async def my_deals(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get all deals the current user is party to."""
    result = await db.execute(
        text("""
            SELECT d.*, dl.title AS listing_title
            FROM deals d
            JOIN deal_listings dl ON d.listing_id = dl.id
            WHERE d.seller_id = :user_id OR d.buyer_id = :user_id
            ORDER BY d.created_at DESC LIMIT 50
        """),
        {"user_id": current_user.user_id},
    )
    rows = result.mappings().all()
    return {"deals": [_serialize(dict(r)) for r in rows]}


@router.get("/deals/{deal_id}")
async def get_deal(
    deal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get deal details (parties only)."""
    result = await db.execute(
        text("""
            SELECT d.*, dl.title AS listing_title, dl.listing_type,
                   c.id AS contract_id, c.status AS contract_status, c.signed_at
            FROM deals d
            JOIN deal_listings dl ON d.listing_id = dl.id
            LEFT JOIN contracts c ON d.contract_id = c.id
            WHERE d.id = :deal_id
        """),
        {"deal_id": deal_id},
    )
    deal = result.mappings().fetchone()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if str(deal["seller_id"]) != current_user.user_id and \
       str(deal["buyer_id"]) != current_user.user_id and \
       current_user.role not in ("owner",):
        raise HTTPException(status_code=403, detail="Access denied")
    return _serialize(dict(deal))


@router.post("/deals/{deal_id}/complete")
async def complete_deal(
    deal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Mark a deal as complete after contract is signed and payment settled."""
    result = await db.execute(
        text("SELECT seller_id, buyer_id, status FROM deals WHERE id = :id"),
        {"id": deal_id},
    )
    deal = result.mappings().fetchone()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if str(deal["seller_id"]) != current_user.user_id and current_user.role not in ("owner",):
        raise HTTPException(status_code=403, detail="Access denied")
    if deal["status"] == "completed":
        raise HTTPException(status_code=400, detail="Deal already completed")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    await db.execute(
        text("""
            UPDATE deals
            SET status = 'completed', completed_at = :now,
                contract_signed_at = COALESCE(contract_signed_at, :now),
                cash_settled_at = :now
            WHERE id = :id
        """),
        {"id": deal_id, "now": now},
    )
    await db.commit()
    return {"deal_id": deal_id, "status": "completed", "completed_at": now.isoformat()}


# ── Messaging ─────────────────────────────────────────────────────────────────

@router.post("/messages", status_code=201)
async def send_message(
    req: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Send a message in a deal negotiation thread."""
    # Validate user is party to this offer
    result = await db.execute(
        text("""
            SELECT do2.offerer_id, dl.creator_id
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.id = :offer_id
        """),
        {"offer_id": req.deal_offer_id},
    )
    offer = result.mappings().fetchone()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if str(offer["offerer_id"]) != current_user.user_id and \
       str(offer["creator_id"]) != current_user.user_id and \
       current_user.role not in ("owner",):
        raise HTTPException(status_code=403, detail="Access denied")

    msg_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO deal_messages (id, deal_offer_id, sender_id, message, attachment_url)
            VALUES (:id, :offer_id, :sender_id, :message, :attachment_url)
        """),
        {
            "id": msg_id,
            "offer_id": req.deal_offer_id,
            "sender_id": req.sender_id,
            "message": req.message,
            "attachment_url": req.attachment_url,
        },
    )
    await db.commit()
    return {"message_id": msg_id}


@router.get("/messages/{deal_offer_id}")
async def get_thread(
    deal_offer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get the full negotiation thread for an offer."""
    # Validate access
    result = await db.execute(
        text("""
            SELECT do2.offerer_id, dl.creator_id
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.id = :offer_id
        """),
        {"offer_id": deal_offer_id},
    )
    offer = result.mappings().fetchone()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if str(offer["offerer_id"]) != current_user.user_id and \
       str(offer["creator_id"]) != current_user.user_id and \
       current_user.role not in ("owner",):
        raise HTTPException(status_code=403, detail="Access denied")

    msgs_result = await db.execute(
        text("""
            SELECT dm.id, dm.sender_id, dm.message, dm.attachment_url, dm.created_at,
                   u.name AS sender_name
            FROM deal_messages dm
            JOIN users u ON dm.sender_id = u.id
            WHERE dm.deal_offer_id = :offer_id
            ORDER BY dm.created_at ASC
        """),
        {"offer_id": deal_offer_id},
    )
    rows = msgs_result.mappings().all()
    return {"messages": [_serialize(dict(r)) for r in rows], "count": len(rows)}


# ── Price Suggestion ──────────────────────────────────────────────────────────

@router.get("/suggest-price")
async def suggest_price(
    listing_type: str = Query(...),
    points_qty: float = Query(1.0, gt=0),
    artist_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get a suggested fair price for a deal listing."""
    from decimal import Decimal, ROUND_HALF_UP

    tier = "new"
    if artist_id:
        result = await db.execute(
            text("SELECT tier FROM artists WHERE id = :id"),
            {"id": artist_id},
        )
        row = result.mappings().fetchone()
        if row:
            tier = row["tier"] or "new"

    tier_prices = {
        "seed": 150, "new": 150, "rising": 600,
        "established": 3000, "star": 3000,
        "hot": 5000, "diamond": 12000, "legend": 25000,
    }
    base = tier_prices.get(tier, 150)
    per_point = round(base * 0.87, 2)
    total = round(per_point * points_qty)

    return {
        "listing_type": listing_type,
        "points_qty": points_qty,
        "suggested_price_per_point": per_point,
        "suggested_total": total,
        "tier": tier,
        "rationale": f"{tier.capitalize()} tier — B2B price (13% below fan store rate)",
        "range": {"low": round(total * 0.8), "high": round(total * 1.2)},
    }


# ── Match Creators ────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get Deal Room marketplace stats."""
    _empty = {"active_listings": 0, "points_for_sale": 0, "cowrite_opportunities": 0, "deals_completed": 0, "total_value_traded": 0.0}
    try:
        result = await db.execute(
            text("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'active') AS active_listings,
                    COUNT(*) FILTER (WHERE status = 'active' AND listing_type IN ('sell_master_points','sell_publishing_points')) AS points_for_sale,
                    COUNT(*) FILTER (WHERE status = 'active' AND listing_type = 'seek_cowriter') AS cowrite_opportunities,
                    COUNT(*) FILTER (WHERE status = 'completed') AS deals_completed
                FROM deal_listings
            """)
        )
        row = result.mappings().fetchone()
        value_result = await db.execute(
            text("SELECT COALESCE(SUM(cash_paid), 0) AS total_value FROM deals WHERE status = 'completed'")
        )
        total_value = float(value_result.scalar() or 0)
        if not row:
            return _empty
        return {
            "active_listings": int(row["active_listings"] or 0),
            "points_for_sale": int(row["points_for_sale"] or 0),
            "cowrite_opportunities": int(row["cowrite_opportunities"] or 0),
            "deals_completed": int(row["deals_completed"] or 0),
            "total_value_traded": total_value,
        }
    except Exception:
        return _empty


# ── External Catalog ──────────────────────────────────────────────────────────

class ExternalCatalogRequest(BaseModel):
    user_id: str
    artist_id: Optional[str] = None
    title: str
    isrc: Optional[str] = None
    spotify_url: Optional[str] = None
    apple_url: Optional[str] = None
    youtube_url: Optional[str] = None
    monthly_streams: Optional[int] = None
    total_streams: Optional[int] = None
    estimated_annual_revenue: Optional[float] = None
    genre: Optional[str] = None
    release_year: Optional[int] = None
    rights_type: str = "master"


@router.post("/external-catalog", status_code=201)
async def submit_external_track(
    req: ExternalCatalogRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Submit an existing track (not on Melodio) for Deal Room listing."""
    catalog_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO external_catalog (
                id, user_id, artist_id, title, isrc,
                spotify_url, apple_url, youtube_url,
                monthly_streams, total_streams, estimated_annual_revenue,
                genre, release_year, rights_type, status
            ) VALUES (
                :id, :user_id, :artist_id, :title, :isrc,
                :spotify_url, :apple_url, :youtube_url,
                :monthly_streams, :total_streams, :estimated_annual_revenue,
                :genre, :release_year, :rights_type, 'pending'
            )
        """),
        {
            "id": catalog_id,
            "user_id": req.user_id,
            "artist_id": req.artist_id,
            "title": req.title,
            "isrc": req.isrc,
            "spotify_url": req.spotify_url,
            "apple_url": req.apple_url,
            "youtube_url": req.youtube_url,
            "monthly_streams": req.monthly_streams or 0,
            "total_streams": req.total_streams or 0,
            "estimated_annual_revenue": req.estimated_annual_revenue,
            "genre": req.genre,
            "release_year": req.release_year,
            "rights_type": req.rights_type,
        },
    )
    await db.commit()
    return {
        "catalog_id": catalog_id,
        "status": "pending",
        "message": "Track submitted for verification. Stats will be populated within 24 hours.",
    }


@router.get("/external-catalog/{catalog_id}")
async def get_external_catalog(
    catalog_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get external catalog entry with streaming stats."""
    result = await db.execute(
        text("SELECT * FROM external_catalog WHERE id = :id"),
        {"id": catalog_id},
    )
    row = result.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Catalog entry not found")
    return _serialize(dict(row))


# ── Auction / Bidding ─────────────────────────────────────────────────────────

class PlaceBidRequest(BaseModel):
    bidder_id: str
    bid_amount: float
    message: Optional[str] = None


@router.post("/listings/{listing_id}/bid", status_code=201)
async def place_bid(
    listing_id: str,
    req: PlaceBidRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Place a bid on an auction listing."""
    from datetime import datetime, timezone

    listing_result = await db.execute(
        text("""
            SELECT id, creator_id, status, listing_mode,
                   auction_ends_at, highest_bid_amount, bid_count, title
            FROM deal_listings WHERE id = :id
        """),
        {"id": listing_id},
    )
    listing = listing_result.mappings().fetchone()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing["listing_mode"] != "auction":
        raise HTTPException(status_code=400, detail="Listing is not in auction mode")
    if listing["status"] != "active":
        raise HTTPException(status_code=400, detail=f"Listing is {listing['status']}")
    if listing["auction_ends_at"] and listing["auction_ends_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Auction has ended")
    if str(listing["creator_id"]) == req.bidder_id:
        raise HTTPException(status_code=400, detail="Cannot bid on your own listing")

    current_high = float(listing["highest_bid_amount"] or 0)
    min_bid = current_high + 100 if current_high > 0 else 0
    if req.bid_amount <= current_high:
        raise HTTPException(
            status_code=400,
            detail=f"Bid must exceed current highest bid of ${current_high:.2f}. Minimum: ${min_bid:.2f}",
        )

    offer_id = str(uuid.uuid4())
    expires_at = listing["auction_ends_at"]

    await db.execute(
        text("""
            INSERT INTO deal_offers (
                id, listing_id, offerer_id, offer_type,
                cash_amount, message, expires_at, status
            ) VALUES (
                :id, :listing_id, :bidder_id, 'cash',
                :amount, :message, :expires_at, 'pending'
            )
        """),
        {
            "id": offer_id,
            "listing_id": listing_id,
            "bidder_id": req.bidder_id,
            "amount": req.bid_amount,
            "message": req.message,
            "expires_at": expires_at,
        },
    )

    # Update listing bid tracking
    await db.execute(
        text("""
            UPDATE deal_listings
            SET highest_bid_amount = :amount,
                bid_count = bid_count + 1
            WHERE id = :id
        """),
        {"id": listing_id, "amount": req.bid_amount},
    )
    await db.commit()
    return {
        "offer_id": offer_id,
        "listing_id": listing_id,
        "bid_amount": req.bid_amount,
        "status": "placed",
    }


@router.get("/listings/{listing_id}/bids")
async def get_bids(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all bids for an auction listing."""
    listing_result = await db.execute(
        text("SELECT listing_mode FROM deal_listings WHERE id = :id"),
        {"id": listing_id},
    )
    listing = listing_result.mappings().fetchone()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    result = await db.execute(
        text("""
            SELECT do2.id, do2.offerer_id, do2.cash_amount AS bid_amount,
                   do2.created_at, do2.status,
                   u.name AS bidder_name
            FROM deal_offers do2
            JOIN users u ON do2.offerer_id = u.id
            WHERE do2.listing_id = :listing_id
            ORDER BY do2.cash_amount DESC
        """),
        {"listing_id": listing_id},
    )
    rows = result.mappings().all()
    return {"bids": [_serialize(dict(r)) for r in rows], "count": len(rows)}


@router.get("/match")
async def match_creators(
    listing_type: str = Query(...),
    genre: Optional[str] = Query(None),
    bpm: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Smart creator matching — find the best collaborators for your listing."""
    matches = []

    if listing_type == "seek_producer":
        result = await db.execute(
            text("""
                SELECT hb.id, hb.title, hb.producer_id, hb.genre, hb.bpm,
                       hb.price_usd, hb.accept_points, u.name AS producer_name
                FROM hub_beats hb
                JOIN users u ON hb.producer_id = u.id
                WHERE hb.status = 'available'
                  AND (:genre IS NULL OR hb.genre ILIKE :genre_like)
                  AND (:bpm IS NULL OR ABS(hb.bpm - :bpm) <= 20)
                ORDER BY hb.created_at DESC LIMIT 5
            """),
            {
                "genre": genre,
                "genre_like": f"%{genre}%" if genre else None,
                "bpm": bpm,
            },
        )
        for i, r in enumerate(result.mappings().all()):
            row = _serialize(dict(r))
            row["compatibility_score"] = max(60, 95 - i * 7)
            row["match_type"] = "beat"
            matches.append(row)

    elif listing_type == "seek_cowriter":
        result = await db.execute(
            text("""
                SELECT dl.id, dl.creator_id, dl.title, dl.genre, dl.description,
                       dl.asking_price, dl.created_at, u.name AS creator_name
                FROM deal_listings dl
                JOIN users u ON dl.creator_id = u.id
                WHERE dl.listing_type = 'seek_cowriter' AND dl.status = 'active'
                  AND (:genre IS NULL OR dl.genre ILIKE :genre_like)
                ORDER BY dl.created_at DESC LIMIT 5
            """),
            {"genre": genre, "genre_like": f"%{genre}%" if genre else None},
        )
        for i, r in enumerate(result.mappings().all()):
            row = _serialize(dict(r))
            row["compatibility_score"] = max(55, 90 - i * 7)
            row["match_type"] = "cowriter"
            matches.append(row)

    else:
        result = await db.execute(
            text("""
                SELECT dl.id, dl.creator_id, dl.title, dl.genre, dl.description,
                       dl.asking_price, dl.accept_points, dl.created_at,
                       u.name AS creator_name
                FROM deal_listings dl
                JOIN users u ON dl.creator_id = u.id
                WHERE dl.listing_type = 'seek_producer' AND dl.status = 'active'
                  AND (:genre IS NULL OR dl.genre ILIKE :genre_like)
                ORDER BY dl.created_at DESC LIMIT 5
            """),
            {"genre": genre, "genre_like": f"%{genre}%" if genre else None},
        )
        for i, r in enumerate(result.mappings().all()):
            row = _serialize(dict(r))
            row["compatibility_score"] = max(55, 88 - i * 7)
            row["match_type"] = "artist_seeking_producer"
            matches.append(row)

    return {"matches": matches, "count": len(matches)}
