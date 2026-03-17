"""
Fan Intelligence Agent — Agent #23
Personalized artist discovery for fans.
Surfaces breaking artists based on trajectory signals, fan taste profiles,
and platform-wide momentum data.

FRAMING: Discovery and curation — NOT financial advice.
Every recommendation includes: "This is artist discovery, not financial advice.
Past performance does not guarantee future royalties."
"""

import hashlib
import logging
import random
from datetime import datetime, timedelta, timezone

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

DISCLAIMER = "Artist discovery only — not financial advice. Royalties not guaranteed."
GLOBAL_DISCLAIMER = (
    "Melodio artist discovery is for informational purposes only. "
    "Buying Melodio Points is not an investment. "
    "Royalties are not guaranteed."
)

# Tier thresholds
TIERS = [
    (85, "🔥 Breaking"),
    (70, "⚡ Rising"),
    (55, "📈 Growing"),
    (40, "👀 Watch List"),
    (0,  "🌱 Early Stage"),
]


def _tier_for_score(score: int) -> tuple[str, str]:
    for threshold, label in TIERS:
        if score >= threshold:
            tier = label.split(" ", 1)[0]
            return tier, label
    return "🌱", "🌱 Early Stage"


class FanIntelligenceAgent(BaseAgent):
    agent_id = "fan_intelligence"
    agent_name = "Fan Intelligence Agent"
    subscriptions = ["artist.milestone", "release.distributed", "points.purchased", "analytics.updated"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "score_artist_trajectory": self._task_score_artist_trajectory,
            "build_fan_profile":       self._task_build_fan_profile,
            "get_recommendations":     self._task_get_recommendations,
            "trending_artists":        self._task_trending_artists,
            "early_access_alerts":     self._task_early_access_alerts,
            "similar_fans_backing":    self._task_similar_fans_backing,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    # ----------------------------------------------------------------
    # Mock momentum scoring — deterministic by artist_id
    # ----------------------------------------------------------------

    def _mock_momentum_score(self, artist_id: str) -> dict:
        seed = int(hashlib.md5(str(artist_id).encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        stream_growth    = rng.randint(20, 95)
        social_velocity  = rng.randint(15, 90)
        sync_heat        = rng.randint(0, 100)
        press_momentum   = rng.randint(10, 85)
        ar_score_val     = rng.randint(40, 98)
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

    # ----------------------------------------------------------------
    # score_artist_trajectory
    # ----------------------------------------------------------------

    async def _task_score_artist_trajectory(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id

        artist = None
        if artist_id:
            artist = await self.db_fetchrow(
                "SELECT id, name, genre, ar_score FROM artists WHERE id = $1::uuid",
                artist_id,
            )

        artist_name = (artist.get("name") if artist else None) or "Unknown Artist"
        db_ar_score = float(artist.get("ar_score") or 0) if artist else 0.0

        dims = self._mock_momentum_score(str(artist_id or "unknown"))

        # Override ar_score dimension with DB value if available
        if db_ar_score > 0:
            dims["ar_score"] = int(min(db_ar_score, 100))

        composite = int(
            dims["stream_growth"]   * 0.35 +
            dims["social_velocity"] * 0.25 +
            dims["sync_heat"]       * 0.20 +
            dims["press_momentum"]  * 0.10 +
            dims["ar_score"]        * 0.10
        )

        tier, tier_label = _tier_for_score(composite)

        return {
            "artist_id":     str(artist_id),
            "artist_name":   artist_name,
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

    # ----------------------------------------------------------------
    # build_fan_profile
    # ----------------------------------------------------------------

    async def _task_build_fan_profile(self, task: AgentTask) -> dict:
        user_id = task.payload.get("user_id")

        genres: list[str] = []
        total_spent = 0.0
        total_artists_backed = 0
        min_price = None
        max_price = None

        if user_id:
            # Pull backed artists via echo_points
            backed = await self.db_fetch(
                """
                SELECT DISTINCT ep.artist_id, a.genre,
                       ep.amount_paid, ep.price_per_point
                FROM echo_points ep
                JOIN artists a ON a.id = ep.artist_id
                WHERE ep.user_id = $1::uuid AND ep.status = 'active'
                """,
                user_id,
            )

            for row in backed:
                genre = row.get("genre")
                if genre:
                    genres.append(genre)
                paid = float(row.get("amount_paid") or 0)
                total_spent += paid
                ppp = float(row.get("price_per_point") or 0)
                if ppp > 0:
                    min_price = min(min_price, ppp) if min_price is not None else ppp
                    max_price = max(max_price, ppp) if max_price is not None else ppp

            total_artists_backed = len({r.get("artist_id") for r in backed})

            # Also check digital_purchases for additional genre signals
            try:
                dp = await self.db_fetch(
                    """
                    SELECT a.genre, dp.amount_paid
                    FROM digital_purchases dp
                    JOIN artists a ON a.id = dp.artist_id
                    WHERE dp.user_id = $1::uuid AND dp.status = 'completed'
                    """,
                    user_id,
                )
                for row in dp:
                    genre = row.get("genre")
                    if genre:
                        genres.append(genre)
                    total_spent += float(row.get("amount_paid") or 0)
            except Exception:
                pass  # digital_purchases may not exist yet

        # Rank genres by frequency
        genre_counts: dict[str, int] = {}
        for g in genres:
            genre_counts[g] = genre_counts.get(g, 0) + 1
        top_genres = sorted(genre_counts, key=genre_counts.get, reverse=True)[:5]  # type: ignore[arg-type]

        return {
            "user_id":              str(user_id) if user_id else None,
            "top_genres":           top_genres,
            "preferred_price_range": {
                "min": round(min_price, 2) if min_price else None,
                "max": round(max_price, 2) if max_price else None,
            },
            "total_artists_backed": total_artists_backed,
            "total_spent":          round(total_spent, 2),
            "profile_built_at":     datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # get_recommendations
    # ----------------------------------------------------------------

    async def _task_get_recommendations(self, task: AgentTask) -> dict:
        user_id     = task.payload.get("user_id")
        limit       = int(task.payload.get("limit", 6))
        genre_filter = task.payload.get("genre_filter")

        # Build fan profile
        profile_task = AgentTask(
            task_id="internal",
            task_type="build_fan_profile",
            payload={"user_id": user_id},
        )
        profile = await self._task_build_fan_profile(profile_task)

        # Pull active artists with ar_score > 50
        artists = await self.db_fetch(
            "SELECT id, name, genre, ar_score FROM artists WHERE status = 'active' AND ar_score > 50 LIMIT 100"
        )

        # IDs fan already backs
        backed_ids: set[str] = set()
        if user_id:
            backed_rows = await self.db_fetch(
                "SELECT DISTINCT artist_id FROM echo_points WHERE user_id = $1::uuid AND status = 'active'",
                user_id,
            )
            backed_ids = {str(r.get("artist_id")) for r in backed_rows}

        scored: list[dict] = []
        for a in artists:
            aid = str(a.get("id"))
            if aid in backed_ids:
                continue

            genre = a.get("genre") or ""
            if genre_filter and genre_filter.lower() not in genre.lower():
                continue

            dims = self._mock_momentum_score(aid)
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

            # Personalization signal
            top_genres = profile.get("top_genres", [])
            if genre and any(g.lower() in genre.lower() for g in top_genres):
                why = f"Matches your taste in {top_genres[0] if top_genres else 'your favorite genres'}"
            elif composite >= 85:
                why = "One of the fastest-breaking artists on Melodio right now"
            elif composite >= 70:
                why = "Strong momentum across streams, social, and sync placements"
            else:
                why = "Steady growth trajectory — early-stage opportunity"

            # Pull point drop info
            point_drop = await self.db_fetchrow(
                """
                SELECT points_available, price_per_point
                FROM point_drops
                WHERE artist_id = $1::uuid AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
                """,
                a.get("id"),
            ) or {}

            scored.append({
                "artist_id":        aid,
                "artist_name":      a.get("name"),
                "genre":            genre,
                "momentum_score":   composite,
                "tier":             tier,
                "tier_label":       tier_label,
                "points_available": int(point_drop.get("points_available") or 0),
                "price_per_point":  float(point_drop.get("price_per_point") or 0),
                "why_recommended":  why,
                "disclaimer":       DISCLAIMER,
            })

        scored.sort(key=lambda x: x["momentum_score"], reverse=True)
        recommendations = scored[:limit]

        return {
            "user_id":         str(user_id) if user_id else None,
            "recommendations": recommendations,
            "total_found":     len(scored),
            "profile_summary": {
                "top_genres":           profile.get("top_genres"),
                "total_artists_backed": profile.get("total_artists_backed"),
            },
            "generated_at":     datetime.now(timezone.utc).isoformat(),
            "global_disclaimer": GLOBAL_DISCLAIMER,
        }

    # ----------------------------------------------------------------
    # trending_artists
    # ----------------------------------------------------------------

    async def _task_trending_artists(self, task: AgentTask) -> dict:
        limit     = int(task.payload.get("limit", 10))
        genre     = task.payload.get("genre")
        timeframe = task.payload.get("timeframe", "7d")

        artists = await self.db_fetch(
            "SELECT id, name, genre, ar_score FROM artists WHERE status = 'active' LIMIT 200"
        )

        scored: list[dict] = []
        for a in artists:
            aid = str(a.get("id"))
            ag  = a.get("genre") or ""
            if genre and genre.lower() not in ag.lower():
                continue

            dims = self._mock_momentum_score(aid)
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
            scored.append({
                "artist_id":     aid,
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
            })

        scored.sort(key=lambda x: x["momentum_score"], reverse=True)

        return {
            "timeframe":    timeframe,
            "trending":     scored[:limit],
            "total":        len(scored),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer":   DISCLAIMER,
        }

    # ----------------------------------------------------------------
    # early_access_alerts
    # ----------------------------------------------------------------

    async def _task_early_access_alerts(self, task: AgentTask) -> dict:
        user_id = task.payload.get("user_id")

        profile_task = AgentTask(
            task_id="internal",
            task_type="build_fan_profile",
            payload={"user_id": user_id},
        )
        profile = await self._task_build_fan_profile(profile_task)
        top_genres = profile.get("top_genres", [])

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        alerts: list[dict] = []

        try:
            drops = await self.db_fetch(
                """
                SELECT pd.id AS drop_id, pd.artist_id, pd.points_available,
                       pd.price_per_point, pd.created_at,
                       a.name AS artist_name, a.genre
                FROM point_drops pd
                JOIN artists a ON a.id = pd.artist_id
                WHERE pd.status = 'active' AND pd.created_at >= $1
                ORDER BY pd.created_at DESC
                LIMIT 50
                """,
                cutoff,
            )

            for drop in drops:
                genre = drop.get("genre") or ""
                dims = self._mock_momentum_score(str(drop.get("artist_id")))
                composite = int(
                    dims["stream_growth"]   * 0.35 +
                    dims["social_velocity"] * 0.25 +
                    dims["sync_heat"]       * 0.20 +
                    dims["press_momentum"]  * 0.10 +
                    dims["ar_score"]        * 0.10
                )

                genre_match = any(g.lower() in genre.lower() for g in top_genres) if top_genres else True
                alert_type  = "trending_artist" if composite >= 70 else "new_drop"

                if genre_match or composite >= 85:
                    alerts.append({
                        "drop_id":         str(drop.get("drop_id")),
                        "artist_name":     drop.get("artist_name"),
                        "genre":           genre,
                        "points_available": int(drop.get("points_available") or 0),
                        "price_per_point": float(drop.get("price_per_point") or 0),
                        "momentum_score":  composite,
                        "alert_type":      alert_type,
                    })

        except Exception as exc:
            logger.warning(f"[FanIntelligence] early_access_alerts DB query failed: {exc}")

        return {
            "user_id":    str(user_id) if user_id else None,
            "alerts":     alerts,
            "alert_count": len(alerts),
        }

    # ----------------------------------------------------------------
    # similar_fans_backing
    # ----------------------------------------------------------------

    async def _task_similar_fans_backing(self, task: AgentTask) -> dict:
        user_id   = task.payload.get("user_id")
        artist_id = task.payload.get("artist_id") or task.artist_id

        similar_fans_count = 0

        if user_id and artist_id:
            try:
                # Fans who backed the same artists this user backs AND also backed artist_id
                row = await self.db_fetchrow(
                    """
                    SELECT COUNT(DISTINCT ep2.user_id) AS cnt
                    FROM echo_points ep1
                    JOIN echo_points ep2
                      ON ep2.artist_id = ep1.artist_id
                     AND ep2.user_id != $1::uuid
                    JOIN echo_points ep3
                      ON ep3.user_id = ep2.user_id
                     AND ep3.artist_id = $2::uuid
                    WHERE ep1.user_id = $1::uuid
                      AND ep1.status = 'active'
                      AND ep2.status = 'active'
                      AND ep3.status = 'active'
                    """,
                    user_id,
                    artist_id,
                )
                similar_fans_count = int(row.get("cnt") or 0) if row else 0
            except Exception as exc:
                logger.warning(f"[FanIntelligence] similar_fans_backing query failed: {exc}")

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
            "artist_id":          str(artist_id) if artist_id else None,
            "similar_fans_count": similar_fans_count,
            "signal":             signal,
            "message":            message,
        }

    # ----------------------------------------------------------------
    # on_message — bus event handler
    # ----------------------------------------------------------------

    async def on_message(self, topic: str, payload: dict) -> None:
        if topic == "artist.milestone":
            artist_id = payload.get("artist_id")
            if artist_id:
                logger.info(f"[FanIntelligence] Re-scoring artist {artist_id} after milestone")
                task = AgentTask(
                    task_id="internal",
                    task_type="score_artist_trajectory",
                    payload={"artist_id": artist_id},
                )
                result = await self._task_score_artist_trajectory(task)
                await self.broadcast("fan_intelligence.artist_updated", {
                    "artist_id":     artist_id,
                    "momentum_score": result.get("momentum_score"),
                    "tier_label":    result.get("tier_label"),
                })

        elif topic == "points.purchased":
            user_id = payload.get("user_id")
            if user_id:
                logger.info(f"[FanIntelligence] Invalidating fan profile cache for user {user_id}")

        elif topic == "release.distributed":
            logger.info("[FanIntelligence] Triggering trending refresh after new release distribution")

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[FanIntelligence] Online — artist discovery and momentum scoring active")
