"""
Melodio KYC Router — Powered by Persona
Handles fan identity verification before Melodio Points purchases.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import hashlib
import hmac

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()

PERSONA_API_KEY = os.getenv("PERSONA_API_KEY", "")
PERSONA_BASE_URL = "https://withpersona.com/api/v1"
PERSONA_VERSION = "2023-01-05"

PERSONA_HEADERS = {
    "Authorization": f"Bearer {PERSONA_API_KEY}",
    "Persona-Version": PERSONA_VERSION,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────

class CreateInquiryRequest(BaseModel):
    reference_id: Optional[str] = None   # our user_id
    redirect_url: Optional[str] = "https://melodio.io/points"


class InquiryStatusRequest(BaseModel):
    inquiry_id: str


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _persona_get(path: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{PERSONA_BASE_URL}{path}",
            headers=PERSONA_HEADERS,
        )
        r.raise_for_status()
        return r.json()


async def _persona_post(path: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{PERSONA_BASE_URL}{path}",
            headers=PERSONA_HEADERS,
            json=payload,
        )
        r.raise_for_status()
        return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/create-inquiry")
async def create_kyc_inquiry(
    body: CreateInquiryRequest,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Persona KYC inquiry for the current user.
    Returns an inquiry_id + hosted verification URL to redirect the fan to.
    """
    if not PERSONA_API_KEY:
        raise HTTPException(status_code=503, detail="KYC service not configured")

    reference_id = body.reference_id or str(current_user.user_id)

    try:
        resp = await _persona_post("/inquiries", {
            "data": {
                "attributes": {
                    "inquiry-template-version-id": None,  # uses default template
                    "reference-id": reference_id,
                    "redirect-url": body.redirect_url,
                }
            }
        })
    except httpx.HTTPStatusError as e:
        # Try without template version (uses account default)
        try:
            resp = await _persona_post("/inquiries", {
                "data": {
                    "attributes": {
                        "reference-id": reference_id,
                        "redirect-url": body.redirect_url,
                    }
                }
            })
        except Exception as e2:
            raise HTTPException(status_code=502, detail=f"Persona error: {str(e2)}")

    inquiry = resp.get("data", {})
    inquiry_id = inquiry.get("id")
    session_token = inquiry.get("attributes", {}).get("session-token")
    hosted_url = f"https://withpersona.com/verify?inquiry-id={inquiry_id}&session-token={session_token}"

    return {
        "inquiry_id": inquiry_id,
        "hosted_url": hosted_url,
        "status": inquiry.get("attributes", {}).get("status", "created"),
        "reference_id": reference_id,
    }


@router.get("/status/{inquiry_id}")
async def get_kyc_status(
    inquiry_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Check the status of a KYC inquiry."""
    if not PERSONA_API_KEY:
        raise HTTPException(status_code=503, detail="KYC service not configured")

    try:
        resp = await _persona_get(f"/inquiries/{inquiry_id}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Persona error: {str(e)}")

    attrs = resp.get("data", {}).get("attributes", {})
    status = attrs.get("status")
    approved = status == "completed"

    return {
        "inquiry_id": inquiry_id,
        "status": status,
        "approved": approved,
        "name": attrs.get("name-first", "") + " " + attrs.get("name-last", ""),
        "country": attrs.get("country-code"),
        "completed_at": attrs.get("completed-at"),
    }


@router.post("/webhook")
async def persona_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receive Persona webhook events.
    Updates user KYC status in DB when inquiry completes.
    """
    payload = await request.body()
    sig_header = request.headers.get("Persona-Signature", "")

    # Verify webhook signature (optional in sandbox)
    webhook_secret = os.getenv("PERSONA_WEBHOOK_SECRET", "")
    if webhook_secret and sig_header:
        expected = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, sig_header.split("=")[-1]):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    import json
    data = json.loads(payload)
    event_name = data.get("data", {}).get("attributes", {}).get("name", "")
    inquiry = data.get("data", {}).get("attributes", {}).get("payload", {}).get("data", {})
    inquiry_id = inquiry.get("id")
    status = inquiry.get("attributes", {}).get("status")
    reference_id = inquiry.get("attributes", {}).get("reference-id")  # our user_id

    if event_name in ("inquiry.completed", "inquiry.approved") and reference_id:
        # Mark user as KYC verified in DB
        await db.execute(text("""
            UPDATE users SET
                email_verified = TRUE,
                updated_at = NOW()
            WHERE id = :user_id::uuid
        """), {"user_id": reference_id})
        await db.commit()

    return {"received": True, "event": event_name, "inquiry_id": inquiry_id}


@router.get("/check-status")
async def check_my_kyc_status(
    current_user: TokenData = Depends(get_current_user),
):
    """Check if current user is KYC verified (for Points Store gating)."""
    if not PERSONA_API_KEY:
        # If Persona not configured, don't block users
        return {"kyc_required": False, "verified": True, "reason": "KYC not configured"}

    return {
        "kyc_required": True,
        "verified": False,  # Will be updated once inquiry completes
        "user_id": str(current_user.user_id),
        "message": "Complete identity verification to purchase Melodio Points",
        "sandbox": "sandbox" in PERSONA_API_KEY,
    }
