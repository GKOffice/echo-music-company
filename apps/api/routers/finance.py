from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import uuid
import json

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()


# ----------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------

class RoyaltyCreate(BaseModel):
    artist_id: str
    track_id: Optional[str] = None
    release_id: Optional[str] = None
    source: str  # streaming|mechanical|performance|sync|youtube|neighboring|print
    platform: Optional[str] = None
    gross_amount: float
    net_amount: float
    currency: str = "USD"
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class ExpenseCreate(BaseModel):
    artist_id: Optional[str] = None
    release_id: Optional[str] = None
    category: str  # recording|marketing|distribution|legal|creative|advance|other
    amount: float
    recoupable: bool = False
    description: Optional[str] = None
    vendor: Optional[str] = None


# ----------------------------------------------------------------
# Label P&L Overview
# ----------------------------------------------------------------

@router.get("/overview")
async def get_label_overview(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Label-wide P&L overview."""
    royalties_result = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(gross_amount), 0) AS total_gross,
                COALESCE(SUM(net_amount), 0) AS total_net,
                COUNT(*) AS royalty_records,
                COUNT(DISTINCT artist_id) AS artists_with_royalties,
                COALESCE(SUM(CASE WHEN distributed = TRUE THEN net_amount ELSE 0 END), 0) AS total_distributed,
                COALESCE(SUM(CASE WHEN distributed = FALSE THEN net_amount ELSE 0 END), 0) AS pending_distribution
            FROM royalties
        """)
    )
    royalties = dict(royalties_result.mappings().fetchone())

    expenses_result = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(amount), 0) AS total_expenses,
                COALESCE(SUM(CASE WHEN recoupable THEN amount ELSE 0 END), 0) AS recoupable_total,
                COALESCE(SUM(CASE WHEN NOT recoupable THEN amount ELSE 0 END), 0) AS non_recoupable_total
            FROM expenses
        """)
    )
    expenses = dict(expenses_result.mappings().fetchone())

    points_result = await db.execute(
        text("SELECT COALESCE(SUM(price_paid), 0) AS total_points_revenue FROM echo_points WHERE status = 'active'")
    )
    points = dict(points_result.mappings().fetchone())

    artists_result = await db.execute(
        text("SELECT COUNT(*) AS total, COUNT(CASE WHEN status = 'signed' THEN 1 END) AS signed FROM artists")
    )
    artists = dict(artists_result.mappings().fetchone())

    total_revenue = float(royalties["total_net"]) + float(points["total_points_revenue"])
    net_profit = total_revenue - float(expenses["total_expenses"])

    return {
        "revenue": {
            "royalties_gross": float(royalties["total_gross"]),
            "royalties_net": float(royalties["total_net"]),
            "points_store": float(points["total_points_revenue"]),
            "total": total_revenue,
        },
        "expenses": {
            "total": float(expenses["total_expenses"]),
            "recoupable": float(expenses["recoupable_total"]),
            "non_recoupable": float(expenses["non_recoupable_total"]),
        },
        "distributions": {
            "paid_out": float(royalties["total_distributed"]),
            "pending": float(royalties["pending_distribution"]),
        },
        "artists": {
            "total": int(artists["total"]),
            "signed": int(artists["signed"]),
        },
        "net_profit": net_profit,
        "royalty_records": int(royalties["royalty_records"]),
    }


# ----------------------------------------------------------------
# Per-Artist Revenue
# ----------------------------------------------------------------

@router.get("/artists/{artist_id}")
async def get_artist_finance(
    artist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Per-artist revenue, expenses, and recoupment status."""
    artist_result = await db.execute(
        text("SELECT id, name, stage_name, advance_amount, recoupment_balance FROM artists WHERE id = :id"),
        {"id": artist_id},
    )
    artist = artist_result.mappings().fetchone()
    if not artist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")

    royalties_result = await db.execute(
        text("""
            SELECT COALESCE(SUM(gross_amount), 0) AS gross, COALESCE(SUM(net_amount), 0) AS net,
                   COUNT(*) AS records
            FROM royalties WHERE artist_id = :id
        """),
        {"id": artist_id},
    )
    royalties = dict(royalties_result.mappings().fetchone())

    expenses_result = await db.execute(
        text("""
            SELECT category, COALESCE(SUM(amount), 0) AS total,
                   COALESCE(SUM(CASE WHEN recoupable THEN amount ELSE 0 END), 0) AS recoupable
            FROM expenses WHERE artist_id = :id GROUP BY category
        """),
        {"id": artist_id},
    )
    expenses_by_cat = [dict(r) for r in expenses_result.mappings().all()]
    total_expenses = sum(float(e["total"]) for e in expenses_by_cat)

    advance = float(artist["advance_amount"])
    recoupment_balance = float(artist["recoupment_balance"])
    fully_recouped = recoupment_balance <= 0

    return {
        "artist_id": artist_id,
        "artist_name": artist["stage_name"] or artist["name"],
        "revenue": {
            "gross": float(royalties["gross"]),
            "net": float(royalties["net"]),
            "royalty_records": int(royalties["records"]),
        },
        "expenses": {
            "total": total_expenses,
            "by_category": expenses_by_cat,
        },
        "recoupment": {
            "advance": advance,
            "balance_remaining": recoupment_balance,
            "fully_recouped": fully_recouped,
            "split": "60/40 (artist/label)" if fully_recouped else "40/60 (artist/label)",
        },
        "net_profit": float(royalties["net"]) - total_expenses,
    }


# ----------------------------------------------------------------
# Royalties
# ----------------------------------------------------------------

@router.get("/royalties")
async def list_royalties(
    artist_id: Optional[str] = Query(None),
    distributed: Optional[bool] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if artist_id:
        conditions.append("artist_id = :artist_id")
        params["artist_id"] = artist_id
    if distributed is not None:
        conditions.append("distributed = :distributed")
        params["distributed"] = distributed
    if source:
        conditions.append("source = :source")
        params["source"] = source

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"SELECT * FROM royalties WHERE {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
        params,
    )
    rows = [dict(r) for r in result.mappings().all()]

    total_result = await db.execute(
        text(f"SELECT COUNT(*) FROM royalties WHERE {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    total = total_result.scalar()

    return {"royalties": rows, "total": total, "limit": limit, "offset": offset}


@router.post("/royalties", status_code=status.HTTP_201_CREATED)
async def create_royalty(
    royalty_in: RoyaltyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    royalty_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO royalties (id, artist_id, track_id, release_id, source, platform,
                gross_amount, net_amount, currency, period_start, period_end, reported_by_agent)
            VALUES (:id, :artist_id, :track_id, :release_id, :source, :platform,
                :gross, :net, :currency, :period_start, :period_end, 'api')
        """),
        {
            "id": royalty_id,
            "artist_id": royalty_in.artist_id,
            "track_id": royalty_in.track_id,
            "release_id": royalty_in.release_id,
            "source": royalty_in.source,
            "platform": royalty_in.platform,
            "gross": royalty_in.gross_amount,
            "net": royalty_in.net_amount,
            "currency": royalty_in.currency,
            "period_start": royalty_in.period_start,
            "period_end": royalty_in.period_end,
        },
    )
    await db.commit()
    return {"id": royalty_id, "message": "Royalty entry created"}


# ----------------------------------------------------------------
# Payout Preview
# ----------------------------------------------------------------

@router.get("/payout-preview")
async def get_payout_preview(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Preview next quarterly payout amounts per artist."""
    result = await db.execute(
        text("""
            SELECT artist_id, COALESCE(SUM(net_amount), 0) AS pending_amount,
                   COUNT(*) AS royalty_count
            FROM royalties
            WHERE distributed = FALSE
            GROUP BY artist_id
            ORDER BY pending_amount DESC
        """)
    )
    rows = result.mappings().all()

    payouts = []
    skipped = []
    total = 0.0
    MIN_THRESHOLD = 50.0

    for row in rows:
        amt = float(row["pending_amount"])
        entry = {
            "artist_id": str(row["artist_id"]),
            "pending_amount": amt,
            "royalty_count": int(row["royalty_count"]),
        }
        if amt >= MIN_THRESHOLD:
            payouts.append(entry)
            total += amt
        else:
            entry["reason"] = f"Below ${MIN_THRESHOLD} threshold"
            skipped.append(entry)

    # Next payout date
    from datetime import date as dt
    today = dt.today()
    quarterly_months = {1: 15, 4: 15, 7: 15, 10: 15}
    next_date = None
    for month in sorted(quarterly_months.keys()):
        candidate = dt(today.year, month, quarterly_months[month])
        if candidate >= today:
            next_date = candidate
            break
    if not next_date:
        first_month = sorted(quarterly_months.keys())[0]
        next_date = dt(today.year + 1, first_month, quarterly_months[first_month])

    return {
        "next_payout_date": next_date.isoformat(),
        "payouts": payouts,
        "skipped": skipped,
        "total_to_pay": total,
        "artists_qualifying": len(payouts),
        "artists_below_threshold": len(skipped),
        "min_threshold": MIN_THRESHOLD,
    }


# ----------------------------------------------------------------
# Expenses
# ----------------------------------------------------------------

@router.get("/expenses")
async def list_expenses(
    artist_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    recoupable: Optional[bool] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if artist_id:
        conditions.append("artist_id = :artist_id")
        params["artist_id"] = artist_id
    if category:
        conditions.append("category = :category")
        params["category"] = category
    if recoupable is not None:
        conditions.append("recoupable = :recoupable")
        params["recoupable"] = recoupable

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"SELECT * FROM expenses WHERE {where} ORDER BY paid_at DESC LIMIT :limit OFFSET :offset"),
        params,
    )
    rows = [dict(r) for r in result.mappings().all()]

    total_result = await db.execute(
        text(f"SELECT COUNT(*), COALESCE(SUM(amount), 0) AS total_amount FROM expenses WHERE {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    summary = total_result.mappings().fetchone()

    return {
        "expenses": rows,
        "total_count": int(summary["count"]),
        "total_amount": float(summary["total_amount"]),
        "limit": limit,
        "offset": offset,
    }


@router.post("/expenses", status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_in: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    expense_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO expenses (id, artist_id, release_id, category, amount,
                recoupable, description, vendor, created_by)
            VALUES (:id, :artist_id, :release_id, :category, :amount,
                :recoupable, :description, :vendor, 'api')
        """),
        {
            "id": expense_id,
            "artist_id": expense_in.artist_id,
            "release_id": expense_in.release_id,
            "category": expense_in.category,
            "amount": expense_in.amount,
            "recoupable": expense_in.recoupable,
            "description": expense_in.description,
            "vendor": expense_in.vendor,
        },
    )

    # If recoupable, update artist's recoupment balance
    if expense_in.recoupable and expense_in.artist_id:
        await db.execute(
            text("UPDATE artists SET recoupment_balance = recoupment_balance + :amount, updated_at = NOW() WHERE id = :id"),
            {"amount": expense_in.amount, "id": expense_in.artist_id},
        )

    await db.commit()
    return {"id": expense_id, "message": "Expense logged"}
