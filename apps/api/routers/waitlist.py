import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.email import waitlist_confirmation

router = APIRouter()

ENSURE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS waitlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(100) DEFAULT 'landing_page',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    notified_at TIMESTAMPTZ
);
"""


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str = "landing_page"


class WaitlistResponse(BaseModel):
    success: bool
    message: str
    already_exists: bool = False


@router.on_event("startup")
async def create_waitlist_table():
    from database import engine
    async with engine.begin() as conn:
        await conn.execute(text(ENSURE_TABLE_SQL))


@router.post("", response_model=WaitlistResponse)
async def join_waitlist(body: WaitlistRequest, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()

    # Check if already exists
    result = await db.execute(
        text("SELECT id FROM waitlist WHERE email = :email"),
        {"email": email},
    )
    if result.fetchone():
        return WaitlistResponse(
            success=True,
            message="You are already on the list.",
            already_exists=True,
        )

    await db.execute(
        text("INSERT INTO waitlist (email, source) VALUES (:email, :source)"),
        {"email": email, "source": body.source},
    )

    asyncio.create_task(waitlist_confirmation(email))

    return WaitlistResponse(
        success=True,
        message="You are on the list.",
        already_exists=False,
    )
