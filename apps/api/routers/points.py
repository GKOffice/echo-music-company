from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import uuid

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()


class PointPurchase(BaseModel):
    track_id: Optional[str] = None
    release_id: Optional[str] = None
    point_type: str
    points_purchased: float
    price_paid: float
    stripe_payment_id: Optional[str] = None


@router.post("/purchase", status_code=status.HTTP_201_CREATED)
async def purchase_points(
    purchase: PointPurchase,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    valid_types = {"master", "publishing", "bundle"}
    if purchase.point_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"point_type must be one of: {', '.join(valid_types)}",
        )

    if not purchase.track_id and not purchase.release_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="track_id or release_id required",
        )

    if purchase.points_purchased <= 0 or purchase.price_paid <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="points_purchased and price_paid must be positive",
        )

    price_per_point = purchase.price_paid / purchase.points_purchased
    point_id = str(uuid.uuid4())

    from datetime import datetime, timedelta, timezone
    holding_period_ends = datetime.now(timezone.utc) + timedelta(days=365)

    await db.execute(
        text(
            """
            INSERT INTO echo_points (id, track_id, release_id, buyer_user_id, point_type,
              points_purchased, price_paid, price_per_point, holding_period_ends, stripe_payment_id)
            VALUES (:id, :track_id, :release_id, :buyer_user_id, :point_type,
              :points_purchased, :price_paid, :price_per_point, :holding_period_ends, :stripe_payment_id)
            """
        ),
        {
            "id": point_id,
            "track_id": purchase.track_id,
            "release_id": purchase.release_id,
            "buyer_user_id": current_user.user_id,
            "point_type": purchase.point_type,
            "points_purchased": purchase.points_purchased,
            "price_paid": purchase.price_paid,
            "price_per_point": price_per_point,
            "holding_period_ends": holding_period_ends,
            "stripe_payment_id": purchase.stripe_payment_id,
        },
    )
    await db.commit()
    return {"id": point_id, "message": "Points purchased", "price_per_point": price_per_point}


@router.get("/my-portfolio")
async def get_my_portfolio(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text(
            """
            SELECT ep.*, t.title as track_title, r.title as release_title,
              a.name as artist_name
            FROM echo_points ep
            LEFT JOIN tracks t ON ep.track_id = t.id
            LEFT JOIN releases r ON ep.release_id = r.id
            LEFT JOIN artists a ON r.artist_id = a.id
            WHERE ep.buyer_user_id = :user_id AND ep.status = 'active'
            ORDER BY ep.purchase_date DESC
            """
        ),
        {"user_id": current_user.user_id},
    )
    points = result.mappings().all()

    totals = await db.execute(
        text(
            """
            SELECT
              COALESCE(SUM(price_paid), 0) as total_invested,
              COALESCE(SUM(royalties_earned), 0) as total_royalties,
              COALESCE(SUM(points_purchased), 0) as total_points
            FROM echo_points
            WHERE buyer_user_id = :user_id AND status = 'active'
            """
        ),
        {"user_id": current_user.user_id},
    )
    totals_row = totals.fetchone()

    return {
        "holdings": [dict(p) for p in points],
        "summary": {
            "total_invested": float(totals_row.total_invested),
            "total_royalties_earned": float(totals_row.total_royalties),
            "total_points": float(totals_row.total_points),
        },
    }


@router.get("/{point_id}")
async def get_point(
    point_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text("SELECT * FROM echo_points WHERE id = :id AND buyer_user_id = :user_id"),
        {"id": point_id, "user_id": current_user.user_id},
    )
    point = result.mappings().fetchone()
    if not point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point not found")
    return dict(point)


@router.get("/track/{track_id}/availability")
async def check_availability(
    track_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    result = await db.execute(
        text(
            """
            SELECT
              point_type,
              COALESCE(SUM(points_purchased), 0) as sold_points
            FROM echo_points
            WHERE track_id = :track_id AND status = 'active'
            GROUP BY point_type
            """
        ),
        {"track_id": track_id},
    )
    sold = {row.point_type: float(row.sold_points) for row in result.fetchall()}

    max_points = 10000.0
    return {
        "track_id": track_id,
        "master_available": max_points - sold.get("master", 0),
        "publishing_available": max_points - sold.get("publishing", 0),
        "max_points_per_type": max_points,
    }
