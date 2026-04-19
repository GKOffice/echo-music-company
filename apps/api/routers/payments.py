"""
Melodio Payments Router
Handles Stripe payment intents for:
- Melodio Points purchases
- Digital merchandise purchases
- Webhook handling
"""
import stripe
import os
import uuid
import json
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional

from database import get_db
from routers.auth import get_current_user, TokenData
from services.stripe_connect import (
    create_connect_account,
    create_onboarding_link,
    get_account_status,
    create_payout,
    get_payout_history,
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

logger = logging.getLogger(__name__)
router = APIRouter()

MELODIO_FEE_PCT = 15.0
DEFAULT_MAX_DOWNLOADS = 5
DOWNLOAD_EXPIRES_DAYS = 30


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateIntentRequest(BaseModel):
    amount_cents: int
    currency: str = "usd"
    product_type: str  # "points" | "digital_merch"
    product_id: str
    metadata: dict = {}


class ConfirmPaymentRequest(BaseModel):
    payment_intent_id: str
    product_type: str
    product_id: str


class RefundRequest(BaseModel):
    payment_intent_id: str
    reason: str


class ConnectOnboardRequest(BaseModel):
    refresh_url: str = "https://melodio.io/connect/refresh"
    return_url: str = "https://melodio.io/connect/complete"


class ConnectPayoutRequest(BaseModel):
    artist_id: str
    amount_cents: int
    currency: str = "usd"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _gen_license_key(product_type: str) -> str:
    prefix = product_type[:3].upper()
    suffix = uuid.uuid4().hex[:8].upper()
    return f"MLO-{prefix}-{suffix}"


async def _credit_points(user_id: str, amount_cents: int, pi_id: str, db: AsyncSession) -> int:
    """Credit echo_points for a user. 1 cent = 1 point. Idempotent."""
    existing = await db.execute(
        text("SELECT id FROM echo_points WHERE reference_id = :ref_id LIMIT 1"),
        {"ref_id": pi_id},
    )
    if existing.mappings().first():
        return amount_cents  # already credited

    await db.execute(
        text("""
            INSERT INTO echo_points (id, user_id, points, transaction_type, description, reference_id)
            VALUES (CAST(:id AS UUID), CAST(:user_id AS UUID), :points, 'purchase', :description, :ref_id)
        """),
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "points": amount_cents,
            "description": "Points purchase via Stripe",
            "ref_id": pi_id,
        },
    )
    await db.commit()
    return amount_cents


async def _create_digital_purchase(
    product_id: str, buyer_user_id: str, pi_id: str, db: AsyncSession
) -> dict:
    """Create digital_purchase record. Idempotent — returns existing token if already processed."""
    existing = await db.execute(
        text("SELECT download_token, license_key FROM digital_purchases WHERE stripe_payment_intent_id = :pi_id LIMIT 1"),
        {"pi_id": pi_id},
    )
    existing_row = existing.mappings().first()
    if existing_row:
        return {
            "download_token": str(existing_row["download_token"]),
            "license_key": existing_row["license_key"],
        }

    result = await db.execute(
        text("SELECT * FROM digital_products WHERE id = CAST(:id AS UUID) AND is_active = true"),
        {"id": product_id},
    )
    product = result.mappings().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product = dict(product)

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
            "buyer_user_id": buyer_user_id,
            "artist_id": str(product["artist_id"]),
            "amount_paid": amount_paid,
            "currency": product.get("currency", "USD"),
            "melodio_fee": melodio_fee,
            "artist_payout": artist_payout,
            "stripe_payment_intent_id": pi_id,
            "download_token": download_token,
            "max_downloads": DEFAULT_MAX_DOWNLOADS,
            "license_key": license_key,
            "expires_at": expires_at,
        },
    )
    await db.execute(
        text("""
            UPDATE digital_products
            SET units_sold = units_sold + 1, total_revenue = total_revenue + :amount
            WHERE id = CAST(:pid AS UUID)
        """),
        {"amount": amount_paid, "pid": product_id},
    )
    await db.commit()
    return {"download_token": download_token, "license_key": license_key}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/create-intent")
async def create_payment_intent(
    body: CreateIntentRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """Create a Stripe PaymentIntent."""
    if body.product_type not in ("points", "digital_merch"):
        raise HTTPException(status_code=400, detail="Invalid product_type")
    if body.amount_cents < 50:
        raise HTTPException(status_code=400, detail="Amount must be at least 50 cents")

    try:
        pi = stripe.PaymentIntent.create(
            amount=body.amount_cents,
            currency=body.currency.lower(),
            metadata={
                "product_type": body.product_type,
                "product_id": body.product_id,
                "user_id": current_user.user_id,
                **body.metadata,
            },
            automatic_payment_methods={"enabled": True},
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=402, detail=str(e.user_message))

    return {
        "client_secret": pi.client_secret,
        "payment_intent_id": pi.id,
        "amount": pi.amount,
        "currency": pi.currency,
    }


@router.post("/confirm")
async def confirm_payment(
    body: ConfirmPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Confirm payment after Stripe.js confirms on frontend."""
    try:
        pi = stripe.PaymentIntent.retrieve(body.payment_intent_id)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=402, detail=str(e.user_message))

    if pi.status != "succeeded":
        raise HTTPException(status_code=402, detail=f"Payment not confirmed (status: {pi.status})")

    result: dict = {
        "success": True,
        "product_type": body.product_type,
        "product_id": body.product_id,
    }

    if body.product_type == "points":
        points = await _credit_points(current_user.user_id, pi.amount, pi.id, db)
        result["points_credited"] = points
    elif body.product_type == "digital_merch":
        purchase = await _create_digital_purchase(body.product_id, current_user.user_id, pi.id, db)
        result["download_token"] = purchase["download_token"]
        result["license_key"] = purchase["license_key"]
    else:
        raise HTTPException(status_code=400, detail="Unknown product_type")

    return result


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    """Stripe webhook endpoint — no auth required."""
    payload = await request.body()

    if WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, stripe_signature, WEBHOOK_SECRET)
            event_type = event.type
            event_obj = event.data.object
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        # Extract fields from Stripe object
        def _get(obj, key):
            return getattr(obj, key, None)
    else:
        # Dev mode: skip signature validation
        event_dict = json.loads(payload)
        event_type = event_dict.get("type", "")
        event_obj = event_dict.get("data", {}).get("object", {})

        def _get(obj, key):
            return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)

    if event_type == "payment_intent.succeeded":
        pi_id = _get(event_obj, "id")
        metadata = _get(event_obj, "metadata") or {}
        amount = _get(event_obj, "amount")
        product_type = metadata.get("product_type") if isinstance(metadata, dict) else getattr(metadata, "product_type", None)
        product_id = metadata.get("product_id") if isinstance(metadata, dict) else getattr(metadata, "product_id", None)
        user_id = metadata.get("user_id") if isinstance(metadata, dict) else getattr(metadata, "user_id", None)

        if product_type and product_id and user_id:
            try:
                if product_type == "points":
                    await _credit_points(user_id, amount, pi_id, db)
                elif product_type == "digital_merch":
                    await _create_digital_purchase(product_id, user_id, pi_id, db)
            except Exception as exc:
                logger.error("Webhook processing error for %s: %s", pi_id, exc)

    elif event_type == "payment_intent.payment_failed":
        pi_id = _get(event_obj, "id")
        logger.warning("Payment failed: %s", pi_id)
        try:
            await request.app.state.redis.xadd("agent:messages", {
                "type": "payment_failed",
                "payment_intent_id": pi_id or "",
                "ts": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            pass

    elif event_type == "charge.refunded":
        pi_id = _get(event_obj, "payment_intent")
        if pi_id:
            await db.execute(
                text("UPDATE digital_purchases SET status = 'refunded' WHERE stripe_payment_intent_id = :pi_id"),
                {"pi_id": pi_id},
            )
            await db.commit()

    return {"received": True}


@router.get("/history")
async def payment_history(
    current_user: TokenData = Depends(get_current_user),
):
    """Last 20 payments for current user from Stripe."""
    try:
        results = stripe.PaymentIntent.search(
            query=f"metadata['user_id']:'{current_user.user_id}' AND status:'succeeded'",
            limit=20,
        )
        payments = [
            {
                "id": pi.id,
                "amount": pi.amount,
                "currency": pi.currency,
                "status": pi.status,
                "created": pi.created,
                "product_type": pi.metadata.get("product_type"),
                "product_id": pi.metadata.get("product_id"),
            }
            for pi in results.data
        ]
        return {"payments": payments}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=402, detail=str(e.user_message))


@router.post("/refund")
async def refund_payment(
    body: RefundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Refund a payment (admin only)."""
    user_result = await db.execute(
        text("SELECT role FROM users WHERE id = CAST(:uid AS UUID)"),
        {"uid": current_user.user_id},
    )
    user = user_result.mappings().first()
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    valid_reasons = ("duplicate", "fraudulent", "requested_by_customer")
    refund_reason = body.reason if body.reason in valid_reasons else "requested_by_customer"

    try:
        refund = stripe.Refund.create(
            payment_intent=body.payment_intent_id,
            reason=refund_reason,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=402, detail=str(e.user_message))

    await db.execute(
        text("UPDATE digital_purchases SET status = 'refunded' WHERE stripe_payment_intent_id = :pi_id"),
        {"pi_id": body.payment_intent_id},
    )
    await db.commit()

    return {
        "refund_id": refund.id,
        "payment_intent_id": body.payment_intent_id,
        "amount_refunded": refund.amount,
        "status": refund.status,
    }


# ── Stripe Connect ────────────────────────────────────────────────────────────

@router.post("/connect/onboard")
async def connect_onboard(
    body: ConnectOnboardRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Create a Stripe Connect Express account for the current artist and return an onboarding link."""
    artist_result = await db.execute(
        text("SELECT id, name, stripe_connect_id FROM artists WHERE user_id = CAST(:uid AS UUID) LIMIT 1"),
        {"uid": current_user.user_id},
    )
    artist = artist_result.mappings().first()
    if not artist:
        raise HTTPException(status_code=404, detail="No artist profile found for this user")

    account_id = artist.get("stripe_connect_id")

    if not account_id:
        # Fetch user email for the Connect account
        user_result = await db.execute(
            text("SELECT email FROM users WHERE id = CAST(:uid AS UUID)"),
            {"uid": current_user.user_id},
        )
        user = user_result.mappings().first()
        account = await create_connect_account(user["email"])
        account_id = account["account_id"]

        await db.execute(
            text("UPDATE artists SET stripe_connect_id = :acct, stripe_connect_status = 'pending' WHERE id = CAST(:aid AS UUID)"),
            {"acct": account_id, "aid": str(artist["id"])},
        )
        await db.commit()

    onboarding_url = await create_onboarding_link(account_id, body.refresh_url, body.return_url)
    return {"onboarding_url": onboarding_url, "account_id": account_id}


@router.get("/connect/status")
async def connect_status(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Check the current artist's Stripe Connect account status."""
    artist_result = await db.execute(
        text("SELECT id, stripe_connect_id, stripe_connect_status FROM artists WHERE user_id = CAST(:uid AS UUID) LIMIT 1"),
        {"uid": current_user.user_id},
    )
    artist = artist_result.mappings().first()
    if not artist:
        raise HTTPException(status_code=404, detail="No artist profile found")

    account_id = artist.get("stripe_connect_id")
    if not account_id:
        return {"status": "not_started", "account_id": None}

    status = await get_account_status(account_id)

    # Update local status based on Stripe data
    new_status = "active" if status["payouts_enabled"] else "pending"
    if new_status != artist.get("stripe_connect_status"):
        await db.execute(
            text("UPDATE artists SET stripe_connect_status = :status WHERE id = CAST(:aid AS UUID)"),
            {"status": new_status, "aid": str(artist["id"])},
        )
        await db.commit()

    return {
        "status": new_status,
        "account_id": account_id,
        "charges_enabled": status["charges_enabled"],
        "payouts_enabled": status["payouts_enabled"],
        "details_submitted": status["details_submitted"],
    }


@router.post("/connect/payout")
async def connect_payout(
    body: ConnectPayoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Trigger a payout to an artist's Connect account (admin only)."""
    user_result = await db.execute(
        text("SELECT role FROM users WHERE id = CAST(:uid AS UUID)"),
        {"uid": current_user.user_id},
    )
    user = user_result.mappings().first()
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    artist_result = await db.execute(
        text("SELECT id, name, stripe_connect_id, stripe_connect_status FROM artists WHERE id = CAST(:aid AS UUID)"),
        {"aid": body.artist_id},
    )
    artist = artist_result.mappings().first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    if not artist.get("stripe_connect_id"):
        raise HTTPException(status_code=400, detail="Artist has no Connect account")
    if artist.get("stripe_connect_status") != "active":
        raise HTTPException(status_code=400, detail="Artist Connect account is not fully onboarded")
    if body.amount_cents < 100:
        raise HTTPException(status_code=400, detail="Minimum payout is $1.00")

    result = await create_payout(artist["stripe_connect_id"], body.amount_cents, body.currency)

    # Log to audit
    await db.execute(
        text("""
            INSERT INTO audit_log (id, action, entity_type, entity_id, performed_by, details)
            VALUES (CAST(:id AS UUID), 'payout_created', 'artist', CAST(:artist_id AS UUID), CAST(:admin_id AS UUID), :details)
        """),
        {
            "id": str(uuid.uuid4()),
            "artist_id": body.artist_id,
            "admin_id": current_user.user_id,
            "details": json.dumps({"transfer_id": result["transfer_id"], "amount_cents": body.amount_cents}),
        },
    )
    await db.commit()

    return result
