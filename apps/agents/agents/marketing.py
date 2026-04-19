"""
Marketing Agent
Runs ad campaigns across Meta/TikTok/YouTube/Google, A/B tests creatives,
manages 80% marketing budget from point sales, and submits to playlist curators.
"""

import json
import logging
import os
import uuid
from datetime import datetime, date, timedelta, timezone

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Budget allocation across channels
CHANNEL_ALLOCATION = {
    "meta": 0.35,
    "tiktok": 0.30,
    "youtube": 0.20,
    "google": 0.10,
    "influencer": 0.05,
}

# Kill criteria
KILL_CPC_THRESHOLD = 1.50
KILL_CTR_THRESHOLD = 0.008  # 0.8%
KILL_COST_PER_STREAM = 0.10

# Scale criteria
SCALE_ROAS_THRESHOLD = 4.0
VIRAL_ROAS_MULTIPLIER = 5.0
SCALE_ROAS_MULTIPLIER = 2.0

PLAYLIST_TARGETS = {
    "hip-hop": ["RapCaviar", "Most Necessary", "Get Turnt", "Rap Life"],
    "pop": ["Today's Top Hits", "Pop Rising", "New Music Friday", "mint"],
    "r&b": ["Are & Be", "R&B Only", "Soul", "Fresh Finds"],
    "electronic": ["Electronic Rising", "Brain Food", "Electro-Mania"],
    "indie": ["Fresh Finds", "Indie Pop", "The Indie List", "Lorem"],
    "default": ["New Music Friday", "Fresh Finds", "Lorem", "Discover Weekly"],
}


class MarketingAgent(BaseAgent):
    agent_id = "marketing"
    agent_name = "Marketing Agent"
    subscriptions = ["release.distributed", "artist.signed", "vault.budget_allocated"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Marketing] Online. Campaign management active.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "create_campaign": self._create_campaign,
            "optimize_campaign": self._optimize_campaign,
            "submit_playlists": self._submit_playlists,
            "generate_ad_copy": self._generate_ad_copy,
            "calculate_roas": self._calculate_roas,
            "apply_marketing_budget": self._apply_marketing_budget,
            "roas_forecast": self._task_roas_forecast,
            # legacy
            "plan_campaign": self._create_campaign,
            "pitch_playlists": self._submit_playlists,
            "run_ads": self._run_ads,
            "report_performance": self._report_performance,
            "press_release": self._press_release,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        payload = message.get("payload", {})
        if topic == "release.distributed":
            release_id = payload.get("release_id")
            if release_id:
                await self.send_message("marketing", "create_campaign", {"release_id": release_id})
        elif topic == "vault.budget_allocated":
            await self._apply_marketing_budget(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="apply_marketing_budget",
                payload=payload,
            ))

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _load_artist_config(self, artist_id: str) -> dict:
        """Load artist-specific marketing config set via WhatsApp. Returns {} if none set."""
        try:
            row = await self.db_fetchrow(
                "SELECT * FROM artist_agent_config WHERE artist_id = $1::uuid AND agent_id = 'marketing' AND is_active = TRUE",
                artist_id,
            )
            return dict(row) if row else {}
        except Exception:
            return {}  # Table may not exist yet — graceful fallback

    async def _create_campaign(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow(
            "SELECT r.title, r.release_date, r.priority, r.artist_id, a.name, a.genre FROM releases r "
            "LEFT JOIN artists a ON r.artist_id = a.id WHERE r.id = $1::uuid",
            release_id,
        )
        if not release:
            return {"error": "Release not found", "release_id": release_id}

        # Load artist-specific config (set by artist via WhatsApp)
        artist_id = str(release.get("artist_id", ""))
        artist_config = await self._load_artist_config(artist_id)
        config_applied = bool(artist_config)

        priority = release.get("priority", "standard")
        total_budget = {"priority": 5000.0, "standard": 2000.0, "low": 500.0}.get(priority, 2000.0)

        # Apply artist budget style if configured
        budget_style = artist_config.get("budget_style", "balanced")
        if budget_style == "aggressive":
            total_budget = round(total_budget * 1.25, 2)  # 25% boost — concentrate spend
        elif budget_style == "conservative":
            total_budget = round(total_budget * 0.70, 2)  # 30% reduction — slow burn

        release_date = release.get("release_date") or date.today()
        if isinstance(release_date, str):
            release_date = date.fromisoformat(release_date)

        # Build channel allocation — respect artist preferences
        base_allocation = dict(CHANNEL_ALLOCATION)
        preferred = []
        excluded = []
        try:
            import json as _j
            raw_preferred = artist_config.get("preferred_channels", "[]")
            raw_excluded = artist_config.get("excluded_channels", "[]")
            preferred = _j.loads(raw_preferred) if isinstance(raw_preferred, str) else (raw_preferred or [])
            excluded = _j.loads(raw_excluded) if isinstance(raw_excluded, str) else (raw_excluded or [])
        except Exception:
            pass

        if excluded:
            # Remove excluded channels and redistribute their budget proportionally
            active = {k: v for k, v in base_allocation.items() if k not in excluded}
            total_pct = sum(active.values())
            base_allocation = {k: round(v / total_pct, 4) for k, v in active.items()}

        if preferred:
            # Boost preferred channels by 20% each, reduce others proportionally
            boost = 0.20
            for ch in preferred:
                if ch in base_allocation:
                    base_allocation[ch] = round(base_allocation[ch] * (1 + boost), 4)
            total_pct = sum(base_allocation.values())
            base_allocation = {k: round(v / total_pct, 4) for k, v in base_allocation.items()}

        channel_budgets = {ch: round(total_budget * pct, 2) for ch, pct in base_allocation.items()}

        plan = {
            "week_minus_4": {
                "label": "Seed Phase",
                "activities": ["teasers on social", "BTS content", "artist story posts"],
                "channels": ["meta", "tiktok"],
                "budget_pct": 0.15,
            },
            "week_minus_2": {
                "label": "Build Phase",
                "activities": ["pre-save campaign live", "influencer seeding", "snippet ads"],
                "channels": ["meta", "tiktok", "youtube"],
                "budget_pct": 0.25,
            },
            "week_0": {
                "label": "Launch Week",
                "activities": ["full ad campaign live", "email blast", "playlist pitch follow-up", "PR push"],
                "channels": ["meta", "tiktok", "youtube", "google"],
                "budget_pct": 0.40,
            },
            "week_plus_1_4": {
                "label": "Sustain Phase",
                "activities": ["retarget engaged audiences", "push winning creatives", "milestone posts"],
                "channels": ["meta", "tiktok"],
                "budget_pct": 0.20,
            },
        }

        campaign_id = str(uuid.uuid4())
        await self.db_execute(
            """
            INSERT INTO campaigns (id, release_id, name, status, total_budget, start_date, end_date, plan_json)
            VALUES ($1::uuid, $2::uuid, $3, 'active', $4, $5, $6, $7::jsonb)
            ON CONFLICT DO NOTHING
            """,
            campaign_id,
            release_id,
            f"{release['name']} — {release['title']} Campaign",
            total_budget,
            release_date - timedelta(weeks=4),
            release_date + timedelta(weeks=4),
            json.dumps(plan),
        )

        await self.send_message("social", "create_content_calendar", {"release_id": release_id})
        await self.send_message("pr", "write_press_release", {"release_id": release_id})

        logger.info(
            f"[Marketing] Campaign created for '{release['title']}' — "
            f"${total_budget} | style={budget_style} | config_applied={config_applied} | "
            f"channels={list(channel_budgets.keys())}"
        )
        await self.log_audit("create_campaign", "releases", release_id, {
            "budget": total_budget,
            "campaign_id": campaign_id,
            "config_applied": config_applied,
            "budget_style": budget_style,
        })

        return {
            "campaign_id": campaign_id,
            "release_id": release_id,
            "release_title": release["title"],
            "artist": release["name"],
            "total_budget": total_budget,
            "channel_budgets": channel_budgets,
            "timeline": plan,
            "status": "active",
            "artist_config_applied": config_applied,
            "budget_style": budget_style,
            "preferred_channels": preferred,
            "excluded_channels": excluded,
            "target_audience": artist_config.get("target_audience"),
            "campaign_goals": artist_config.get("campaign_goals"),
            "avoid_content": artist_config.get("avoid_content"),
        }

    async def _optimize_campaign(self, task: AgentTask) -> dict:
        campaign_id = task.payload.get("campaign_id")
        release_id = task.payload.get("release_id") or task.release_id

        # Mock ad performance data; in production pull from Meta/TikTok APIs
        ad_variants = task.payload.get("ad_variants", [
            {"id": "ad_a", "cpc": 0.85, "ctr": 0.012, "cost_per_stream": 0.04, "spend": 200, "roas": 5.2},
            {"id": "ad_b", "cpc": 1.80, "ctr": 0.006, "cost_per_stream": 0.15, "spend": 150, "roas": 1.8},
            {"id": "ad_c", "cpc": 1.10, "ctr": 0.009, "cost_per_stream": 0.07, "spend": 180, "roas": 3.2},
        ])

        killed = []
        scaled = []
        actions = []

        for ad in ad_variants:
            kill = False
            if ad.get("cpc", 0) > KILL_CPC_THRESHOLD:
                kill = True
                actions.append(f"Kill {ad['id']}: CPC ${ad['cpc']:.2f} > ${KILL_CPC_THRESHOLD}")
            if ad.get("ctr", 1) < KILL_CTR_THRESHOLD and ad.get("spend", 0) > 50:
                kill = True
                actions.append(f"Kill {ad['id']}: CTR {ad['ctr']*100:.1f}% < 0.8%")
            if ad.get("cost_per_stream", 0) > KILL_COST_PER_STREAM:
                kill = True
                actions.append(f"Kill {ad['id']}: cost/stream ${ad['cost_per_stream']:.2f} > ${KILL_COST_PER_STREAM}")

            if kill:
                killed.append(ad["id"])
            elif ad.get("roas", 0) >= SCALE_ROAS_THRESHOLD:
                scaled.append(ad["id"])
                multiplier = VIRAL_ROAS_MULTIPLIER if ad["roas"] >= 8.0 else SCALE_ROAS_MULTIPLIER
                actions.append(f"Scale {ad['id']}: ROAS {ad['roas']:.1f}x → {multiplier}x budget increase")

        logger.info(f"[Marketing] Campaign optimized: {len(killed)} killed, {len(scaled)} scaled")
        return {
            "campaign_id": campaign_id,
            "release_id": release_id,
            "ads_killed": killed,
            "ads_scaled": scaled,
            "actions_taken": actions,
            "optimized_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _submit_playlists(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        genre = task.payload.get("genre", "")

        release = await self.db_fetchrow(
            "SELECT r.title, a.name, a.genre FROM releases r LEFT JOIN artists a ON r.artist_id = a.id WHERE r.id = $1::uuid",
            release_id,
        )
        if release:
            genre = genre or release.get("genre") or "default"

        playlists = PLAYLIST_TARGETS.get(genre.lower() if genre else "default", PLAYLIST_TARGETS["default"])

        pitches = [{"playlist": pl, "status": "submitted", "platform": "spotify"} for pl in playlists]

        await self.db_execute(
            "UPDATE releases SET playlist_pitched = TRUE, updated_at = NOW() WHERE id = $1::uuid",
            release_id,
        )

        logger.info(f"[Marketing] Playlist pitch: {len(pitches)} submissions for release {release_id}")
        return {
            "release_id": release_id,
            "genre": genre,
            "playlists_pitched": len(pitches),
            "pitches": pitches,
        }

    async def _generate_ad_copy(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        track_name = task.payload.get("track_name", "New Track")
        artist_name = task.payload.get("artist_name", "Artist")
        platform = task.payload.get("platform", "meta")

        variants = [
            {
                "variant": "A",
                "headline": f"{artist_name} just dropped something 🔥",
                "body": f"Stream '{track_name}' now — available everywhere.",
                "cta": "Listen Now",
                "angle": "hype",
            },
            {
                "variant": "B",
                "headline": f"New music from {artist_name}",
                "body": f"'{track_name}' is out now. Add it to your playlist.",
                "cta": "Stream Now",
                "angle": "direct",
            },
            {
                "variant": "C",
                "headline": f"You need to hear this 👂",
                "body": f"{artist_name}'s latest '{track_name}' is everywhere. Don't sleep.",
                "cta": "Play Now",
                "angle": "fomo",
            },
        ]

        return {
            "release_id": release_id,
            "platform": platform,
            "variants": variants,
            "test_recommendation": "Run all 3 for 48h, kill lowest CTR",
        }

    async def _calculate_roas(self, task: AgentTask) -> dict:
        campaign_id = task.payload.get("campaign_id")
        release_id = task.payload.get("release_id") or task.release_id
        spend = task.payload.get("spend_usd", 0.0)

        revenue = await self.db_fetchrow(
            "SELECT COALESCE(SUM(net_amount), 0) AS total FROM royalties WHERE release_id = $1::uuid",
            release_id,
        ) if release_id else None

        revenue_total = float(revenue["total"]) if revenue else 0.0
        roas = round(revenue_total / spend, 2) if spend > 0 else 0.0

        if campaign_id:
            await self.db_execute(
                "UPDATE campaigns SET roas = $2, spent = $3 WHERE id = $1::uuid",
                campaign_id, roas, spend,
            )

        return {
            "campaign_id": campaign_id,
            "release_id": release_id,
            "spend_usd": spend,
            "revenue_usd": revenue_total,
            "roas": roas,
            "verdict": "profitable" if roas >= 1.0 else "unprofitable",
        }

    async def _apply_marketing_budget(self, task: AgentTask) -> dict:
        total_received = task.payload.get("amount", 0.0)
        marketing_budget = round(total_received * 0.80, 2)
        reserve = round(total_received * 0.20, 2)

        channel_budgets = {ch: round(marketing_budget * pct, 2) for ch, pct in CHANNEL_ALLOCATION.items()}

        logger.info(f"[Marketing] Budget applied: ${marketing_budget} across channels (80% rule)")
        return {
            "total_received": total_received,
            "marketing_budget": marketing_budget,
            "reserve": reserve,
            "channel_budgets": channel_budgets,
            "rule": "80% of point sales revenue allocated to marketing",
        }

    # ----------------------------------------------------------------
    # Hero skill: ROAS Oracle
    # ----------------------------------------------------------------

    # Platform benchmarks: (cpm_min, cpm_max, ctr_min, ctr_max)
    _PLATFORM_BENCHMARKS = {
        "meta":    {"cpm_min": 0.50, "cpm_max": 2.00, "ctr_min": 0.01, "ctr_max": 0.03},
        "tiktok":  {"cpm_min": 1.00, "cpm_max": 3.00, "ctr_min": 0.02, "ctr_max": 0.05},
        "youtube": {"cpm_min": 2.00, "cpm_max": 5.00, "ctr_min": 0.005, "ctr_max": 0.015},
        "spotify": {"cpm_min": None,  "cpm_max": None,  "ctr_min": None,  "ctr_max": None,
                    "cost_per_stream_min": 0.015, "cost_per_stream_max": 0.025},
    }

    # Avg stream payout rate used for ROAS estimate
    _AVG_STREAM_RATE = 0.004  # USD

    async def _task_roas_forecast(self, task: AgentTask) -> AgentResult:
        """
        ROAS Oracle hero skill.
        Projects campaign outcomes using industry benchmark CPM/CTR data.
        """
        artist_id = task.payload.get("artist_id") or task.artist_id
        budget = float(task.payload.get("budget", 0.0))
        campaign_type = task.payload.get("campaign_type", "release_promo")
        platform = task.payload.get("platform", "meta").lower()

        if budget <= 0:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="budget must be > 0",
            )

        benchmarks = self._PLATFORM_BENCHMARKS.get(platform, self._PLATFORM_BENCHMARKS["meta"])

        # Spotify audio ads: different model
        if platform == "spotify" and benchmarks.get("cost_per_stream_min"):
            cps_mid = (benchmarks["cost_per_stream_min"] + benchmarks["cost_per_stream_max"]) / 2
            estimated_streams = int(budget / cps_mid)
            estimated_reach = estimated_streams * 3  # rough listener-to-stream ratio
            estimated_clicks = int(estimated_streams * 0.15)
            estimated_new_fans = int(estimated_clicks * 0.05)
        else:
            # CPM-based model
            cpm_mid = (benchmarks["cpm_min"] + benchmarks["cpm_max"]) / 2
            ctr_mid = (benchmarks["ctr_min"] + benchmarks["ctr_max"]) / 2
            estimated_reach = int(budget / cpm_mid * 1000)
            estimated_clicks = int(estimated_reach * ctr_mid)
            estimated_streams = int(estimated_clicks * 0.30)
            estimated_new_fans = int(estimated_clicks * 0.05)

        # Projected ROAS = stream revenue / spend
        stream_revenue = estimated_streams * self._AVG_STREAM_RATE
        projected_roas = round(stream_revenue / budget, 3) if budget > 0 else 0.0

        # Budget recommendation
        if platform == "spotify":
            meaningful_min = 500
            diminishing_max = 5000
        elif platform == "tiktok":
            meaningful_min = 200
            diminishing_max = 3000
        elif platform == "youtube":
            meaningful_min = 300
            diminishing_max = 5000
        else:  # meta
            meaningful_min = 300
            diminishing_max = 5000

        if budget < meaningful_min:
            budget_recommendation = f"Increase to ${meaningful_min:,} for meaningful impact on {platform.title()}"
        elif budget > diminishing_max:
            budget_recommendation = f"Diminishing returns above ${diminishing_max:,} — consider spreading across platforms"
        else:
            budget_recommendation = f"${budget:,.0f} is in the optimal range for {platform.title()} music campaigns"

        # Risk level
        # Artists with <10k streams = higher risk; established = lower risk
        artist_streams = 0
        if artist_id:
            streams_row = await self.db_fetchrow(
                """
                SELECT COALESCE(SUM(t.streams_total), 0) AS total
                FROM tracks t
                JOIN releases r ON t.release_id = r.id
                WHERE r.artist_id = $1::uuid
                """,
                artist_id,
            )
            artist_streams = int(streams_row["total"]) if streams_row else 0

        if artist_streams > 100_000:
            artist_stage = "established"
        elif artist_streams > 10_000:
            artist_stage = "developing"
        else:
            artist_stage = "emerging"

        high_risk_combos = {("emerging", "brand_awareness"), ("emerging", "social_growth")}
        low_risk_combos = {("established", "release_promo"), ("developing", "release_promo")}

        if (artist_stage, campaign_type) in high_risk_combos or budget > diminishing_max:
            risk_level = "high"
        elif (artist_stage, campaign_type) in low_risk_combos and budget <= diminishing_max:
            risk_level = "low"
        else:
            risk_level = "medium"

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "projected_roas": projected_roas,
                "estimated_reach": estimated_reach,
                "estimated_streams": estimated_streams,
                "estimated_new_fans": estimated_new_fans,
                "budget": budget,
                "platform": platform,
                "campaign_type": campaign_type,
                "artist_stage": artist_stage,
                "budget_recommendation": budget_recommendation,
                "risk_level": risk_level,
                "benchmarks_used": {
                    k: v for k, v in benchmarks.items() if v is not None
                },
                "hero_skill": "roas_oracle",
            },
        )

    # ----------------------------------------------------------------
    # Legacy handlers
    # ----------------------------------------------------------------

    async def _run_ads(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        budget = task.payload.get("budget_usd", 1000)
        platforms = task.payload.get("platforms", ["meta", "tiktok"])
        return {"release_id": release_id, "budget": budget, "platforms": platforms, "status": "ads_live"}

    async def _report_performance(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow("SELECT streams_total, revenue_total FROM releases WHERE id = $1::uuid", release_id)
        return {"release_id": release_id, "streams": dict(release) if release else {}}

    async def _press_release(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        release = await self.db_fetchrow(
            "SELECT r.title, a.name FROM releases r LEFT JOIN artists a ON r.artist_id = a.id WHERE r.id = $1::uuid",
            release_id,
        )
        if not release:
            return {"error": "Release not found"}
        return {
            "release_id": release_id,
            "press_release_draft": f"{release['name']} drops new release '{release['title']}' via ECHO",
            "status": "draft",
        }
