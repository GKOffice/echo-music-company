from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional

from database import get_db
from routers.auth import get_current_user, TokenData
from services.weekly_digest import generate_weekly_digest, send_weekly_digest

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth: admin/super_admin only
# ---------------------------------------------------------------------------

async def require_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role not in ("admin", "super_admin", "owner"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class RejectBody(BaseModel):
    reason: Optional[str] = "Does not meet quality standards"


class DigestSendRequest(BaseModel):
    to_email: EmailStr = "ceo@melodio.io"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/stats")
async def admin_stats(
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    queries = {
        "total_artists": "SELECT COALESCE(COUNT(*), 0) FROM artists",
        "total_releases": "SELECT COALESCE(COUNT(*), 0) FROM releases",
        "total_users": "SELECT COALESCE(COUNT(*), 0) FROM users",
        "pending_submissions": "SELECT COALESCE(COUNT(*), 0) FROM releases WHERE status = 'pending_review'",
    }

    stats = {}
    for key, q in queries.items():
        result = await db.execute(text(q))
        stats[key] = result.scalar()

    # Waitlist count — table may not exist
    try:
        result = await db.execute(text("SELECT COALESCE(COUNT(*), 0) FROM waitlist"))
        stats["waitlist_count"] = result.scalar()
    except Exception:
        stats["waitlist_count"] = 0

    return stats


@router.get("/recent-signups")
async def recent_signups(
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT id, email, role, status, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 20
        """)
    )
    users = []
    for row in result.mappings().fetchall():
        users.append({
            "id": str(row["id"]),
            "email": row["email"],
            "role": row["role"],
            "status": row["status"],
            "created_at": str(row["created_at"]) if row["created_at"] else None,
        })
    return {"signups": users}


@router.get("/pending")
async def pending_releases(
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT r.id, r.title, r.type, r.status, r.created_at,
                   COALESCE(a.name, a.stage_name, 'Unknown') as artist_name,
                   a.id as artist_id
            FROM releases r
            LEFT JOIN artists a ON r.artist_id = a.id
            WHERE r.status = 'pending_review'
            ORDER BY r.created_at ASC
        """)
    )
    releases = []
    for row in result.mappings().fetchall():
        releases.append({
            "id": str(row["id"]),
            "title": row["title"],
            "type": row["type"],
            "status": row["status"],
            "artist_name": row["artist_name"],
            "artist_id": str(row["artist_id"]) if row["artist_id"] else None,
            "created_at": str(row["created_at"]) if row["created_at"] else None,
        })
    return {"pending": releases}


@router.post("/approve/{release_id}")
async def approve_release(
    release_id: str,
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT id, status FROM releases WHERE id = :id"),
        {"id": release_id},
    )
    release = result.fetchone()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    await db.execute(
        text("UPDATE releases SET status = 'approved', distribution_status = 'processing', updated_at = NOW() WHERE id = :id"),
        {"id": release_id},
    )
    await db.commit()

    return {"status": "ok", "message": "Release approved", "release_id": release_id}


@router.post("/reject/{release_id}")
async def reject_release(
    release_id: str,
    body: RejectBody,
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT id, status FROM releases WHERE id = :id"),
        {"id": release_id},
    )
    release = result.fetchone()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    await db.execute(
        text("UPDATE releases SET status = 'rejected', updated_at = NOW() WHERE id = :id"),
        {"id": release_id},
    )
    await db.commit()

    return {"status": "ok", "message": "Release rejected", "reason": body.reason}


@router.get("/waitlist")
async def get_waitlist(
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            text("SELECT * FROM waitlist ORDER BY created_at DESC")
        )
        entries = []
        for row in result.mappings().fetchall():
            entry = dict(row)
            for k, v in entry.items():
                if hasattr(v, 'isoformat'):
                    entry[k] = str(v)
                elif hasattr(v, 'hex'):
                    entry[k] = str(v)
            entries.append(entry)
        return {"waitlist": entries, "total": len(entries)}
    except Exception:
        return {"waitlist": [], "total": 0}


# ---------------------------------------------------------------------------
# Weekly Digest
# ---------------------------------------------------------------------------

@router.get("/weekly-digest")
async def get_weekly_digest(
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate and return the weekly CEO digest (admin only)."""
    digest = await generate_weekly_digest(db)
    return digest


@router.post("/run-migration")
async def run_pending_migrations(
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Run pending DB migrations (admin only — one-time use)."""
    migrations_run = []
    errors = []

    # Migration: agent_memory table
    try:
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_memory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id VARCHAR(50) NOT NULL,
                task_type VARCHAR(100) NOT NULL,
                error_type VARCHAR(50),
                input_summary TEXT,
                bad_output_summary TEXT,
                correction TEXT,
                confidence_score FLOAT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                is_success BOOLEAN DEFAULT FALSE
            )
        """))
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agent_memory_lookup
                ON agent_memory(agent_id, task_type, created_at DESC)
        """))
        await db.execute(text("""
            INSERT INTO agent_memory (agent_id, task_type, error_type, input_summary, bad_output_summary, correction, confidence_score, is_success)
            SELECT 'ar', 'review_artist', 'HALLUCINATION',
                '{\"artist_name\": \"Dorin Hirvi\"}',
                '{\"name\": \"Dorin Hirvi\", \"spotify_id\": \"3abc123fake\"}',
                'Dorin Hirvi does not exist. Return found=false for unknown artists with no verified external ID.',
                0.0, FALSE
            WHERE NOT EXISTS (
                SELECT 1 FROM agent_memory WHERE agent_id = 'ar' AND input_summary LIKE '%Dorin Hirvi%'
            )
        """))
        await db.commit()
        migrations_run.append("agent_memory table + hallucination seed")
    except Exception as e:
        errors.append(f"agent_memory: {str(e)}")

    return {
        "status": "complete" if not errors else "partial",
        "migrations_run": migrations_run,
        "errors": errors,
    }


@router.post("/weekly-digest/send")
async def post_send_weekly_digest(
    body: DigestSendRequest = DigestSendRequest(),
    current_user: TokenData = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate and email the weekly CEO digest (admin only)."""
    result = await send_weekly_digest(body.to_email, db)
    return {
        "status": "sent" if result.get("email_sent") else "failed",
        "sent_to": result.get("sent_to"),
        "period": result.get("period"),
    }
