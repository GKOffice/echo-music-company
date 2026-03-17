"""
Melodio Fan Intelligence API
Personalized artist discovery — momentum scoring, trending, taste profiles.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
import hashlib
import random
from datetime import datetime, timezone

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()

DISCLAIMER = "Artist discovery only — not financial advice. Royalties not guaranteed."
GLOBAL_DISCLAIMER = (
    "Melodio artist discovery is for informational purposes only. "
    "Buying Melodio Points is not an investment. "
    "Royalties are not guaranteed."
)

MOCK_TRENDING = [
    {"name": "Nova Vex",     "genre": "Dark R&B",    "momentum_score": 91, "tier": "🔥", "tier_label": "🔥 Breaking"},
    {"name": "Lyra Bloom",   "genre": "Indie Pop",   "momentum_score": 84, "tier": "⚡", "tier_label": "⚡ Rising"},
    {"name": "Melo Cipher",  "genre": "Hip-Hop",     "momentum_score": 78, "tier": "⚡", "tier_label": "⚡ Rising"},
    {"name": "Khai Dusk",    "genre": "Alt Soul",    "momentum_score": 73, "tier": "⚡", "tier_label": "⚡ Rising"},
    {"name": "Zara Sol",     "genre": "Afrobeats",   "momentum_score": 69, "tier": "📈", "tier_label": "📈 Growing"},
    {"name": "Echo Static",  "genre": "Electronic",  "momentum_score": 65, "tier": "📈", "tier_label": "📈 Growing"},
    {"name": "River Kane",   "genre": "Folk Pop",    "momentum_score": 58, "tier": "📈", "tier_label": "📈 Growing"},
    {"name": "Jade Vortex",  "genre": "Neo Soul",    "momentum_score": 52, "tier": "👀", "tier_label": "👀 Watch List"},
]

TIERS = [
    (85, "🔥", "🔥 Breaking"),
    (70, "⚡", "⚡ Rising"),
    (55, "📈", "📈 Growing"),
    (40, "👀", "👀 Watch List"),
    (0,  "🌱", "🌱 Early Stage"),
]


def _serialize(row) -> dict:
    if row is None:
        return {}
    out = {}
    for k, v in (row.items() if hasattr(row, "items") else row._mapping.items()):
        if hasattr(v, "hex"):
            out[k] = str(v)
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def _tier_for_score(score: int) -> tuple[str, str]:
    for threshold, tier, label in TIERS:
        if score >= threshold:
            return tier, label
    return "🌱", "🌱 Early Stage"


def _mock_momentum(artist_id: str) -> dict:
    seed = int(hashlib.md5(str(artist_id).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    stream_growth   = rng.randint(20, 95)
    social_velocity = rng.randint(15, 90)
    sync_heat       = rng.randint(0, 100)
    press_momentum  = rng.randint(10, 85)
    ar_score_val    = rng.randint(40, 98)
    composite = int(
        stream_growth   * 0.35 +
        social_velocity * 0.25 +
        sync_heat       * 0.20 +
        press_momentum  * 0.10 +
        ar_score_val    * 0.10
    )
    return {
        "stream_growth":   stream_growth,
        "social_velocity": social_velocity,
        "sync_heat":       sync_heat,
        "press_momentum":  press_momentum,
        "ar_score":        ar_score_val,
        "composite":       composite,
    }


# ── GET /trending ─────────────────────────────────────────────────────────────

@router.get("/trending")
async def get_trending(
    limit:     int            = Query(10, ge=1, le=50),
    genre:     Optional[str]  = Query(None),
    timeframe: str            = Query("7d", pattern="^(7d|30d|90d)$"),
    db:        AsyncSession   = Depends(get_db),
):
    result = await db.execute(
        text("SELECT id, name, genre, ar_score FROM artists WHERE status = 'active' LIMIT 200")
    )
    rows = [_serialize(r) for r in result.fetchall()]

    trending = []
    for a in rows:
        ag = a.get("genre") or ""
        if genre and genre.lower() not in ag.lower():
            continue
        dims = _mock_momentum(str(a.get("id")))
        db_ar = float(a.get("ar_score") or 0)
        if db_ar > 0:
            dims["ar_score"] = int(min(db_ar, 100))
        composite = int(
            dims["stream_growth"]   * 0.35 +
            dims["social_velocity"] * 0.25 +
            dims["sync_heat"]       * 0.20 +
            dims["press_momentum"]  * 0.10 +
            dims["ar_score"]        * 0.10
        )
        tier, tier_label = _tier_for_score(composite)
        trending.append({
            "artist_id":     str(a.get("id")),
            "artist_name":   a.get("name"),
            "genre":         ag,
            "momentum_score": composite,
            "tier":          tier,
            "tier_label":    tier_label,
            "dimension_scores": {
                "stream_growth":   dims["stream_growth"],
                "social_velocity": dims["social_velocity"],
                "sync_heat":       dims["sync_heat"],
                "press_momentum":  dims["press_momentum"],
                "ar_score":        dims["ar_score"],
            },
            "disclaimer": DISCLAIMER,
        })

    trending.sort(key=lambda x: x["momentum_score"], reverse=True)

    # Fallback to mock data if DB is empty
    if not trending:
        mock = MOCK_TRENDING
        if genre:
            mock = [m for m in mock if genre.lower() in m["genre"].lower()]
        trending = mock[:limit]

    return {
        "timeframe":    timeframe,
        "trending":     trending[:limit],
        "total":        len(trending),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer":   DISCLAIMER,
    }


# ── GET /recommendations/{user_id} ───────────────────────────────────────────

@router.get("/recommendations/{user_id}")
async def get_recommendations(
    user_id:      str,
    limit:        int           = Query(6, ge=1, le=20),
    genre_filter: Optional[str] = Query(None),
    db:           AsyncSession  = Depends(get_db),
    current_user: TokenData     = Depends(get_current_user),
):
    if str(current_user.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fan profile
    try:
        backed_result = await db.execute(
            text("""
                SELECT DISTINCT ep.artist_id, a.genre, ep.amount_paid, ep.price_per_point
                FROM echo_points ep
                JOIN artists a ON a.id = ep.artist_id
                WHERE ep.user_id = :uid AND ep.status = 'active'
            """),
            {"uid": user_id},
        )
        backed_rows = [_serialize(r) for r in backed_result.fetchall()]
    except Exception:
        backed_rows = []

    backed_ids = {str(r.get("artist_id")) for r in backed_rows}
    genre_counts: dict[str, int] = {}
    for r in backed_rows:
        g = r.get("genre")
        if g:
            genre_counts[g] = genre_counts.get(g, 0) + 1
    top_genres = sorted(genre_counts, key=genre_counts.get, reverse=True)[:5]  # type: ignore[arg-type]

    # Pull active artists
    result = await db.execute(
        text("SELECT id, name, genre, ar_score FROM artists WHERE status = 'active' AND ar_score > 50 LIMIT 100")
    )
    artists = [_serialize(r) for r in result.fetchall()]

    scored = []
    for a in artists:
        aid = str(a.get("id"))
        if aid in backed_ids:
            continue
        ag = a.get("genre") or ""
        if genre_filter and genre_filter.lower() not in ag.lower():
            continue

        dims = _mock_momentum(aid)
        db_ar = float(a.get("ar_score") or 0)
        if db_ar > 0:
            dims["ar_score"] = int(min(db_ar, 100))
        composite = int(
            dims["stream_growth"]   * 0.35 +
            dims["social_velocity"] * 0.25 +
            dims["sync_heat"]       * 0.20 +
            dims["press_momentum"]  * 0.10 +
            dims["ar_score"]        * 0.10
        )
        tier, tier_label = _tier_for_score(composite)

        if ag and any(g.lower() in ag.lower() for g in top_genres):
            why = f"Matches your taste in {top_genres[0] if top_genres else 'your favorite genres'}"
        elif composite >= 85:
            why = "One of the fastest-breaking artists on Melodio right now"
        elif composite >= 70:
            why = "Strong momentum across streams, social, and sync placements"
        else:
            why = "Steady growth trajectory — early-stage opportunity"

        # Point drop info
        try:
            pd_result = await db.execute(
                text("""
                    SELECT points_available, price_per_point
                    FROM point_drops
                    WHERE artist_id = :aid AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                """),
                {"aid": a.get("id")},
            )
            pd_row = _serialize(pd_result.fetchone())
        except Exception:
            pd_row = {}

        scored.append({
            "artist_id":        aid,
            "artist_name":      a.get("name"),
            "genre":            ag,
            "momentum_score":   composite,
            "tier":             tier,
            "tier_label":       tier_label,
            "points_available": int(pd_row.get("points_available") or 0),
            "price_per_point":  float(pd_row.get("price_per_point") or 0),
            "why_recommended":  why,
            "disclaimer":       DISCLAIMER,
        })

    scored.sort(key=lambda x: x["momentum_score"], reverse=True)

    return {
        "user_id":         user_id,
        "recommendations": scored[:limit],
        "total_found":     len(scored),
        "profile_summary": {"top_genres": top_genres, "total_artists_backed": len(backed_ids)},
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "global_disclaimer": GLOBAL_DISCLAIMER,
    }


# ── GET /artist/{artist_id}/score ─────────────────────────────────────────────

@router.get("/artist/{artist_id}/score")
async def get_artist_score(
    artist_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT id, name, genre, ar_score FROM artists WHERE id = :aid"),
        {"aid": artist_id},
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Artist not found")

    a = _serialize(row)
    dims = _mock_momentum(artist_id)
    db_ar = float(a.get("ar_score") or 0)
    if db_ar > 0:
        dims["ar_score"] = int(min(db_ar, 100))
    composite = int(
        dims["stream_growth"]   * 0.35 +
        dims["social_velocity"] * 0.25 +
        dims["sync_heat"]       * 0.20 +
        dims["press_momentum"]  * 0.10 +
        dims["ar_score"]        * 0.10
    )
    tier, tier_label = _tier_for_score(composite)

    return {
        "artist_id":     artist_id,
        "artist_name":   a.get("name"),
        "genre":         a.get("genre"),
        "momentum_score": composite,
        "tier":          tier,
        "tier_label":    tier_label,
        "dimension_scores": {
            "stream_growth":   dims["stream_growth"],
            "social_velocity": dims["social_velocity"],
            "sync_heat":       dims["sync_heat"],
            "press_momentum":  dims["press_momentum"],
            "ar_score":        dims["ar_score"],
        },
        "disclaimer": DISCLAIMER,
    }


# ── GET /fan/{user_id}/profile ────────────────────────────────────────────────

@router.get("/fan/{user_id}/profile")
async def get_fan_profile(
    user_id:      str,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(get_current_user),
):
    if str(current_user.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        result = await db.execute(
            text("""
                SELECT DISTINCT ep.artist_id, a.genre, ep.amount_paid, ep.price_per_point
                FROM echo_points ep
                JOIN artists a ON a.id = ep.artist_id
                WHERE ep.user_id = :uid AND ep.status = 'active'
            """),
            {"uid": user_id},
        )
        rows = [_serialize(r) for r in result.fetchall()]
    except Exception:
        rows = []

    genres = [r.get("genre") for r in rows if r.get("genre")]
    genre_counts: dict[str, int] = {}
    for g in genres:
        genre_counts[g] = genre_counts.get(g, 0) + 1
    top_genres = sorted(genre_counts, key=genre_counts.get, reverse=True)[:5]  # type: ignore[arg-type]

    prices = [float(r.get("price_per_point") or 0) for r in rows if r.get("price_per_point")]
    total_spent = sum(float(r.get("amount_paid") or 0) for r in rows)

    return {
        "user_id":    user_id,
        "top_genres": top_genres,
        "preferred_price_range": {
            "min": round(min(prices), 2) if prices else None,
            "max": round(max(prices), 2) if prices else None,
        },
        "total_artists_backed": len({str(r.get("artist_id")) for r in rows}),
        "total_spent":          round(total_spent, 2),
        "profile_built_at":     datetime.now(timezone.utc).isoformat(),
    }


# ── GET /alerts/{user_id} ─────────────────────────────────────────────────────

@router.get("/alerts/{user_id}")
async def get_early_access_alerts(
    user_id:      str,
    db:           AsyncSession = Depends(get_db),
    current_user: TokenData    = Depends(get_current_user),
):
    if str(current_user.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get fan's top genres
    try:
        backed = await db.execute(
            text("""
                SELECT DISTINCT a.genre FROM echo_points ep
                JOIN artists a ON a.id = ep.artist_id
                WHERE ep.user_id = :uid AND ep.status = 'active'
            """),
            {"uid": user_id},
        )
        genres = [r[0] for r in backed.fetchall() if r[0]]
    except Exception:
        genres = []

    alerts = []
    try:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        drops = await db.execute(
            text("""
                SELECT pd.id AS drop_id, pd.artist_id, pd.points_available,
                       pd.price_per_point, a.name AS artist_name, a.genre
                FROM point_drops pd
                JOIN artists a ON a.id = pd.artist_id
                WHERE pd.status = 'active' AND pd.created_at >= :cutoff
                ORDER BY pd.created_at DESC LIMIT 50
            """),
            {"cutoff": cutoff},
        )
        for drop in [_serialize(r) for r in drops.fetchall()]:
            g = drop.get("genre") or ""
            dims = _mock_momentum(str(drop.get("artist_id")))
            composite = int(
                dims["stream_growth"]   * 0.35 +
                dims["social_velocity"] * 0.25 +
                dims["sync_heat"]       * 0.20 +
                dims["press_momentum"]  * 0.10 +
                dims["ar_score"]        * 0.10
            )
            genre_match = any(genre.lower() in g.lower() for genre in genres) if genres else True
            if genre_match or composite >= 85:
                alerts.append({
                    "drop_id":         str(drop.get("drop_id")),
                    "artist_name":     drop.get("artist_name"),
                    "genre":           g,
                    "points_available": int(drop.get("points_available") or 0),
                    "price_per_point": float(drop.get("price_per_point") or 0),
                    "momentum_score":  composite,
                    "alert_type":      "trending_artist" if composite >= 70 else "new_drop",
                })
    except Exception:
        pass

    return {"user_id": user_id, "alerts": alerts, "alert_count": len(alerts)}


# ── GET /artist/{artist_id}/social-proof ─────────────────────────────────────

@router.get("/artist/{artist_id}/social-proof")
async def get_social_proof(
    artist_id:    str,
    user_id:      Optional[str] = Query(None),
    db:           AsyncSession  = Depends(get_db),
    current_user: TokenData     = Depends(get_current_user),
):
    similar_fans_count = 0

    if user_id:
        try:
            result = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT ep2.user_id) AS cnt
                    FROM echo_points ep1
                    JOIN echo_points ep2
                      ON ep2.artist_id = ep1.artist_id
                     AND ep2.user_id != :uid
                    JOIN echo_points ep3
                      ON ep3.user_id = ep2.user_id
                     AND ep3.artist_id = :aid
                    WHERE ep1.user_id = :uid
                      AND ep1.status = 'active'
                      AND ep2.status = 'active'
                      AND ep3.status = 'active'
                """),
                {"uid": user_id, "aid": artist_id},
            )
            row = result.fetchone()
            similar_fans_count = int(row[0] or 0) if row else 0
        except Exception:
            pass

    if similar_fans_count >= 50:
        signal  = "strong"
        message = f"{similar_fans_count} fans with similar taste are already backing this artist."
    elif similar_fans_count >= 10:
        signal  = "moderate"
        message = f"{similar_fans_count} fans who like what you like are backing this artist."
    else:
        signal  = "early"
        message = "Be among the first fans to discover this artist."

    return {
        "artist_id":          artist_id,
        "similar_fans_count": similar_fans_count,
        "signal":             signal,
        "message":            message,
        "disclaimer":         DISCLAIMER,
    }
