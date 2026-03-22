from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def generate_isrc(db: AsyncSession) -> str:
    """Generate a unique ISRC code: US-MEL-26-NNNNN using a DB sequence."""
    result = await db.execute(text("SELECT nextval('isrc_seq')"))
    seq = result.scalar()
    return f"US-MEL-26-{seq:05d}"
