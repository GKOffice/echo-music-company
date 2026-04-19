"""
Melodio WhatsApp Webhook Router
Handles Meta webhook verification and incoming message events.
"""
import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, HTTPException, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Meta webhook verification handshake."""
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("[WhatsApp] Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")

    logger.warning(f"[WhatsApp] Webhook verification failed — token mismatch")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request):
    """Receive incoming WhatsApp messages and status updates."""
    body = await request.body()

    # BUG FIX: Require APP_SECRET in production. Reject all unauthenticated webhooks.
    if not APP_SECRET:
        if ENVIRONMENT == "production":
            logger.error("[WhatsApp] WHATSAPP_APP_SECRET not set — rejecting webhook in production")
            raise HTTPException(status_code=503, detail="Webhook not configured")
        else:
            logger.warning("[WhatsApp] APP_SECRET not set — skipping signature check (dev mode only)")
    else:
        sig_header = request.headers.get("X-Hub-Signature-256", "")
        # BUG FIX: use hmac.new() correctly (stdlib function, always available)
        expected = "sha256=" + hmac.new(
            APP_SECRET.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected):
            logger.warning("[WhatsApp] Webhook signature mismatch")
            raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        data = json.loads(body)
        entry = data.get("entry", [])

        for e in entry:
            for change in e.get("changes", []):
                value = change.get("value", {})

                # Incoming messages
                for msg in value.get("messages", []):
                    from_number = msg.get("from")
                    msg_type = msg.get("type")
                    text = msg.get("text", {}).get("body", "") if msg_type == "text" else f"[{msg_type}]"
                    logger.info(f"[WhatsApp] Message from {from_number}: {text}")
                    # TODO: route to Comms Agent via message bus

                # Status updates
                for status in value.get("statuses", []):
                    logger.info(f"[WhatsApp] Status update: {status.get('status')} for {status.get('recipient_id')}")

    except Exception as e:
        logger.error(f"[WhatsApp] Webhook processing error: {e}")

    # Always return 200 to Meta
    return {"status": "ok"}
