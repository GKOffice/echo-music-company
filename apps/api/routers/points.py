from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import uuid
import math

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()


# ----------------------------------------------------------------
# Models
# ----------------------------------------------------------------

class BuyPointsRequest(BaseModel):
    points_qty: float
    price_per_point: Optional[float] = None  # uses drop price if not provided
    stripe_payment_id: Optional[str] = None


class ExchangeOrderRequest(BaseModel):
    track_id: Optional[str] = None
    echo_point_id: Optional[str] = None
    order_type: str  # "buy" or "sell"
    points_qty: float
    price_per_point: float


class CreateDropRequest(BaseModel):
    artist_id: str
    track_id: str
    release_id: Optional[str] = None
    points_to_sell: float
    price_per_point: float
    early_bird_discount_pct: float = 0.20


# ----------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------

def _earnings_estimate(monthly_listeners: int, price_per_point: float) -> dict:
    """Estimate quarterly royalty earnings per point based on listener count."""
    if monthly_listeners <= 0:
        return {"conservative": 0.0, "expected": 0.0, "optimistic": 0.0}
    # 3-month window; each point = 1% of revenue
    conservative = round(monthly_listeners * 0.3 * 0.003 * 3 / 100, 4)
    expected = round(monthly_listeners * 0.8 * 0.004 * 3 / 100, 4)
    optimistic = round(monthly_listeners * 1.5 * 0.005 * 3 / 100, 4)
    return {"conservative": conservative, "expected": expected, "optimistic": optimistic}


def _serialize_row(row: dict) -> dict:
    """Convert UUID / datetime objects to strings for JSON serialisation."""
    out = {}
    for k, v in row.items():
        if hasattr(v, "hex"):          # UUID
            out[k] = str(v)
        elif hasattr(v, "isoformat"):  # datetime / date
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


# ----------------------------------------------------------------
# Store endpoints
# ----------------------------------------------------------------

@router.get("/store")
async def browse_store(
    genre: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    sort: str = Query("newest", enum=["newest", "price_asc", "price_desc", "confidence_desc"]),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Browse all active point drops with optional filtering."""
    try:
        where_clauses = ["pd.status = 'active'"]
        params: dict = {"limit": limit, "offset": offset}

        if genre:
            where_clauses.append("a.genre ILIKE :genre")
            params["genre"] = f"%{genre}%"
        if tier:
            where_clauses.append("a.tier = :tier")
            params["tier"] = tier

        order_map = {
            "newest": "pd.created_at DESC",
            "price_asc": "pd.price_per_point ASC",
            "price_desc": "pd.price_per_point DESC",
            "confidence_desc": "pd.ai_confidence_score DESC",
        }
        order_by = order_map.get(sort, "pd.created_at DESC")
        where_sql = " AND ".join(where_clauses)

        result = await db.execute(
            text(f"""
                SELECT
                    pd.id as drop_id, pd.track_id, pd.artist_id,
                    pd.total_points_available, pd.points_sold, pd.price_per_point,
                    pd.early_bird_discount_pct, pd.early_bird_ends_at,
                    pd.ai_confidence_score, pd.closes_at, pd.created_at,
                    pd.total_points_available - pd.points_sold as points_remaining,
                    CASE WHEN pd.total_points_available > 0
                        THEN ROUND(pd.points_sold / pd.total_points_available * 100, 1)
                        ELSE 0 END as pct_sold,
                    t.title as track_title, t.duration_seconds, t.genre as track_genre,
                    a.name as artist_name, a.stage_name, a.genre as artist_genre,
                    a.monthly_listeners, a.tier as artist_tier, a.profile_photo_url,
                    COALESCE(
                        (SELECT price_per_point FROM exchange_trades
                         WHERE track_id = pd.track_id ORDER BY traded_at DESC LIMIT 1),
                        pd.price_per_point
                    ) as current_exchange_price
                FROM point_drops pd
                JOIN tracks t ON pd.track_id = t.id
                JOIN artists a ON pd.artist_id = a.id
                WHERE {where_sql}
                ORDER BY {order_by}
                LIMIT :limit OFFSET :offset
            """),
            params,
        )
        drops = result.mappings().all()

        count_result = await db.execute(
            text(f"""
                SELECT COUNT(*) as total
                FROM point_drops pd
                JOIN tracks t ON pd.track_id = t.id
                JOIN artists a ON pd.artist_id = a.id
                WHERE {where_sql}
            """),
            {k: v for k, v in params.items() if k not in ("limit", "offset")},
        )
        total = count_result.scalar() or 0

        items = []
        for d in drops:
            row = _serialize_row(dict(d))
            monthly_listeners = int(d.get("monthly_listeners") or 0)
            price = float(d.get("price_per_point") or 0)
            row["earnings_estimate"] = _earnings_estimate(monthly_listeners, price)
            items.append(row)

        return {"drops": items, "total": total, "limit": limit, "offset": offset}
    except Exception:
        return {"drops": [], "total": 0, "limit": limit, "offset": offset}


@router.get("/store/{track_id}")
async def get_drop_detail(
    track_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Single drop detail page data."""
    result = await db.execute(
        text("""
            SELECT
                pd.id as drop_id, pd.track_id, pd.artist_id, pd.release_id,
                pd.total_points_available, pd.points_sold, pd.price_per_point,
                pd.early_bird_discount_pct, pd.early_bird_ends_at, pd.ai_confidence_score,
                pd.status, pd.closes_at, pd.marketing_budget_allocated, pd.created_at,
                pd.total_points_available - pd.points_sold as points_remaining,
                CASE WHEN pd.total_points_available > 0
                    THEN ROUND(pd.points_sold / pd.total_points_available * 100, 1)
                    ELSE 0 END as pct_sold,
                t.title as track_title, t.duration_seconds, t.isrc, t.genre as track_genre,
                a.name as artist_name, a.stage_name, a.genre as artist_genre,
                a.monthly_listeners, a.tier as artist_tier, a.profile_photo_url,
                a.spotify_id, a.instagram, a.tiktok,
                r.title as release_title, r.artwork_url, r.release_date,
                COALESCE(
                    (SELECT price_per_point FROM exchange_trades
                     WHERE track_id = pd.track_id ORDER BY traded_at DESC LIMIT 1),
                    pd.price_per_point
                ) as current_exchange_price,
                (SELECT COUNT(*) FROM echo_points WHERE track_id = pd.track_id
                 AND status IN ('active','tradeable')) as holder_count
            FROM point_drops pd
            JOIN tracks t ON pd.track_id = t.id
            JOIN artists a ON pd.artist_id = a.id
            LEFT JOIN releases r ON pd.release_id = r.id
            WHERE pd.track_id = :track_id AND pd.status = 'active'
            ORDER BY pd.created_at DESC LIMIT 1
        """),
        {"track_id": track_id},
    )
    drop = result.mappings().fetchone()
    if not drop:
        raise HTTPException(status_code=404, detail="No active drop found for this track")

    row = _serialize_row(dict(drop))
    monthly_listeners = int(drop.get("monthly_listeners") or 0)
    row["earnings_estimate"] = _earnings_estimate(monthly_listeners, float(drop.get("price_per_point") or 0))

    # Price history for chart
    price_history_result = await db.execute(
        text("""
            SELECT price_per_point, volume_traded, source, recorded_at
            FROM track_price_history
            WHERE track_id = :track_id
            ORDER BY recorded_at DESC LIMIT 30
        """),
        {"track_id": track_id},
    )
    row["price_history"] = [_serialize_row(dict(h)) for h in price_history_result.mappings().all()]

    return row


@router.post("/store/{track_id}/buy", status_code=201)
async def buy_points(
    track_id: str,
    req: BuyPointsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Purchase points from an active drop. Requires auth."""
    from datetime import datetime, timedelta, timezone

    drop_result = await db.execute(
        text("""
            SELECT id, total_points_available, points_sold, price_per_point, artist_id
            FROM point_drops
            WHERE track_id = :track_id AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """),
        {"track_id": track_id},
    )
    drop = drop_result.mappings().fetchone()
    if not drop:
        raise HTTPException(status_code=404, detail="No active drop found for this track")

    available = float(drop["total_points_available"]) - float(drop["points_sold"])
    if req.points_qty > available:
        raise HTTPException(status_code=400, detail=f"Only {available} points remaining in this drop")

    # ── Payment verification (BUG FIX: stripe_payment_id must exist and be succeeded) ──
    if not req.stripe_payment_id:
        raise HTTPException(status_code=402, detail="stripe_payment_id is required")
    try:
        import stripe as _stripe
        import os as _os
        _stripe.api_key = _os.getenv("STRIPE_SECRET_KEY")
        pi = _stripe.PaymentIntent.retrieve(req.stripe_payment_id)
        if pi.status != "succeeded":
            raise HTTPException(status_code=402, detail=f"Payment not confirmed (status: {pi.status})")
        pi_user = (pi.metadata or {}).get("user_id", "")
        if pi_user and pi_user != current_user.user_id:
            raise HTTPException(status_code=403, detail="Payment does not belong to this user")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=402, detail=f"Could not verify payment: {e}")

    price_per_point = req.price_per_point or float(drop["price_per_point"])
    gross_amount = round(req.points_qty * price_per_point, 2)
    facilitator_fee = round(gross_amount * 0.05, 2)
    net_amount = round(gross_amount - facilitator_fee, 2)
    marketing_allocation = round(net_amount * 0.80, 2)
    artist_payment = round(net_amount * 0.20, 2)
    # BUG FIX: 365-day hold to match marketing/legal language (was 30)
    holding_ends = datetime.now(timezone.utc) + timedelta(days=365)
    point_id = str(uuid.uuid4())

    await db.execute(
        text("""
            INSERT INTO echo_points (
                id, track_id, buyer_user_id, point_type,
                points_purchased, price_paid, price_per_point,
                holding_period_ends, status, stripe_payment_id
            )
            VALUES (
                :id, :track_id, :buyer_user_id, 'master',
                :points_qty, :price_paid, :price_per_point,
                :holding_ends, 'active', :stripe_payment_id
            )
        """),
        {
            "id": point_id,
            "track_id": track_id,
            "buyer_user_id": current_user.user_id,
            "points_qty": req.points_qty,
            "price_paid": gross_amount,
            "price_per_point": price_per_point,
            "holding_ends": holding_ends,
            "stripe_payment_id": req.stripe_payment_id,
        },
    )

    await db.execute(
        text("""
            UPDATE point_drops
            SET points_sold = points_sold + :qty,
                status = CASE WHEN points_sold + :qty >= total_points_available THEN 'sold_out' ELSE status END
            WHERE id = :drop_id
        """),
        {"qty": req.points_qty, "drop_id": str(drop["id"])},
    )
    await db.commit()

    return {
        "echo_point_id": point_id,
        "track_id": track_id,
        "points_purchased": req.points_qty,
        "price_per_point": price_per_point,
        "gross_amount": gross_amount,
        "facilitator_fee": facilitator_fee,
        "net_amount": net_amount,
        "marketing_allocation": marketing_allocation,
        "artist_payment": artist_payment,
        "holding_period_ends": holding_ends.isoformat(),
        "license": {
            "type": "fractional_master",
            "royalty_per_point": "1% of master streaming revenue per point owned",
            "tradeable_after": holding_ends.isoformat(),
            "disclaimer": "NOT A GUARANTEE — estimated earnings based on comparable data",
        },
    }


# ----------------------------------------------------------------
# Portfolio
# ----------------------------------------------------------------

@router.get("/portfolio/{user_id}")
async def get_portfolio(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """User's full point portfolio. Users see their own; owners see all."""
    if current_user.user_id != user_id and current_user.role not in ("owner",):
        raise HTTPException(status_code=403, detail="Access denied")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    try:
        result = await db.execute(
            text("""
                SELECT
                    ep.id, ep.track_id, ep.points_purchased,
                    ep.price_paid, ep.price_per_point as cost_per_point,
                    ep.royalties_earned, ep.holding_period_ends, ep.status, ep.purchase_date,
                    t.title as track_title, t.genre as track_genre,
                    a.name as artist_name, a.genre as artist_genre, a.profile_photo_url,
                    COALESCE(
                        (SELECT price_per_point FROM exchange_trades
                         WHERE track_id = ep.track_id ORDER BY traded_at DESC LIMIT 1),
                        ep.price_per_point
                    ) as current_price_per_point
                FROM echo_points ep
                JOIN tracks t ON ep.track_id = t.id
                JOIN artists a ON t.artist_id = a.id
                WHERE ep.buyer_user_id = :user_id AND ep.status IN ('active', 'tradeable')
                ORDER BY ep.purchase_date DESC
            """),
            {"user_id": user_id},
        )
        holdings = result.mappings().all()
    except Exception:
        holdings = []

    total_cost_basis = 0.0
    total_current_value = 0.0
    total_royalties = 0.0
    items = []

    for h in holdings:
        pts = float(h.get("points_purchased") or 0)
        cost_per = float(h.get("cost_per_point") or 0)
        current_per = float(h.get("current_price_per_point") or 0)
        cost_basis = round(pts * cost_per, 2)
        current_value = round(pts * current_per, 2)
        unrealized_gain = round(current_value - cost_basis, 2)
        royalties = float(h.get("royalties_earned") or 0)
        total_cost_basis += cost_basis
        total_current_value += current_value
        total_royalties += royalties

        holding_ends = h.get("holding_period_ends")
        tradeable = h.get("status") == "tradeable" or (holding_ends and holding_ends <= now)
        items.append({
            "echo_point_id": str(h["id"]),
            "track_id": str(h["track_id"]),
            "track_title": h.get("track_title"),
            "artist_name": h.get("artist_name"),
            "points_owned": pts,
            "cost_per_point": cost_per,
            "cost_basis": cost_basis,
            "current_price_per_point": current_per,
            "current_value": current_value,
            "unrealized_gain": unrealized_gain,
            "royalties_earned": royalties,
            "status": h.get("status"),
            "holding_period_ends": holding_ends.isoformat() if holding_ends else None,
            "tradeable": tradeable,
        })

    return {
        "user_id": user_id,
        "holdings": items,
        "summary": {
            "total_cost_basis": round(total_cost_basis, 2),
            "total_current_value": round(total_current_value, 2),
            "total_unrealized_gain": round(total_current_value - total_cost_basis, 2),
            "total_royalties_earned": round(total_royalties, 2),
            "num_holdings": len(items),
        },
    }


# ----------------------------------------------------------------
# Exchange — static route BEFORE parameterized
# ----------------------------------------------------------------

@router.post("/exchange/order", status_code=201)
async def place_exchange_order(
    req: ExchangeOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Place a limit buy or sell order on the Exchange."""
    from datetime import datetime, timedelta, timezone

    if req.order_type not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="order_type must be 'buy' or 'sell'")
    if req.points_qty <= 0 or req.price_per_point <= 0:
        raise HTTPException(status_code=400, detail="points_qty and price_per_point must be positive")

    track_id = req.track_id
    echo_point_id = req.echo_point_id

    if req.order_type == "sell":
        if not echo_point_id:
            raise HTTPException(status_code=400, detail="echo_point_id required for sell orders")

        point_result = await db.execute(
            text("SELECT id, track_id, buyer_user_id, holding_period_ends FROM echo_points WHERE id = :id"),
            {"id": echo_point_id},
        )
        point_row = point_result.mappings().fetchone()
        if not point_row:
            raise HTTPException(status_code=404, detail="Echo point not found")
        if str(point_row["buyer_user_id"]) != current_user.user_id:
            raise HTTPException(status_code=403, detail="You do not own these points")
        holding_ends = point_row["holding_period_ends"]
        if holding_ends and holding_ends > datetime.now(timezone.utc):
            days_left = (holding_ends - datetime.now(timezone.utc)).days
            raise HTTPException(status_code=400, detail=f"Holding period not complete. {days_left} days remaining.")
        track_id = str(point_row["track_id"])
    else:
        if not track_id:
            raise HTTPException(status_code=400, detail="track_id required for buy orders")

    order_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    await db.execute(
        text("""
            INSERT INTO exchange_orders (
                id, track_id, user_id, order_type,
                points_qty, price_per_point, status,
                echo_point_id, expires_at
            )
            VALUES (
                :id, :track_id, :user_id, :order_type,
                :points_qty, :price_per_point, 'open',
                :echo_point_id, :expires_at
            )
        """),
        {
            "id": order_id,
            "track_id": track_id,
            "user_id": current_user.user_id,
            "order_type": req.order_type,
            "points_qty": req.points_qty,
            "price_per_point": req.price_per_point,
            "echo_point_id": echo_point_id,
            "expires_at": expires_at,
        },
    )
    await db.commit()

    return {
        "order_id": order_id,
        "track_id": track_id,
        "order_type": req.order_type,
        "points_qty": req.points_qty,
        "price_per_point": req.price_per_point,
        "status": "open",
        "expires_at": expires_at.isoformat(),
    }


@router.get("/exchange/{track_id}")
async def get_exchange_orderbook(
    track_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Exchange order book for a track: bids, asks, recent trades."""
    buy_result = await db.execute(
        text("""
            SELECT id, points_qty, points_filled, price_per_point,
                   points_qty - points_filled as qty_available, created_at
            FROM exchange_orders
            WHERE track_id = :track_id AND order_type = 'buy' AND status = 'open'
            ORDER BY price_per_point DESC LIMIT 20
        """),
        {"track_id": track_id},
    )
    sell_result = await db.execute(
        text("""
            SELECT id, points_qty, points_filled, price_per_point,
                   points_qty - points_filled as qty_available, created_at
            FROM exchange_orders
            WHERE track_id = :track_id AND order_type = 'sell' AND status = 'open'
            ORDER BY price_per_point ASC LIMIT 20
        """),
        {"track_id": track_id},
    )
    trades_result = await db.execute(
        text("""
            SELECT points_qty, price_per_point, gross_amount, traded_at
            FROM exchange_trades
            WHERE track_id = :track_id
            ORDER BY traded_at DESC LIMIT 10
        """),
        {"track_id": track_id},
    )
    last_price_result = await db.execute(
        text("SELECT price_per_point FROM exchange_trades WHERE track_id = :track_id ORDER BY traded_at DESC LIMIT 1"),
        {"track_id": track_id},
    )
    last_price = last_price_result.scalar()

    return {
        "track_id": track_id,
        "last_price": float(last_price) if last_price else None,
        "bids": [_serialize_row(dict(r)) for r in buy_result.mappings().all()],
        "asks": [_serialize_row(dict(r)) for r in sell_result.mappings().all()],
        "recent_trades": [_serialize_row(dict(r)) for r in trades_result.mappings().all()],
    }


# ----------------------------------------------------------------
# Payouts
# ----------------------------------------------------------------

@router.get("/payouts/{user_id}")
async def get_payout_history(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Quarterly payout history for a user."""
    if current_user.user_id != user_id and current_user.role not in ("owner",):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        text("""
            SELECT
                pp.id, pp.track_id, pp.quarter,
                pp.points_held, pp.revenue_pool, pp.payout_amount,
                pp.status, pp.processed_at, pp.created_at,
                t.title as track_title,
                a.name as artist_name
            FROM point_payouts pp
            JOIN tracks t ON pp.track_id = t.id
            JOIN artists a ON t.artist_id = a.id
            WHERE pp.user_id = :user_id
            ORDER BY pp.created_at DESC
        """),
        {"user_id": user_id},
    )
    payouts = result.mappings().all()
    total_earned = sum(float(p.get("payout_amount") or 0) for p in payouts if p.get("status") == "processed")

    return {
        "user_id": user_id,
        "payouts": [_serialize_row(dict(p)) for p in payouts],
        "summary": {
            "total_earned": round(total_earned, 2),
            "total_payouts": len(payouts),
        },
    }


# ----------------------------------------------------------------
# Payout Processing (called by quarterly scheduler)
# ----------------------------------------------------------------

@router.post("/payouts/process")
async def process_quarterly_payouts(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Process quarterly royalty payouts for all eligible point holders.
    Called by APScheduler on Jan/Apr/Jul/Oct 15 at 09:00 UTC.
    Also callable manually by admin.
    Requires X-Service: scheduler header OR admin auth token.
    """
    import logging as _logging
    from datetime import datetime, timezone
    _log = _logging.getLogger(__name__)

    # Auth: accept scheduler service header OR admin JWT
    service_header = request.headers.get("X-Service", "")
    auth_header = request.headers.get("Authorization", "")
    is_admin = False

    if service_header == "scheduler":
        # Trusted internal call from APScheduler
        is_admin = True
    elif auth_header.startswith("Bearer "):
        try:
            from routers.auth import get_current_user, TokenData
            from jose import jwt
            import os as _os
            token = auth_header.split(" ", 1)[1]
            payload = jwt.decode(token, _os.getenv("SECRET_KEY", ""), algorithms=["HS256"])
            if payload.get("role") in ("admin", "owner", "super_admin"):
                is_admin = True
        except Exception:
            pass

    if not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to trigger payouts")

    now = datetime.now(timezone.utc)
    quarter = f"Q{(now.month - 1) // 3 + 1}-{now.year}"
    MIN_PAYOUT = 50.0

    _log.info(f"[payouts] Processing quarterly payouts for {quarter}")

    # Find all active point holdings with undistributed royalties
    holdings_result = await db.execute(
        text("""
            SELECT
                ep.id as echo_point_id,
                ep.buyer_user_id,
                ep.track_id,
                ep.points_purchased,
                COALESCE(
                    (SELECT SUM(net_amount) FROM royalties
                     WHERE track_id = ep.track_id AND distributed = FALSE),
                    0
                ) as revenue_pool
            FROM echo_points ep
            WHERE ep.status IN ('active', 'tradeable')
              AND ep.holding_period_ends IS NOT NULL
            ORDER BY ep.buyer_user_id, ep.track_id
        """)
    )
    holdings = holdings_result.mappings().all()

    payouts_created = 0
    payouts_skipped = 0
    total_distributed = 0.0

    for h in holdings:
        revenue_pool = float(h["revenue_pool"] or 0)
        points_held = float(h["points_purchased"] or 0)
        # Each point = 1% of revenue
        payout_amount = round(revenue_pool * points_held / 100, 2)

        if payout_amount < MIN_PAYOUT:
            payouts_skipped += 1
            continue

        payout_id = str(uuid.uuid4())
        try:
            await db.execute(
                text("""
                    INSERT INTO point_payouts (
                        id, user_id, track_id, echo_point_id,
                        quarter, points_held, revenue_pool,
                        payout_amount, status, processed_at
                    ) VALUES (
                        :id, :user_id, :track_id, :echo_point_id,
                        :quarter, :points_held, :revenue_pool,
                        :payout_amount, 'processed', NOW()
                    )
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": payout_id,
                    "user_id": str(h["buyer_user_id"]),
                    "track_id": str(h["track_id"]),
                    "echo_point_id": str(h["echo_point_id"]),
                    "quarter": quarter,
                    "points_held": points_held,
                    "revenue_pool": revenue_pool,
                    "payout_amount": payout_amount,
                },
            )
            # Update royalties_earned on the echo_point
            await db.execute(
                text("UPDATE echo_points SET royalties_earned = royalties_earned + :amt WHERE id = :id"),
                {"amt": payout_amount, "id": str(h["echo_point_id"])},
            )
            payouts_created += 1
            total_distributed += payout_amount
        except Exception as exc:
            _log.error(f"[payouts] Failed to create payout for {h['echo_point_id']}: {exc}")

    # Mark royalties as distributed
    await db.execute(
        text("UPDATE royalties SET distributed = TRUE WHERE distributed = FALSE")
    )
    await db.commit()

    _log.info(f"[payouts] {quarter} complete: {payouts_created} payouts, ${total_distributed:.2f} distributed")
    return {
        "quarter": quarter,
        "payouts_created": payouts_created,
        "payouts_skipped_below_threshold": payouts_skipped,
        "total_distributed": round(total_distributed, 2),
        "min_payout_threshold": MIN_PAYOUT,
        "processed_at": now.isoformat(),
    }


# ----------------------------------------------------------------
# Drops — static routes BEFORE any parameterized routes
# ----------------------------------------------------------------

@router.get("/drops/create")
async def get_pricing_recommendation(
    artist_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get AI pricing recommendation for a new point drop."""
    artist_result = await db.execute(
        text("SELECT id, name, monthly_listeners, echo_score, genre, tier FROM artists WHERE id = :id"),
        {"id": artist_id},
    )
    artist = artist_result.mappings().fetchone()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    monthly_listeners = int(artist.get("monthly_listeners") or 0)
    echo_score = float(artist.get("echo_score") or 0)

    tier_thresholds = [
        ("new", 10_000), ("rising", 50_000), ("established", 200_000), ("star", float("inf"))
    ]
    tier_price_ranges = {
        "new": (100, 300), "rising": (300, 1500),
        "established": (1500, 8000), "star": (8000, 40000),
    }
    determined_tier = "star"
    for t, max_listeners in tier_thresholds:
        if monthly_listeners <= max_listeners:
            determined_tier = t
            break

    price_range = tier_price_ranges[determined_tier]
    recommended_price = (price_range[0] + price_range[1]) // 2
    confidence = min(100, int(monthly_listeners / 1000 * 0.4 + echo_score * 0.3 + 15))

    return {
        "artist_id": artist_id,
        "artist_name": artist["name"],
        "tier": determined_tier,
        "recommended_price_per_point": recommended_price,
        "price_range": {"min": price_range[0], "max": price_range[1]},
        "max_points_to_sell": 25.0,
        "artist_min_retained": 30.0,
        "ai_confidence_score": confidence,
        "earnings_estimate": _earnings_estimate(monthly_listeners, recommended_price),
        "marketing_rule": "80% of net proceeds go to marketing budget",
        "artist_proceeds_pct": "20% of net proceeds go to artist",
    }


@router.post("/drops/create", status_code=201)
async def create_drop(
    req: CreateDropRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Create a new point drop for a track. Requires admin/owner OR the artist's own account."""
    from datetime import datetime, timedelta, timezone

    # BUG FIX: Any authenticated user could previously create drops for any artist
    if current_user.role not in ("admin", "owner", "super_admin"):
        # Non-admin: verify the artist belongs to this user
        ownership_result = await db.execute(
            text("SELECT id FROM artists WHERE id = :artist_id AND user_id = CAST(:user_id AS UUID) LIMIT 1"),
            {"artist_id": req.artist_id, "user_id": current_user.user_id},
        )
        if not ownership_result.mappings().first():
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to create drops for this artist",
            )

    if req.points_to_sell <= 0 or req.price_per_point <= 0:
        raise HTTPException(status_code=400, detail="points_to_sell and price_per_point must be positive")
    if req.points_to_sell > 25:
        raise HTTPException(status_code=400, detail="Cannot sell more than 25 points per track")

    existing_result = await db.execute(
        text("""
            SELECT COALESCE(SUM(total_points_available), 0) as already_listed
            FROM point_drops WHERE track_id = :track_id AND status IN ('active', 'sold_out')
        """),
        {"track_id": req.track_id},
    )
    already_listed = float(existing_result.scalar() or 0)
    if already_listed + req.points_to_sell > 25:
        raise HTTPException(
            status_code=400,
            detail=f"Total points would exceed 25 per track (already listed: {already_listed})",
        )

    gross_revenue = round(req.points_to_sell * req.price_per_point, 2)
    facilitator_fee = round(gross_revenue * 0.05, 2)
    net_revenue = round(gross_revenue - facilitator_fee, 2)
    marketing_budget = round(net_revenue * 0.80, 2)
    artist_proceeds = round(net_revenue * 0.20, 2)

    artist_result = await db.execute(
        text("SELECT monthly_listeners FROM artists WHERE id = :id"),
        {"id": req.artist_id},
    )
    artist_row = artist_result.mappings().fetchone()
    monthly_listeners = int(artist_row["monthly_listeners"] if artist_row else 0)
    ai_confidence = min(100, int(monthly_listeners / 1000 * 0.4 + 30))

    drop_id = str(uuid.uuid4())
    early_bird_ends = datetime.now(timezone.utc) + timedelta(days=7)
    closes_at = datetime.now(timezone.utc) + timedelta(days=90)

    await db.execute(
        text("""
            INSERT INTO point_drops (
                id, track_id, release_id, artist_id,
                total_points_available, price_per_point,
                early_bird_discount_pct, early_bird_ends_at,
                ai_confidence_score, status, marketing_budget_allocated, closes_at
            )
            VALUES (
                :id, :track_id, :release_id, :artist_id,
                :total_points, :price_per_point,
                :early_bird_discount, :early_bird_ends,
                :confidence, 'active', :marketing_budget, :closes_at
            )
        """),
        {
            "id": drop_id,
            "track_id": req.track_id,
            "release_id": req.release_id,
            "artist_id": req.artist_id,
            "total_points": req.points_to_sell,
            "price_per_point": req.price_per_point,
            "early_bird_discount": req.early_bird_discount_pct,
            "early_bird_ends": early_bird_ends,
            "confidence": ai_confidence,
            "marketing_budget": marketing_budget,
            "closes_at": closes_at,
        },
    )
    await db.commit()

    return {
        "drop_id": drop_id,
        "track_id": req.track_id,
        "points_to_sell": req.points_to_sell,
        "price_per_point": req.price_per_point,
        "revenue_if_sold_out": {
            "gross": gross_revenue,
            "facilitator_fee": facilitator_fee,
            "net": net_revenue,
            "marketing_budget": marketing_budget,
            "artist_proceeds": artist_proceeds,
        },
        "ai_confidence_score": ai_confidence,
        "early_bird_ends_at": early_bird_ends.isoformat(),
        "closes_at": closes_at.isoformat(),
        "status": "active",
    }


# ----------------------------------------------------------------
# AI Confidence Score
# ----------------------------------------------------------------

@router.get("/confidence/{artist_id}")
async def get_ai_confidence_score(
    artist_id: str,
    db: AsyncSession = Depends(get_db),
):
    """AI confidence score for an artist (public endpoint)."""
    artist_result = await db.execute(
        text("SELECT id, name, monthly_listeners, echo_score, genre, tier, total_streams FROM artists WHERE id = :id"),
        {"id": artist_id},
    )
    artist = artist_result.mappings().fetchone()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    monthly_listeners = int(artist.get("monthly_listeners") or 0)
    total_streams = int(artist.get("total_streams") or 0)
    echo_score = float(artist.get("echo_score") or 0)

    listeners_score = (
        min(30, int(math.log10(monthly_listeners + 1) / math.log10(1_000_001) * 30))
        if monthly_listeners > 0 else 0
    )
    growth_score = min(25, int(echo_score / 100 * 25))
    engagement_score = (
        min(20, int(total_streams / (monthly_listeners * 12) / 100 * 20))
        if monthly_listeners > 0 and total_streams > 0 else 5
    )
    track_count_result = await db.execute(
        text("SELECT COUNT(*) FROM tracks WHERE artist_id = :id AND created_at >= NOW() - INTERVAL '12 months'"),
        {"id": artist_id},
    )
    track_count = int(track_count_result.scalar() or 0)
    consistency_score = min(15, track_count * 3)

    total_score = listeners_score + growth_score + engagement_score + consistency_score

    return {
        "artist_id": artist_id,
        "artist_name": artist["name"],
        "ai_confidence_score": total_score,
        "breakdown": {
            "monthly_listeners": {"score": listeners_score, "max": 30, "value": monthly_listeners},
            "growth_signal": {"score": growth_score, "max": 25, "value": echo_score},
            "engagement": {"score": engagement_score, "max": 20},
            "release_consistency": {"score": consistency_score, "max": 15, "tracks_last_12mo": track_count},
        },
        "disclaimer": "NOT A GUARANTEE — predictive estimate based on comparable data",
    }
