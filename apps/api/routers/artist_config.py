"""
Artist Agent Config Router
Lets artists view and update their marketing + creative agent preferences.
Set via WhatsApp commands (/set, /config, /reset) or directly via this API.
"""
import uuid
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from routers.auth import get_current_user, TokenData

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Column allowlists (prevent dynamic field injection) ──────────────────────
_MARKETING_ALLOWED = {
    "preferred_channels", "excluded_channels", "budget_style",
    "target_audience", "campaign_goals", "playlist_targets",
    "avoid_content", "marketing_notes",
}
_CREATIVE_ALLOWED = {
    "brand_tone", "color_palette", "visual_style", "artist_persona",
    "content_do", "content_dont", "sample_references", "creative_notes",
}
_ALL_ALLOWED = _MARKETING_ALLOWED | _CREATIVE_ALLOWED


# ── Schemas ───────────────────────────────────────────────────────────────────

class MarketingConfig(BaseModel):
    preferred_channels: Optional[List[str]] = None    # ["tiktok", "meta"]
    excluded_channels: Optional[List[str]] = None     # ["google"]
    budget_style: Optional[str] = None                # "aggressive" | "balanced" | "conservative"
    target_audience: Optional[str] = None
    campaign_goals: Optional[str] = None
    playlist_targets: Optional[List[str]] = None
    avoid_content: Optional[str] = None
    marketing_notes: Optional[str] = None


class CreativeConfig(BaseModel):
    brand_tone: Optional[str] = None
    color_palette: Optional[dict] = None              # {"primary": "#000", "accent": "#fff"}
    visual_style: Optional[str] = None
    artist_persona: Optional[str] = None
    content_do: Optional[str] = None
    content_dont: Optional[str] = None
    sample_references: Optional[str] = None
    creative_notes: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_artist_id(user_id: str, db: AsyncSession) -> str:
    """Resolve artist_id from user_id. Raises 404 if no artist profile."""
    result = await db.execute(
        text("SELECT id FROM artists WHERE user_id = CAST(:uid AS UUID) LIMIT 1"),
        {"uid": user_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="No artist profile found for this account")
    return str(row["id"])


async def _upsert_config(
    artist_id: str,
    agent_id: str,
    updates: dict,
    via: str,
    db: AsyncSession,
) -> dict:
    """Insert or update agent config. Returns the updated row."""
    # Check existing
    existing = await db.execute(
        text("SELECT id, version FROM artist_agent_config WHERE artist_id = CAST(:aid AS UUID) AND agent_id = :agent"),
        {"aid": artist_id, "agent": agent_id},
    )
    row = existing.mappings().first()

    if row:
        set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
        params = {**updates, "aid": artist_id, "agent": agent_id}
        await db.execute(
            text(f"UPDATE artist_agent_config SET {set_clauses}, version = version + 1, updated_at = NOW(), set_via = :via WHERE artist_id = CAST(:aid AS UUID) AND agent_id = :agent"),
            {**params, "via": via},
        )
    else:
        col_names = ", ".join(updates.keys())
        col_params = ", ".join(f":{k}" for k in updates.keys())
        await db.execute(
            text(f"INSERT INTO artist_agent_config (artist_id, agent_id, {col_names}, set_via) VALUES (CAST(:aid AS UUID), :agent, {col_params}, :via)"),
            {**updates, "aid": artist_id, "agent": agent_id, "via": via},
        )
    await db.commit()

    # Return current state
    result = await db.execute(
        text("SELECT * FROM artist_agent_config WHERE artist_id = CAST(:aid AS UUID) AND agent_id = :agent"),
        {"aid": artist_id, "agent": agent_id},
    )
    final = result.mappings().first()
    return dict(final) if final else {}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/me")
async def get_my_configs(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get all agent configs for the authenticated artist."""
    artist_id = await _get_artist_id(current_user.user_id, db)
    result = await db.execute(
        text("SELECT * FROM artist_agent_config WHERE artist_id = CAST(:aid AS UUID) AND is_active = TRUE ORDER BY agent_id"),
        {"aid": artist_id},
    )
    rows = result.mappings().all()
    configs = {}
    for row in rows:
        d = dict(row)
        # Parse JSON fields
        for f in ("preferred_channels", "excluded_channels", "playlist_targets", "color_palette"):
            if d.get(f) and isinstance(d[f], str):
                try:
                    d[f] = json.loads(d[f])
                except Exception:
                    pass
        configs[d["agent_id"]] = d
    return {
        "artist_id": artist_id,
        "configs": configs,
        "whatsapp_commands": {
            "set": "/set [marketing|creative] [field] [value]",
            "view": "/config",
            "reset": "/reset [marketing|creative]",
            "help": "/help",
        },
    }


@router.get("/{agent_id}")
async def get_agent_config(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get config for a specific agent (marketing or creative)."""
    if agent_id not in ("marketing", "creative"):
        raise HTTPException(status_code=400, detail="agent_id must be 'marketing' or 'creative'")
    artist_id = await _get_artist_id(current_user.user_id, db)
    result = await db.execute(
        text("SELECT * FROM artist_agent_config WHERE artist_id = CAST(:aid AS UUID) AND agent_id = :agent AND is_active = TRUE"),
        {"aid": artist_id, "agent": agent_id},
    )
    row = result.mappings().first()
    if not row:
        return {"agent_id": agent_id, "config": None, "note": "No custom config — using Melodio defaults"}
    d = dict(row)
    for f in ("preferred_channels", "excluded_channels", "playlist_targets", "color_palette"):
        if d.get(f) and isinstance(d[f], str):
            try:
                d[f] = json.loads(d[f])
            except Exception:
                pass
    return {"agent_id": agent_id, "config": d}


@router.put("/marketing")
async def update_marketing_config(
    body: MarketingConfig,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Update marketing agent config for the authenticated artist."""
    artist_id = await _get_artist_id(current_user.user_id, db)
    updates = {}
    data = body.model_dump(exclude_none=True)
    for k, v in data.items():
        if k not in _MARKETING_ALLOWED:
            continue
        if isinstance(v, (list, dict)):
            updates[k] = json.dumps(v)
        else:
            updates[k] = v
    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    result = await _upsert_config(artist_id, "marketing", updates, "api", db)
    logger.info(f"[artist_config] Artist {artist_id} updated marketing config via API")
    return {"status": "updated", "agent_id": "marketing", "config": result}


@router.put("/creative")
async def update_creative_config(
    body: CreativeConfig,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Update creative agent config for the authenticated artist."""
    artist_id = await _get_artist_id(current_user.user_id, db)
    updates = {}
    data = body.model_dump(exclude_none=True)
    for k, v in data.items():
        if k not in _CREATIVE_ALLOWED:
            continue
        if isinstance(v, (list, dict)):
            updates[k] = json.dumps(v)
        else:
            updates[k] = v
    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    result = await _upsert_config(artist_id, "creative", updates, "api", db)
    logger.info(f"[artist_config] Artist {artist_id} updated creative config via API")
    return {"status": "updated", "agent_id": "creative", "config": result}


@router.delete("/{agent_id}")
async def reset_agent_config(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Reset (delete) custom config for a specific agent — reverts to Melodio defaults."""
    if agent_id not in ("marketing", "creative"):
        raise HTTPException(status_code=400, detail="agent_id must be 'marketing' or 'creative'")
    artist_id = await _get_artist_id(current_user.user_id, db)
    await db.execute(
        text("DELETE FROM artist_agent_config WHERE artist_id = CAST(:aid AS UUID) AND agent_id = :agent"),
        {"aid": artist_id, "agent": agent_id},
    )
    await db.commit()
    return {"status": "reset", "agent_id": agent_id, "note": "Reverted to Melodio defaults"}
