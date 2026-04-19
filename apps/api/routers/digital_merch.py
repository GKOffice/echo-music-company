"""
Melodio Digital Merchandise API
Artist store: downloads, stems, sample packs, beat licenses, digital art, and more.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timedelta, timezone

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()

MELODIO_FEE_PCT = 15.0
DEFAULT_MAX_DOWNLOADS = 5
DOWNLOAD_EXPIRES_DAYS = 30


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


def _gen_license_key(product_type: str) -> str:
    prefix = product_type[:3].upper()
    suffix = uuid.uuid4().hex[:8].upper()
    return f"MLO-{prefix}-{suffix}"


# ── Schemas ───────────────────────────────────────────────────────────────────

class DigitalProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    product_type: str
    price: float
    currency: str = "USD"
    file_url: Optional[str] = None
    preview_url: Optional[str] = None
    cover_art_url: Optional[str] = None
    file_size_mb: Optional[float] = None
    file_format: Optional[str] = None
    license_type: str = "personal"
    download_limit: Optional[int] = None
    tags: Optional[list[str]] = None
    release_id: Optional[str] = None
    track_id: Optional[str] = None


class DigitalProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    product_type: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    file_url: Optional[str] = None
    preview_url: Optional[str] = None
    cover_art_url: Optional[str] = None
    file_size_mb: Optional[float] = None
    file_format: Optional[str] = None
    license_type: Optional[str] = None
    download_limit: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    tags: Optional[list[str]] = None
    release_id: Optional[str] = None
    track_id: Optional[str] = None

_DIGITAL_PRODUCT_UPDATE_ALLOWED = {
    "title", "description", "product_type", "price", "currency",
    "file_url", "preview_url", "cover_art_url", "file_size_mb",
    "file_format", "license_type", "download_limit", "is_active",
    "is_featured", "tags", "release_id", "track_id",
}


class PurchaseRequest(BaseModel):
    stripe_payment_intent_id: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
async def list_products(
    artist_id: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List all active digital products (public)."""
    conditions = ["dp.is_active = true"]
    params: dict = {"limit": limit, "offset": offset}

    if artist_id:
        conditions.append("dp.artist_id = CAST(:artist_id AS UUID)")
        params["artist_id"] = artist_id
    if product_type:
        conditions.append("dp.product_type = :product_type")
        params["product_type"] = product_type
    if featured is not None:
        conditions.append("dp.is_featured = :featured")
        params["featured"] = featured

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"""
            SELECT dp.*, a.name AS artist_name
            FROM digital_products dp
            JOIN artists a ON a.id = dp.artist_id
            WHERE {where}
            ORDER BY dp.is_featured DESC, dp.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    rows = result.mappings().all()
    return {"products": [_serialize(dict(r)) for r in rows], "total": len(rows)}


@router.get("/artist/{artist_id}")
async def artist_storefront(
    artist_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Artist storefront — all active products for an artist (public)."""
    result = await db.execute(
        text("""
            SELECT dp.*, a.name AS artist_name
            FROM digital_products dp
            JOIN artists a ON a.id = dp.artist_id
            WHERE dp.artist_id = CAST(:artist_id AS UUID) AND dp.is_active = true
            ORDER BY dp.is_featured DESC, dp.product_type, dp.price
        """),
        {"artist_id": artist_id},
    )
    rows = result.mappings().all()

    artist_result = await db.execute(
        text("SELECT id, name, genre, bio FROM artists WHERE id = CAST(:id AS UUID)"),
        {"id": artist_id},
    )
    artist = artist_result.mappings().first()

    return {
        "artist": _serialize(dict(artist)) if artist else None,
        "products": [_serialize(dict(r)) for r in rows],
        "total": len(rows),
    }


@router.get("/purchases/my")
async def my_purchases(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Buyer purchase history (authenticated)."""
    result = await db.execute(
        text("""
            SELECT dp2.id AS purchase_id, dp2.purchased_at, dp2.amount_paid,
                   dp2.status, dp2.download_count, dp2.max_downloads,
                   dp2.license_key, dp2.expires_at, dp2.download_token,
                   p.title, p.product_type, p.cover_art_url,
                   a.name AS artist_name
            FROM digital_purchases dp2
            JOIN digital_products p ON p.id = dp2.product_id
            JOIN artists a ON a.id = dp2.artist_id
            WHERE dp2.buyer_user_id = CAST(:user_id AS UUID)
            ORDER BY dp2.purchased_at DESC
        """),
        {"user_id": current_user.user_id},
    )
    rows = result.mappings().all()
    return {"purchases": [_serialize(dict(r)) for r in rows]}


@router.get("/download/{token}")
async def secure_download(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Secure token-based download — no auth required."""
    result = await db.execute(
        text("""
            SELECT dp2.*, p.file_url, p.title, p.file_format
            FROM digital_purchases dp2
            JOIN digital_products p ON p.id = dp2.product_id
            WHERE dp2.download_token = CAST(:token AS UUID)
        """),
        {"token": token},
    )
    purchase = result.mappings().first()

    if not purchase:
        raise HTTPException(status_code=404, detail="Download token not found")

    purchase = dict(purchase)

    if purchase.get("status") != "completed":
        raise HTTPException(status_code=403, detail="Purchase not completed")

    if purchase.get("expires_at") and purchase["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Download link has expired")

    if purchase.get("download_count", 0) >= purchase.get("max_downloads", DEFAULT_MAX_DOWNLOADS):
        raise HTTPException(status_code=410, detail="Maximum downloads reached")

    await db.execute(
        text("""
            UPDATE digital_purchases
            SET download_count = download_count + 1, last_downloaded_at = NOW()
            WHERE download_token = CAST(:token AS UUID)
        """),
        {"token": token},
    )
    await db.commit()

    return {
        "download_url": purchase.get("file_url"),
        "title": purchase.get("title"),
        "file_format": purchase.get("file_format"),
        "expires_in_seconds": 3600,
        "downloads_remaining": purchase.get("max_downloads", DEFAULT_MAX_DOWNLOADS) - purchase.get("download_count", 0) - 1,
    }


@router.get("/{product_id}/stats")
async def product_stats(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Product sales stats (artist only)."""
    result = await db.execute(
        text("SELECT * FROM digital_products WHERE id = CAST(:id AS UUID)"),
        {"id": product_id},
    )
    product = result.mappings().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product = dict(product)

    # Verify artist ownership
    artist_result = await db.execute(
        text("SELECT id FROM artists WHERE id = CAST(:aid AS UUID) AND user_id = CAST(:uid AS UUID)"),
        {"aid": str(product["artist_id"]), "uid": current_user.user_id},
    )
    if not artist_result.mappings().first():
        raise HTTPException(status_code=403, detail="Not authorized")

    sales_result = await db.execute(
        text("""
            SELECT
                COUNT(*) AS total_purchases,
                COALESCE(SUM(amount_paid), 0) AS gross_revenue,
                COALESCE(SUM(artist_payout), 0) AS net_revenue,
                COALESCE(SUM(melodio_fee), 0) AS total_fees,
                COALESCE(AVG(amount_paid), 0) AS avg_order_value
            FROM digital_purchases
            WHERE product_id = CAST(:pid AS UUID) AND status = 'completed'
        """),
        {"pid": product_id},
    )
    stats = dict(sales_result.mappings().first() or {})

    return {
        "product": _serialize(product),
        "stats": {k: float(v) if v is not None else 0 for k, v in stats.items()},
    }


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get product detail (public)."""
    result = await db.execute(
        text("""
            SELECT dp.*, a.name AS artist_name
            FROM digital_products dp
            JOIN artists a ON a.id = dp.artist_id
            WHERE dp.id = CAST(:id AS UUID) AND dp.is_active = true
        """),
        {"id": product_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return _serialize(dict(row))


@router.post("")
async def create_product(
    body: DigitalProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Create digital product (artist auth)."""
    # Find artist belonging to current user
    artist_result = await db.execute(
        text("SELECT id FROM artists WHERE user_id = CAST(:uid AS UUID) LIMIT 1"),
        {"uid": current_user.user_id},
    )
    artist = artist_result.mappings().first()
    if not artist:
        raise HTTPException(status_code=403, detail="No artist profile found for user")

    artist_id = str(artist["id"])
    product_id = str(uuid.uuid4())

    await db.execute(
        text("""
            INSERT INTO digital_products
              (id, artist_id, title, description, product_type, price, currency,
               file_url, preview_url, cover_art_url, file_size_mb, file_format,
               license_type, download_limit, tags, release_id, track_id)
            VALUES
              (CAST(:id AS UUID), CAST(:artist_id AS UUID), :title, :description, :product_type, :price, :currency,
               :file_url, :preview_url, :cover_art_url, :file_size_mb, :file_format,
               :license_type, :download_limit, :tags, :release_id, :track_id)
        """),
        {
            "id": product_id,
            "artist_id": artist_id,
            "title": body.title,
            "description": body.description,
            "product_type": body.product_type,
            "price": body.price,
            "currency": body.currency,
            "file_url": body.file_url,
            "preview_url": body.preview_url,
            "cover_art_url": body.cover_art_url,
            "file_size_mb": body.file_size_mb,
            "file_format": body.file_format,
            "license_type": body.license_type,
            "download_limit": body.download_limit,
            "tags": body.tags,
            "release_id": body.release_id,
            "track_id": body.track_id,
        },
    )
    await db.commit()
    return {"product_id": product_id, "artist_id": artist_id, "status": "created"}


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    body: DigitalProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Update product (artist auth)."""
    result = await db.execute(
        text("""
            SELECT dp.id, dp.artist_id FROM digital_products dp
            JOIN artists a ON a.id = dp.artist_id
            WHERE dp.id = CAST(:pid AS UUID) AND a.user_id = CAST(:uid AS UUID)
        """),
        {"pid": product_id, "uid": current_user.user_id},
    )
    if not result.mappings().first():
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    # BUG FIX: whitelist column names before building dynamic SET clause
    updates = {k: v for k, v in updates.items() if k in _DIGITAL_PRODUCT_UPDATE_ALLOWED}
    if not updates:
        return {"status": "no_changes"}

    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
    updates["pid"] = product_id
    await db.execute(
        text(f"UPDATE digital_products SET {set_clauses} WHERE id = CAST(:pid AS UUID)"),
        updates,
    )
    await db.commit()
    return {"product_id": product_id, "status": "updated", "fields": list(updates.keys())}


@router.delete("/{product_id}")
async def deactivate_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Deactivate product (artist auth)."""
    result = await db.execute(
        text("""
            SELECT dp.id FROM digital_products dp
            JOIN artists a ON a.id = dp.artist_id
            WHERE dp.id = CAST(:pid AS UUID) AND a.user_id = CAST(:uid AS UUID)
        """),
        {"pid": product_id, "uid": current_user.user_id},
    )
    if not result.mappings().first():
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    await db.execute(
        text("UPDATE digital_products SET is_active = false WHERE id = CAST(:pid AS UUID)"),
        {"pid": product_id},
    )
    await db.commit()
    return {"product_id": product_id, "status": "deactivated"}


@router.post("/{product_id}/purchase")
async def purchase_product(
    product_id: str,
    body: PurchaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Purchase a digital product (authenticated user)."""
    result = await db.execute(
        text("SELECT * FROM digital_products WHERE id = CAST(:id AS UUID) AND is_active = true"),
        {"id": product_id},
    )
    product = result.mappings().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product = dict(product)

    payment_intent = body.stripe_payment_intent_id or f"mock_{uuid.uuid4().hex}"
    if not payment_intent.startswith("mock_"):
        import stripe
        import os
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        try:
            pi = stripe.PaymentIntent.retrieve(payment_intent)
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=402, detail=str(e.user_message))
        if pi.status != "succeeded":
            raise HTTPException(status_code=402, detail="Payment not confirmed")

    amount_paid = float(product["price"])
    melodio_fee = round(amount_paid * MELODIO_FEE_PCT / 100, 2)
    artist_payout = round(amount_paid - melodio_fee, 2)
    download_token = str(uuid.uuid4())
    license_key = _gen_license_key(product["product_type"])
    expires_at = datetime.now(timezone.utc) + timedelta(days=DOWNLOAD_EXPIRES_DAYS)
    purchase_id = str(uuid.uuid4())

    await db.execute(
        text("""
            INSERT INTO digital_purchases
              (id, product_id, buyer_user_id, artist_id, amount_paid, currency,
               melodio_fee, artist_payout, stripe_payment_intent_id,
               download_token, max_downloads, license_key, status, expires_at)
            VALUES
              (CAST(:id AS UUID), CAST(:product_id AS UUID), CAST(:buyer_user_id AS UUID), CAST(:artist_id AS UUID),
               :amount_paid, :currency, :melodio_fee, :artist_payout,
               :stripe_payment_intent_id, CAST(:download_token AS UUID), :max_downloads,
               :license_key, 'completed', :expires_at)
        """),
        {
            "id": purchase_id,
            "product_id": product_id,
            "buyer_user_id": current_user.user_id,
            "artist_id": str(product["artist_id"]),
            "amount_paid": amount_paid,
            "currency": product.get("currency", "USD"),
            "melodio_fee": melodio_fee,
            "artist_payout": artist_payout,
            "stripe_payment_intent_id": payment_intent,
            "download_token": download_token,
            "max_downloads": DEFAULT_MAX_DOWNLOADS,
            "license_key": license_key,
            "expires_at": expires_at,
        },
    )

    # Update product counters
    await db.execute(
        text("""
            UPDATE digital_products
            SET units_sold = units_sold + 1, total_revenue = total_revenue + :amount
            WHERE id = CAST(:pid AS UUID)
        """),
        {"amount": amount_paid, "pid": product_id},
    )
    await db.commit()

    return {
        "purchase_id": purchase_id,
        "product_id": product_id,
        "amount_paid": amount_paid,
        "melodio_fee": melodio_fee,
        "artist_payout": artist_payout,
        "download_token": download_token,
        "download_url": f"/api/v1/digital-merch/download/{download_token}",
        "license_key": license_key,
        "expires_at": expires_at.isoformat(),
        "max_downloads": DEFAULT_MAX_DOWNLOADS,
        "status": "completed",
    }
