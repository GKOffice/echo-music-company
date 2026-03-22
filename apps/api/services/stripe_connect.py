"""
Stripe Connect service for artist payouts.
Creates Express accounts, handles onboarding, and processes payouts.
"""
import stripe
import os
import logging

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
logger = logging.getLogger(__name__)


async def create_connect_account(email: str, country: str = "US") -> dict:
    """Create a Stripe Express Connect account for an artist."""
    account = stripe.Account.create(
        type="express",
        country=country,
        email=email,
        capabilities={
            "transfers": {"requested": True},
        },
    )
    return {"account_id": account.id, "email": email}


async def create_onboarding_link(
    account_id: str, refresh_url: str, return_url: str
) -> str:
    """Generate a Stripe Connect onboarding link for the artist."""
    link = stripe.AccountLink.create(
        account=account_id,
        refresh_url=refresh_url,
        return_url=return_url,
        type="account_onboarding",
    )
    return link.url


async def get_account_status(account_id: str) -> dict:
    """Check whether a Connect account is fully onboarded."""
    account = stripe.Account.retrieve(account_id)
    return {
        "account_id": account.id,
        "charges_enabled": account.charges_enabled,
        "payouts_enabled": account.payouts_enabled,
        "details_submitted": account.details_submitted,
        "requirements": account.requirements,
    }


async def create_payout(
    account_id: str, amount_cents: int, currency: str = "usd"
) -> dict:
    """Transfer funds to an artist's Connect account."""
    transfer = stripe.Transfer.create(
        amount=amount_cents,
        currency=currency,
        destination=account_id,
        description="Melodio artist payout",
    )
    return {
        "transfer_id": transfer.id,
        "amount": transfer.amount,
        "currency": transfer.currency,
        "destination": transfer.destination,
        "status": "pending",
    }


async def get_payout_history(account_id: str) -> list[dict]:
    """List recent transfers sent to an artist's Connect account."""
    transfers = stripe.Transfer.list(destination=account_id, limit=50)
    return [
        {
            "transfer_id": t.id,
            "amount": t.amount,
            "currency": t.currency,
            "created": t.created,
            "reversed": t.reversed,
        }
        for t in transfers.data
    ]
