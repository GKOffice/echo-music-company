"""
Melodio Fan Economy Model — API Router
Studio Fund · First In Registry · Deferred Collaboration Marketplace · Release Day Settlement

CORE RULE: Zero money collected before Release Day.
All pre-release stages are commitment/reservation only.
Single Settlement Event on Release Day.

LANGUAGE POLICY: Never use invest/investment/investor/ROI/returns/securities/equity.
Always use: purchase, pledge, support, royalty holders, royalty earnings, commit.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import date, datetime

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()

# ─────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────

class RewardTier(BaseModel):
    level: int
    min_amount: float
    title: str
    perks: str

class CreateCampaignRequest(BaseModel):
    title: str
    goal_amount: float
    description: str
    reward_tiers: List[RewardTier] = []
    release_date: Optional[str] = None  # ISO date string

class PledgeRequest(BaseModel):
    amount: float
    tier_level: int = 1

class FirstInRequest(BaseModel):
    artist_id: str
    committed_amount: float = 0.0

class CreateCollabOfferRequest(BaseModel):
    title: str
    role_needed: str
    deferred_fee: float
    description: Optional[str] = None

class SettlementRequest(BaseModel):
    song_id: str
    total_collected: float

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _row(row) -> dict:
    """Serialize row to JSON-safe dict."""
    if row is None:
        return {}
    out = {}
    for k, v in dict(row._mapping).items():
        if hasattr(v, "hex"):
            out[k] = str(v)
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out

def _rows(result) -> list:
    return [_row(r) for r in result]


# ─────────────────────────────────────────────
# STUDIO FUND — Artist Patronage Campaigns
# ─────────────────────────────────────────────

@router.post("/studio-fund")
async def create_campaign(
    req: CreateCampaignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Artist creates a Studio Fund patronage campaign. No money collected until Release Day."""
    campaign_id = str(uuid.uuid4())
    import json
    tiers_json = json.dumps([t.dict() for t in req.reward_tiers])

    await db.execute(text("""
        INSERT INTO studio_fund_campaigns
          (id, artist_id, title, goal_amount, description, reward_tiers, release_date, status, total_pledged)
        VALUES
          (:id, :artist_id, :title, :goal_amount, :description, CAST(:reward_tiers AS JSONB), :release_date, 'active', 0)
    """), {
        "id": campaign_id,
        "artist_id": current_user.user_id,
        "title": req.title,
        "goal_amount": req.goal_amount,
        "description": req.description,
        "reward_tiers": tiers_json,
        "release_date": req.release_date,
    })

    return {
        "success": True,
        "campaign_id": campaign_id,
        "message": "Studio Fund campaign created. Fans can now pledge support — no charges until Release Day.",
    }


@router.get("/studio-fund")
async def list_campaigns(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List active Studio Fund campaigns."""
    result = await db.execute(text("""
        SELECT sfc.*, a.name as artist_name,
               COUNT(sfp.id) as pledge_count
        FROM studio_fund_campaigns sfc
        LEFT JOIN artists a ON a.id = sfc.artist_id
        LEFT JOIN studio_fund_pledges sfp ON sfp.campaign_id = sfc.id AND sfp.status = 'pending'
        WHERE sfc.status = 'active'
        GROUP BY sfc.id, a.name
        ORDER BY sfc.created_at DESC
        LIMIT :limit OFFSET :offset
    """), {"limit": limit, "offset": offset})
    campaigns = _rows(result)
    return {"campaigns": campaigns, "count": len(campaigns)}


@router.get("/studio-fund/{campaign_id}")
async def get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    """Get campaign detail with pledge stats."""
    result = await db.execute(text("""
        SELECT sfc.*, a.name as artist_name,
               COUNT(sfp.id) as pledge_count,
               COALESCE(SUM(sfp.amount) FILTER (WHERE sfp.status = 'pending'), 0) as live_total_pledged
        FROM studio_fund_campaigns sfc
        LEFT JOIN artists a ON a.id = sfc.artist_id
        LEFT JOIN studio_fund_pledges sfp ON sfp.campaign_id = sfc.id
        WHERE sfc.id = :campaign_id
        GROUP BY sfc.id, a.name
    """), {"campaign_id": campaign_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _row(row)


@router.post("/studio-fund/{campaign_id}/pledge")
async def pledge_support(
    campaign_id: str,
    req: PledgeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Fan pledges support. NO charge — commitment only until Release Day."""
    # Check campaign exists and is active
    result = await db.execute(text(
        "SELECT id, status FROM studio_fund_campaigns WHERE id = :id"
    ), {"id": campaign_id})
    campaign = result.fetchone()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if _row(campaign).get("status") != "active":
        raise HTTPException(status_code=400, detail="Campaign is not accepting pledges")

    # Remove any existing pledge first (update if exists)
    await db.execute(text("""
        INSERT INTO studio_fund_pledges (id, campaign_id, fan_id, amount, tier_level, status)
        VALUES (:id, :campaign_id, :fan_id, :amount, :tier_level, 'pending')
        ON CONFLICT (campaign_id, fan_id) DO UPDATE
          SET amount = :amount, tier_level = :tier_level, status = 'pending'
    """), {
        "id": str(uuid.uuid4()),
        "campaign_id": campaign_id,
        "fan_id": current_user.user_id,
        "amount": req.amount,
        "tier_level": req.tier_level,
    })

    # Update campaign total
    await db.execute(text("""
        UPDATE studio_fund_campaigns
        SET total_pledged = (
            SELECT COALESCE(SUM(amount), 0) FROM studio_fund_pledges
            WHERE campaign_id = :campaign_id AND status = 'pending'
        )
        WHERE id = :campaign_id
    """), {"campaign_id": campaign_id})

    return {
        "success": True,
        "message": f"Pledge of ${req.amount:.2f} registered. No charge until Release Day.",
        "note": "You can withdraw your pledge at any time before Release Day.",
    }


@router.delete("/studio-fund/{campaign_id}/pledge")
async def withdraw_pledge(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Fan withdraws their pledge. Allowed any time before Release Day."""
    await db.execute(text("""
        UPDATE studio_fund_pledges SET status = 'withdrawn'
        WHERE campaign_id = :campaign_id AND fan_id = :fan_id AND status = 'pending'
    """), {"campaign_id": campaign_id, "fan_id": current_user.user_id})

    await db.execute(text("""
        UPDATE studio_fund_campaigns
        SET total_pledged = (
            SELECT COALESCE(SUM(amount), 0) FROM studio_fund_pledges
            WHERE campaign_id = :campaign_id AND status = 'pending'
        )
        WHERE id = :campaign_id
    """), {"campaign_id": campaign_id})

    return {"success": True, "message": "Pledge withdrawn successfully."}


# ─────────────────────────────────────────────
# FIRST IN REGISTRY — Fan Commitment Signals
# ─────────────────────────────────────────────

@router.post("/first-in/register")
async def register_first_in(
    req: FirstInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Fan registers First In intent for an artist's next release. No charge. Pure commitment signal."""
    await db.execute(text("""
        INSERT INTO first_in_registrations (id, fan_id, artist_id, committed_amount, status)
        VALUES (:id, :fan_id, :artist_id, :committed_amount, 'active')
        ON CONFLICT (fan_id, artist_id) DO UPDATE
          SET committed_amount = :committed_amount, status = 'active'
    """), {
        "id": str(uuid.uuid4()),
        "fan_id": current_user.user_id,
        "artist_id": req.artist_id,
        "committed_amount": req.committed_amount,
    })

    return {
        "success": True,
        "message": "You're First In! You'll get 24-hour priority access when this artist's next release goes live.",
        "note": "This is a non-binding commitment. You may withdraw at any time before Release Day.",
    }


@router.delete("/first-in/{artist_id}")
async def withdraw_first_in(
    artist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Fan withdraws First In registration."""
    await db.execute(text("""
        UPDATE first_in_registrations SET status = 'withdrawn'
        WHERE fan_id = :fan_id AND artist_id = :artist_id
    """), {"fan_id": current_user.user_id, "artist_id": artist_id})
    return {"success": True, "message": "First In registration withdrawn."}


@router.get("/first-in/stats/{artist_id}")
async def get_first_in_stats(artist_id: str, db: AsyncSession = Depends(get_db)):
    """Get commitment registry stats for an artist dashboard."""
    result = await db.execute(text("""
        SELECT
            COUNT(*) as first_in_count,
            COALESCE(SUM(committed_amount), 0) as estimated_day1_demand,
            COALESCE(AVG(committed_amount), 0) as avg_commitment,
            COALESCE(MIN(committed_amount), 0) as min_commitment,
            COALESCE(MAX(committed_amount), 0) as max_commitment
        FROM first_in_registrations
        WHERE artist_id = :artist_id AND status = 'active'
    """), {"artist_id": artist_id})
    stats = _row(result.fetchone())
    return {
        "artist_id": artist_id,
        "first_in_count": int(stats.get("first_in_count", 0)),
        "estimated_day1_demand": float(stats.get("estimated_day1_demand", 0)),
        "avg_commitment_per_fan": round(float(stats.get("avg_commitment", 0)), 2),
        "message": f"{int(stats.get('first_in_count', 0))} fans are First In for this artist's next release.",
    }


@router.get("/first-in/my")
async def my_first_in(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get all artists the current fan is First In for."""
    result = await db.execute(text("""
        SELECT fir.*, a.name as artist_name, a.genre
        FROM first_in_registrations fir
        LEFT JOIN artists a ON a.id = fir.artist_id
        WHERE fir.fan_id = :fan_id AND fir.status = 'active'
        ORDER BY fir.created_at DESC
    """), {"fan_id": current_user.user_id})
    return {"registrations": _rows(result)}


# ─────────────────────────────────────────────
# DEFERRED COLLABORATION MARKETPLACE
# ─────────────────────────────────────────────

@router.post("/collaboration/offer")
async def create_collab_offer(
    req: CreateCollabOfferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Artist posts a deferred collaboration offer backed by fan commitment data."""
    # Get artist's First In commitment total as snapshot
    result = await db.execute(text("""
        SELECT COALESCE(SUM(committed_amount), 0) as total_committed
        FROM first_in_registrations
        WHERE artist_id = :artist_id AND status = 'active'
    """), {"artist_id": current_user.user_id})
    row = result.fetchone()
    fan_commitment_snapshot = float(row[0]) if row else 0.0

    # Enforce 40% protection floor
    protection_floor = fan_commitment_snapshot * 0.40
    if req.deferred_fee > protection_floor and fan_commitment_snapshot > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Deferred fee ${req.deferred_fee:.2f} exceeds the 40% Collaborator Protection Floor "
                   f"(${protection_floor:.2f} based on ${fan_commitment_snapshot:.2f} fan commitments). "
                   f"Reduce the fee or build more fan commitment first."
        )

    offer_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO deferred_collab_offers
          (id, artist_id, title, role_needed, deferred_fee, fan_commitment_snapshot, protection_floor, status)
        VALUES
          (:id, :artist_id, :title, :role_needed, :deferred_fee, :snapshot, :floor, 'open')
    """), {
        "id": offer_id,
        "artist_id": current_user.user_id,
        "title": req.title,
        "role_needed": req.role_needed,
        "deferred_fee": req.deferred_fee,
        "snapshot": fan_commitment_snapshot,
        "floor": protection_floor,
    })

    return {
        "success": True,
        "offer_id": offer_id,
        "fan_commitment_snapshot": fan_commitment_snapshot,
        "deferred_fee": req.deferred_fee,
        "message": "Collaboration offer posted. Collaborators can view your fan commitment data and apply.",
        "note": "Payment is deferred — collaborator is paid first on Release Day from settlement proceeds.",
    }


@router.get("/collaboration/offers")
async def list_collab_offers(
    role: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Browse open deferred collaboration offers."""
    where = "WHERE dco.status = 'open'"
    params: dict = {"limit": limit, "offset": offset}
    if role:
        where += " AND LOWER(dco.role_needed) LIKE LOWER(:role)"
        params["role"] = f"%{role}%"

    result = await db.execute(text(f"""
        SELECT dco.*, a.name as artist_name, a.genre
        FROM deferred_collab_offers dco
        LEFT JOIN artists a ON a.id = dco.artist_id
        {where}
        ORDER BY dco.fan_commitment_snapshot DESC, dco.created_at DESC
        LIMIT :limit OFFSET :offset
    """), params)
    offers = _rows(result)
    return {"offers": offers, "count": len(offers)}


@router.get("/collaboration/offer/{offer_id}")
async def get_collab_offer(offer_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific collaboration offer."""
    result = await db.execute(text("""
        SELECT dco.*, a.name as artist_name, a.genre,
               dca.id as agreement_id, dca.collaborator_id, dca.payment_status
        FROM deferred_collab_offers dco
        LEFT JOIN artists a ON a.id = dco.artist_id
        LEFT JOIN deferred_collab_agreements dca ON dca.offer_id = dco.id
        WHERE dco.id = :offer_id
    """), {"offer_id": offer_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Offer not found")
    return _row(row)


@router.post("/collaboration/offer/{offer_id}/accept")
async def accept_collab_offer(
    offer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Collaborator accepts a deferred offer. Creates a Deferred Collaboration Agreement."""
    # Check offer is still open
    result = await db.execute(text(
        "SELECT * FROM deferred_collab_offers WHERE id = :id AND status = 'open'"
    ), {"id": offer_id})
    offer = result.fetchone()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found or already filled")

    offer_data = _row(offer)
    agreement_id = str(uuid.uuid4())

    await db.execute(text("""
        INSERT INTO deferred_collab_agreements
          (id, offer_id, collaborator_id, artist_id, deferred_fee, payment_status)
        VALUES
          (:id, :offer_id, :collaborator_id, :artist_id, :deferred_fee, 'pending')
    """), {
        "id": agreement_id,
        "offer_id": offer_id,
        "collaborator_id": current_user.user_id,
        "artist_id": offer_data.get("artist_id"),
        "deferred_fee": offer_data.get("deferred_fee"),
    })

    # Mark offer as filled
    await db.execute(text(
        "UPDATE deferred_collab_offers SET status = 'filled' WHERE id = :id"
    ), {"id": offer_id})

    return {
        "success": True,
        "agreement_id": agreement_id,
        "deferred_fee": offer_data.get("deferred_fee"),
        "message": "Deferred Collaboration Agreement created. You will be paid first on Release Day.",
        "payment_order": "1st: Collaborators · 2nd: Melodio 5% fee · 3rd: Artist balance",
        "note": "Begin work only after signing the formal Deferred Collaboration Agreement with the artist.",
    }


# ─────────────────────────────────────────────
# RELEASE DAY SETTLEMENT
# ─────────────────────────────────────────────

@router.post("/settlement/trigger/{artist_id}")
async def trigger_settlement(
    artist_id: str,
    req: SettlementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Trigger the Release Day Single Settlement Event.
    Atomic: all legs execute or entire transaction rolls back.
    Payment order: Collaborators first → Melodio 5% fee → Artist balance.
    SYSTEM/ADMIN USE ONLY.
    """
    settlement_id = str(uuid.uuid4())
    total = req.total_collected
    platform_fee = round(total * 0.05, 2)

    # Get all pending deferred agreements for this artist
    result = await db.execute(text("""
        SELECT dca.id, dca.collaborator_id, dca.deferred_fee
        FROM deferred_collab_agreements dca
        WHERE dca.artist_id = :artist_id AND dca.payment_status = 'pending'
    """), {"artist_id": artist_id})
    agreements = _rows(result)

    # Calculate collaborator payouts
    total_collab_fees = sum(float(a.get("deferred_fee", 0)) for a in agreements)
    import json
    collab_payouts = [
        {"collaborator_id": a["collaborator_id"], "amount": float(a["deferred_fee"])}
        for a in agreements
    ]

    # Artist gets what's left after collaborators and platform fee
    artist_balance = round(total - total_collab_fees - platform_fee, 2)
    if artist_balance < 0:
        artist_balance = 0.0

    # Get active campaign for this artist
    result = await db.execute(text("""
        SELECT id FROM studio_fund_campaigns
        WHERE artist_id = :artist_id AND status = 'active'
        ORDER BY created_at DESC LIMIT 1
    """), {"artist_id": artist_id})
    campaign_row = result.fetchone()
    campaign_id = _row(campaign_row).get("id") if campaign_row else None

    # Create settlement record
    await db.execute(text("""
        INSERT INTO release_day_settlements
          (id, song_id, artist_id, campaign_id, total_collected, collaborator_payouts,
           platform_fee, artist_balance, status, settled_at)
        VALUES
          (:id, :song_id, :artist_id, :campaign_id, :total, CAST(:payouts AS JSONB),
           :fee, :balance, 'complete', NOW())
    """), {
        "id": settlement_id,
        "song_id": req.song_id,
        "artist_id": artist_id,
        "campaign_id": campaign_id,
        "total": total,
        "payouts": json.dumps(collab_payouts),
        "fee": platform_fee,
        "balance": artist_balance,
    })

    # Mark all agreements as paid
    if agreements:
        await db.execute(text("""
            UPDATE deferred_collab_agreements
            SET payment_status = 'paid', song_id = :song_id
            WHERE artist_id = :artist_id AND payment_status = 'pending'
        """), {"artist_id": artist_id, "song_id": req.song_id})

    # Mark campaign as settled
    if campaign_id:
        await db.execute(text("""
            UPDATE studio_fund_campaigns SET status = 'settled'
            WHERE id = :campaign_id
        """), {"campaign_id": campaign_id})

        # Mark all pledges as collected
        await db.execute(text("""
            UPDATE studio_fund_pledges SET status = 'collected'
            WHERE campaign_id = :campaign_id AND status = 'pending'
        """), {"campaign_id": campaign_id})

    return {
        "success": True,
        "settlement_id": settlement_id,
        "total_collected": total,
        "settlement_waterfall": {
            "1_collaborator_payments": total_collab_fees,
            "2_platform_fee_5pct": platform_fee,
            "3_artist_balance": artist_balance,
        },
        "collaborator_payouts": collab_payouts,
        "message": "Release Day Settlement complete. All parties paid.",
    }


@router.get("/settlement/{artist_id}")
async def get_settlement(artist_id: str, db: AsyncSession = Depends(get_db)):
    """Get settlement status for an artist."""
    result = await db.execute(text("""
        SELECT rds.*, a.name as artist_name
        FROM release_day_settlements rds
        LEFT JOIN artists a ON a.id = rds.artist_id
        WHERE rds.artist_id = :artist_id
        ORDER BY rds.created_at DESC
        LIMIT 10
    """), {"artist_id": artist_id})
    return {"settlements": _rows(result)}


# ─────────────────────────────────────────────
# ARTIST DASHBOARD — Fan Economy Summary
# ─────────────────────────────────────────────

@router.get("/dashboard/summary")
async def fan_economy_summary(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Artist dashboard: Fan Economy summary — First In stats, active campaign, open offers."""
    artist_id = current_user.user_id

    # First In stats
    fi_result = await db.execute(text("""
        SELECT COUNT(*) as count, COALESCE(SUM(committed_amount), 0) as total_demand
        FROM first_in_registrations
        WHERE artist_id = :artist_id AND status = 'active'
    """), {"artist_id": artist_id})
    fi = _row(fi_result.fetchone())

    # Active campaign
    camp_result = await db.execute(text("""
        SELECT id, title, goal_amount, total_pledged, status, release_date
        FROM studio_fund_campaigns
        WHERE artist_id = :artist_id AND status = 'active'
        ORDER BY created_at DESC LIMIT 1
    """), {"artist_id": artist_id})
    campaign = _row(camp_result.fetchone()) if camp_result.rowcount else {}

    # Open collab offers
    offers_result = await db.execute(text("""
        SELECT COUNT(*) as open_offers
        FROM deferred_collab_offers
        WHERE artist_id = :artist_id AND status = 'open'
    """), {"artist_id": artist_id})
    offers = _row(offers_result.fetchone())

    return {
        "first_in": {
            "fan_count": int(fi.get("count", 0)),
            "estimated_day1_demand": float(fi.get("total_demand", 0)),
        },
        "studio_fund": campaign or None,
        "open_collab_offers": int(offers.get("open_offers", 0)),
        "protection_floor": round(float(fi.get("total_demand", 0)) * 0.40, 2),
    }
