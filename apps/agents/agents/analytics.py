"""
ECHO Analytics Agent
Single source of truth for all label data. Track everything, analyze patterns, predict outcomes.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class AnalyticsAgent(BaseAgent):
    agent_id = "analytics"
    agent_name = "Analytics Agent"
    subscriptions = ["streams.update", "release.live", "points.sold", "agent.analytics"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        asyncio.create_task(self._anomaly_detection_loop())
        asyncio.create_task(self._daily_report_loop())
        logger.info("[Analytics] Online. Tracking all label data.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "label_overview": self._task_label_overview,
            "artist_dashboard": self._task_artist_dashboard,
            "release_performance": self._task_release_performance,
            "points_analytics": self._task_points_analytics,
            "agent_performance": self._task_agent_performance,
            "anomaly_scan": self._task_anomaly_scan,
            "generate_weekly_report": self._task_generate_weekly_report,
            "predict_release_performance": self._task_predict_release_performance,
            "melodio_score": self._task_melodio_score,
        }
        handler = handlers.get(task.task_type, self._task_default)
        return await handler(task)

    async def _task_default(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            success=False,
            task_id=task.task_id,
            agent_id=self.agent_id,
            error=f"Unknown task type: {task.task_type}",
        )

    async def _task_label_overview(self, task: AgentTask) -> AgentResult:
        stats = await self.db_fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM artists WHERE status = 'signed') as signed_artists,
                (SELECT COUNT(*) FROM artists WHERE status = 'prospect') as prospects,
                (SELECT COUNT(*) FROM releases WHERE status = 'released') as released_tracks,
                (SELECT COALESCE(SUM(streams_total), 0) FROM releases) as total_streams,
                (SELECT COALESCE(SUM(revenue_total), 0) FROM releases) as total_revenue,
                (SELECT COUNT(*) FROM echo_points WHERE status = 'active') as active_point_holders,
                (SELECT COALESCE(SUM(points_purchased), 0) FROM echo_points) as total_points_sold,
                (SELECT COALESCE(SUM(price_paid), 0) FROM echo_points) as total_points_revenue,
                (SELECT COUNT(*) FROM submissions WHERE DATE(created_at) = CURRENT_DATE) as demos_today,
                (SELECT COUNT(*) FROM hub_beats WHERE status = 'available') as beats_available
        """)

        if not stats:
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id=self.agent_id,
                error="Failed to fetch label stats",
            )

        signed = int(stats["signed_artists"] or 0)
        total_rev = float(stats["total_revenue"] or 0)

        result = {
            "signed_artists": signed,
            "prospects": int(stats["prospects"] or 0),
            "released_tracks": int(stats["released_tracks"] or 0),
            "total_streams": int(stats["total_streams"] or 0),
            "total_revenue": total_rev,
            "active_point_holders": int(stats["active_point_holders"] or 0),
            "total_points_sold": int(stats["total_points_sold"] or 0),
            "total_points_revenue": float(stats["total_points_revenue"] or 0),
            "demos_today": int(stats["demos_today"] or 0),
            "beats_available": int(stats["beats_available"] or 0),
            "avg_revenue_per_artist": round(total_rev / signed, 2) if signed > 0 else 0.0,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _task_artist_dashboard(self, task: AgentTask) -> AgentResult:
        artist_id = task.payload.get("artist_id") or task.artist_id
        if not artist_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="artist_id required")

        artist = await self.db_fetchrow(
            """SELECT id, name, stage_name, monthly_listeners, total_streams, echo_score, tier,
                      streams_total, revenue_total, advance_amount, recoupment_balance, status
               FROM artists WHERE id = $1::uuid""",
            artist_id,
        )
        if not artist:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Artist not found")

        releases = await self.db_fetch(
            """SELECT id, title, status, streams_total, revenue_total, release_date,
                      spotify_url, apple_url
               FROM releases WHERE artist_id = $1::uuid ORDER BY release_date DESC""",
            artist_id,
        )

        points_stats = await self.db_fetchrow(
            """SELECT COUNT(*) as holders, COALESCE(SUM(points_purchased), 0) as total_sold,
                      COALESCE(SUM(price_paid), 0) as total_revenue
               FROM echo_points WHERE artist_id = $1::uuid AND status = 'active'""",
            artist_id,
        )

        # Growth trend: this month vs last month streams
        now = datetime.now(timezone.utc)
        first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_last_month = (first_this_month - timedelta(days=1)).replace(day=1)

        trend = await self.db_fetchrow(
            """SELECT
                   COALESCE(SUM(CASE WHEN period_start >= $2 THEN net_amount ELSE 0 END), 0) as this_month,
                   COALESCE(SUM(CASE WHEN period_start >= $3 AND period_start < $2 THEN net_amount ELSE 0 END), 0) as last_month
               FROM royalties WHERE artist_id = $1::uuid""",
            artist_id,
            first_this_month,
            first_last_month,
        )

        this_month_rev = float(trend["this_month"] or 0) if trend else 0.0
        last_month_rev = float(trend["last_month"] or 0) if trend else 0.0
        growth_pct = 0.0
        if last_month_rev > 0:
            growth_pct = round(((this_month_rev - last_month_rev) / last_month_rev) * 100, 1)

        advance = float(artist["advance_amount"] or 0)
        recoup_balance = float(artist["recoupment_balance"] or 0)
        recoup_pct = 0.0
        if advance > 0:
            recoup_pct = round(max(0, (advance - recoup_balance) / advance * 100), 1)

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "artist_id": artist_id,
                "name": artist["stage_name"] or artist["name"],
                "status": artist["status"],
                "streams_total": int(artist["streams_total"] or 0),
                "revenue_total": float(artist["revenue_total"] or 0),
                "echo_score": float(artist["echo_score"] or 0),
                "tier": artist["tier"],
                "monthly_listeners": int(artist["monthly_listeners"] or 0),
                "releases": [dict(r) for r in releases],
                "points": {
                    "holders": int(points_stats["holders"] or 0) if points_stats else 0,
                    "total_sold": int(points_stats["total_sold"] or 0) if points_stats else 0,
                    "total_revenue": float(points_stats["total_revenue"] or 0) if points_stats else 0.0,
                },
                "recoupment": {
                    "advance": advance,
                    "balance_remaining": recoup_balance,
                    "percent_recouped": recoup_pct,
                    "fully_recouped": recoup_balance <= 0,
                },
                "growth_trend": {
                    "this_month_revenue": this_month_rev,
                    "last_month_revenue": last_month_rev,
                    "growth_percent": growth_pct,
                },
            },
        )

    async def _task_release_performance(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id") or task.release_id
        if not release_id:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="release_id required")

        release = await self.db_fetchrow(
            """SELECT id, title, artist_id, status, streams_total, revenue_total,
                      release_date, spotify_url, apple_url
               FROM releases WHERE id = $1::uuid""",
            release_id,
        )
        if not release:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id, error="Release not found")

        # Streams by day — last 30 days from royalties
        daily_streams = await self.db_fetch(
            """SELECT DATE(period_start) as day, COALESCE(SUM(net_amount), 0) as revenue,
                      COUNT(*) as royalty_records
               FROM royalties WHERE release_id = $1::uuid
                 AND period_start >= NOW() - INTERVAL '30 days'
               GROUP BY DATE(period_start) ORDER BY day""",
            release_id,
        )

        # Revenue breakdown by source
        revenue_by_source = await self.db_fetch(
            """SELECT source, platform, COALESCE(SUM(net_amount), 0) as revenue
               FROM royalties WHERE release_id = $1::uuid
               GROUP BY source, platform ORDER BY revenue DESC""",
            release_id,
        )

        # Point holders for this release
        point_holders = await self.db_fetchrow(
            """SELECT COUNT(*) as holders, COALESCE(SUM(points_purchased), 0) as total_points
               FROM echo_points WHERE release_id = $1::uuid AND status = 'active'""",
            release_id,
        )

        total_rev = float(release["revenue_total"] or 0)
        streams = int(release["streams_total"] or 0)

        # Simple projection comparison: expected = 1000 streams/day baseline
        days_live = 1
        if release["release_date"]:
            delta = datetime.now(timezone.utc).date() - release["release_date"]
            days_live = max(1, delta.days)
        projected_streams = days_live * 1000
        performance_vs_projection = round((streams / projected_streams * 100), 1) if projected_streams > 0 else 0.0

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "title": release["title"],
                "status": release["status"],
                "streams_total": streams,
                "revenue_total": total_rev,
                "days_live": days_live,
                "daily_breakdown": [dict(d) for d in daily_streams],
                "revenue_by_source": [dict(r) for r in revenue_by_source],
                "point_holders": {
                    "count": int(point_holders["holders"] or 0) if point_holders else 0,
                    "total_points": int(point_holders["total_points"] or 0) if point_holders else 0,
                },
                "performance_vs_projection_pct": performance_vs_projection,
                "playlist_adds": 0,  # placeholder until playlist tracking is live
            },
        )

    async def _task_points_analytics(self, task: AgentTask) -> AgentResult:
        # Overall totals
        totals = await self.db_fetchrow(
            """SELECT COUNT(*) as total_holders,
                      COALESCE(SUM(points_purchased), 0) as total_points,
                      COALESCE(SUM(price_paid), 0) as total_revenue
               FROM echo_points WHERE status = 'active'"""
        )

        # Top selling drops
        top_drops = await self.db_fetch(
            """SELECT ep.release_id, r.title, a.name as artist_name,
                      COUNT(ep.id) as holders,
                      COALESCE(SUM(ep.points_purchased), 0) as points_sold,
                      COALESCE(SUM(ep.price_paid), 0) as revenue
               FROM echo_points ep
               LEFT JOIN releases r ON ep.release_id = r.id
               LEFT JOIN artists a ON ep.artist_id = a.id
               WHERE ep.status = 'active'
               GROUP BY ep.release_id, r.title, a.name
               ORDER BY revenue DESC LIMIT 10"""
        )

        # Exchange volume — points used vs purchased
        exchange = await self.db_fetchrow(
            """SELECT COALESCE(SUM(points_purchased), 0) as purchased,
                      COALESCE(SUM(points_redeemed), 0) as redeemed
               FROM echo_points"""
        )

        # Holder demographics (basic — from users table)
        demographics = await self.db_fetch(
            """SELECT u.country, COUNT(DISTINCT ep.user_id) as holders
               FROM echo_points ep
               JOIN users u ON ep.user_id = u.id
               WHERE ep.status = 'active'
               GROUP BY u.country ORDER BY holders DESC LIMIT 10"""
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "total_holders": int(totals["total_holders"] or 0) if totals else 0,
                "total_points_sold": int(totals["total_points"] or 0) if totals else 0,
                "total_revenue": float(totals["total_revenue"] or 0) if totals else 0.0,
                "top_drops": [dict(d) for d in top_drops],
                "exchange": {
                    "purchased": int(exchange["purchased"] or 0) if exchange else 0,
                    "redeemed": int(exchange["redeemed"] or 0) if exchange else 0,
                },
                "demographics_by_country": [dict(d) for d in demographics],
            },
        )

    async def _task_agent_performance(self, task: AgentTask) -> AgentResult:
        # Task completion stats by agent
        stats = await self.db_fetch(
            """SELECT agent_id,
                      COUNT(*) as total_tasks,
                      COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                      COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                      AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000) as avg_duration_ms
               FROM agent_tasks
               WHERE created_at >= NOW() - INTERVAL '7 days'
               GROUP BY agent_id ORDER BY total_tasks DESC"""
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "period": "last_7_days",
                "agents": [dict(s) for s in stats],
            },
        )

    async def _task_anomaly_scan(self, task: AgentTask) -> AgentResult:
        anomalies = []

        # 1. Stream drops > 50% day-over-day
        stream_drops = await self.db_fetch(
            """SELECT release_id,
                      MAX(CASE WHEN day_rank = 1 THEN daily_rev END) as today,
                      MAX(CASE WHEN day_rank = 2 THEN daily_rev END) as yesterday
               FROM (
                   SELECT release_id,
                          DATE(period_start) as day,
                          SUM(net_amount) as daily_rev,
                          ROW_NUMBER() OVER (PARTITION BY release_id ORDER BY DATE(period_start) DESC) as day_rank
                   FROM royalties
                   WHERE period_start >= NOW() - INTERVAL '3 days'
                   GROUP BY release_id, DATE(period_start)
               ) sub
               WHERE day_rank <= 2
               GROUP BY release_id
               HAVING MAX(CASE WHEN day_rank = 2 THEN daily_rev END) > 0
                  AND MAX(CASE WHEN day_rank = 1 THEN daily_rev END) <
                      MAX(CASE WHEN day_rank = 2 THEN daily_rev END) * 0.5"""
        )
        for row in stream_drops:
            anomalies.append({
                "type": "stream_drop",
                "severity": "critical",
                "entity": "release",
                "entity_id": str(row["release_id"]),
                "message": f"Revenue dropped >50% day-over-day (possible takedown or content issue)",
                "today": float(row["today"] or 0),
                "yesterday": float(row["yesterday"] or 0),
            })

        # 2. Revenue discrepancy: releases with streams but no royalty records
        rev_mismatch = await self.db_fetch(
            """SELECT r.id, r.title, r.streams_total, r.revenue_total,
                      COALESCE(SUM(roy.net_amount), 0) as royalties_recorded
               FROM releases r
               LEFT JOIN royalties roy ON roy.release_id = r.id
               WHERE r.streams_total > 10000
               GROUP BY r.id, r.title, r.streams_total, r.revenue_total
               HAVING r.revenue_total > 0
                  AND ABS(r.revenue_total - COALESCE(SUM(roy.net_amount), 0)) / NULLIF(r.revenue_total, 0) > 0.1"""
        )
        for row in rev_mismatch:
            anomalies.append({
                "type": "revenue_discrepancy",
                "severity": "warning",
                "entity": "release",
                "entity_id": str(row["id"]),
                "message": f"Revenue discrepancy >10% on '{row['title']}' — flag for finance review",
                "reported": float(row["revenue_total"] or 0),
                "royalties_recorded": float(row["royalties_recorded"] or 0),
            })

        # 3. Agent error rate > 20% in last 24h
        agent_errors = await self.db_fetch(
            """SELECT agent_id,
                      COUNT(*) as total,
                      COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
               FROM agent_tasks
               WHERE created_at >= NOW() - INTERVAL '24 hours'
               GROUP BY agent_id
               HAVING COUNT(*) >= 5
                  AND COUNT(CASE WHEN status = 'failed' THEN 1 END)::float / COUNT(*) > 0.2"""
        )
        for row in agent_errors:
            anomalies.append({
                "type": "agent_error_rate",
                "severity": "warning",
                "entity": "agent",
                "entity_id": row["agent_id"],
                "message": f"Agent '{row['agent_id']}' has >20% error rate in last 24h",
                "total_tasks": int(row["total"]),
                "failed_tasks": int(row["failed"]),
            })

        # Broadcast critical anomalies to CEO
        critical = [a for a in anomalies if a["severity"] == "critical"]
        if critical:
            await self.broadcast("agent.ceo", {
                "topic": "anomalies_detected",
                "anomalies": critical,
                "count": len(critical),
            })

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "anomalies": anomalies,
                "total": len(anomalies),
                "critical": len([a for a in anomalies if a["severity"] == "critical"]),
                "warnings": len([a for a in anomalies if a["severity"] == "warning"]),
                "scanned_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _task_predict_release_performance(self, task: AgentTask) -> AgentResult:
        artist_id = task.payload.get("artist_id") or task.artist_id
        genre = task.payload.get("genre", "pop")

        # Genre baseline multipliers (streams per day week 1)
        genre_baselines = {
            "hip_hop": 3500, "pop": 2500, "r&b": 2000, "electronic": 1500,
            "rock": 1800, "country": 1200, "latin": 2800, "afrobeats": 2200,
        }
        baseline = genre_baselines.get(genre.lower(), 1500)

        artist_stats = None
        growth_multiplier = 1.0
        if artist_id:
            artist_stats = await self.db_fetchrow(
                """SELECT echo_score, tier, total_streams, monthly_listeners
                   FROM artists WHERE id = $1::uuid""",
                artist_id,
            )
            if artist_stats:
                echo_score = float(artist_stats["echo_score"] or 50)
                growth_multiplier = 0.5 + (echo_score / 100)

        # Projections
        week1_streams = int(baseline * growth_multiplier * 7)
        month1_streams = int(week1_streams * 3.2)   # decay curve
        month3_streams = int(month1_streams * 2.1)
        year1_streams = int(month3_streams * 3.5)

        rev_per_1k = 0.004  # $4 per 1000 streams
        confidence = min(95, int(50 + (growth_multiplier * 30)))

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "genre": genre,
                "projections": {
                    "week_1": {"streams": week1_streams, "revenue": round(week1_streams * rev_per_1k, 2)},
                    "month_1": {"streams": month1_streams, "revenue": round(month1_streams * rev_per_1k, 2)},
                    "month_3": {"streams": month3_streams, "revenue": round(month3_streams * rev_per_1k, 2)},
                    "year_1": {"streams": year1_streams, "revenue": round(year1_streams * rev_per_1k, 2)},
                },
                "confidence_score": confidence,
                "growth_multiplier": round(growth_multiplier, 2),
                "artist_tier": artist_stats["tier"] if artist_stats else "unknown",
            },
        )

    async def _task_generate_weekly_report(self, task: AgentTask) -> AgentResult:
        now = datetime.now(timezone.utc)
        week_num = now.isocalendar()[1]
        year = now.year
        week_label = f"{year}-W{week_num:02d}"

        # Overview
        overview_task = AgentTask(task_id=task.task_id + "_sub", task_type="label_overview", payload={})
        overview_result = await self._task_label_overview(overview_task)
        metrics = overview_result.result

        # Top performer this week
        top_performer = await self.db_fetchrow(
            """SELECT a.name, a.stage_name, r.title,
                      COALESCE(SUM(roy.net_amount), 0) as week_revenue
               FROM royalties roy
               JOIN artists a ON roy.artist_id = a.id
               LEFT JOIN releases r ON roy.release_id = r.id
               WHERE roy.period_start >= NOW() - INTERVAL '7 days'
               GROUP BY a.name, a.stage_name, r.title
               ORDER BY week_revenue DESC LIMIT 1"""
        )

        # Anomaly scan
        anomaly_task = AgentTask(task_id=task.task_id + "_anom", task_type="anomaly_scan", payload={})
        anomaly_result = await self._task_anomaly_scan(anomaly_task)
        anomalies = anomaly_result.result.get("anomalies", [])

        # Highlights
        highlights = []
        streams = metrics.get("total_streams", 0)
        if streams > 0:
            highlights.append(f"Label total: {streams:,} streams")
        demos = metrics.get("demos_today", 0)
        if demos > 0:
            highlights.append(f"{demos} demo submissions today")
        points_rev = metrics.get("total_points_revenue", 0)
        if points_rev > 0:
            highlights.append(f"${points_rev:,.2f} total ECHO Points revenue")

        # Recommendations
        recommendations = []
        if anomaly_result.result.get("critical", 0) > 0:
            recommendations.append("Review critical anomalies flagged this week")
        if metrics.get("prospects", 0) > 5:
            recommendations.append("AR pipeline has 5+ prospects — schedule showcase reviews")
        if metrics.get("beats_available", 0) < 10:
            recommendations.append("Hub beat catalog running low — activate new producer outreach")

        report = {
            "week": week_label,
            "generated_at": now.isoformat(),
            "highlights": highlights,
            "metrics": metrics,
            "top_performer": dict(top_performer) if top_performer else None,
            "alerts": [a for a in anomalies if a["severity"] in ("critical", "warning")],
            "recommendations": recommendations,
        }

        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=report)

    # ----------------------------------------------------------------
    # Hero Skills
    # ----------------------------------------------------------------

    async def _task_melodio_score(self, task: AgentTask) -> AgentResult:
        """Melodio Score™ — composite 0-100 artist health score across 6 dimensions."""
        artist_id = task.payload.get("artist_id")
        if not artist_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id, error="artist_id required"
            )

        artist = await self.db_fetchrow("SELECT * FROM artists WHERE id = $1::uuid", artist_id)
        if not artist:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id, error="Artist not found"
            )

        # 1. release_activity (20pts)
        releases = await self.db_fetch(
            "SELECT release_date, streams_total, spotify_url, apple_url FROM releases WHERE artist_id = $1::uuid",
            artist_id,
        )
        release_count = len(releases)
        now = datetime.now(timezone.utc)
        recent_releases = sum(
            1 for r in releases
            if r.get("release_date") and (now.date() - r["release_date"]).days <= 365
        )
        release_pts = min(20, int((min(release_count, 5) / 5) * 10 + (min(recent_releases, 3) / 3) * 10))

        # 2. streaming_performance (20pts)
        total_streams = int(artist.get("total_streams") or 0) or sum(
            int(r.get("streams_total") or 0) for r in releases
        )
        if total_streams >= 1_000_000:
            stream_pts = 20
        elif total_streams >= 100_000:
            stream_pts = 14
        elif total_streams >= 10_000:
            stream_pts = 8
        elif total_streams >= 1_000:
            stream_pts = 4
        else:
            stream_pts = 1

        # 3. fan_engagement (20pts)
        fan_data = await self.db_fetchrow(
            "SELECT COUNT(*) as holders, COALESCE(SUM(points_purchased), 0) as total_pts "
            "FROM echo_points WHERE artist_id = $1::uuid AND status = 'active'",
            artist_id,
        )
        holders = int(fan_data["holders"] or 0) if fan_data else 0
        if holders >= 100:
            engagement_pts = 20
        elif holders >= 20:
            engagement_pts = 14
        elif holders >= 5:
            engagement_pts = 8
        elif holders >= 1:
            engagement_pts = 4
        else:
            engagement_pts = 0

        # 4. revenue_health (15pts)
        royalty_data = await self.db_fetchrow(
            "SELECT COALESCE(SUM(net_amount), 0) as total_royalties "
            "FROM royalties WHERE artist_id = $1::uuid",
            artist_id,
        )
        total_royalties = float(royalty_data["total_royalties"] or 0) if royalty_data else 0.0
        if total_royalties >= 10_000:
            revenue_pts = 15
        elif total_royalties >= 1_000:
            revenue_pts = 10
        elif total_royalties >= 100:
            revenue_pts = 6
        elif total_royalties > 0:
            revenue_pts = 3
        else:
            revenue_pts = 0

        # 5. platform_presence (15pts)
        dsps = set()
        for r in releases:
            if r.get("spotify_url"):
                dsps.add("spotify")
            if r.get("apple_url"):
                dsps.add("apple")
        platform_pts = min(15, len(dsps) * 5 + (3 if release_count > 0 else 0))

        # 6. momentum (10pts): recent 30d vs prior 30d royalties
        trend = await self.db_fetchrow(
            "SELECT "
            "COALESCE(SUM(CASE WHEN period_start >= NOW() - INTERVAL '30 days' THEN net_amount ELSE 0 END), 0) as recent, "
            "COALESCE(SUM(CASE WHEN period_start >= NOW() - INTERVAL '60 days' AND period_start < NOW() - INTERVAL '30 days' THEN net_amount ELSE 0 END), 0) as prior "
            "FROM royalties WHERE artist_id = $1::uuid",
            artist_id,
        )
        recent_rev = float(trend["recent"] or 0) if trend else 0.0
        prior_rev = float(trend["prior"] or 0) if trend else 0.0
        if prior_rev > 0 and recent_rev > prior_rev * 1.1:
            momentum_pts = 10
        elif prior_rev > 0 and recent_rev >= prior_rev * 0.9:
            momentum_pts = 7
        elif recent_rev > 0:
            momentum_pts = 5
        else:
            momentum_pts = 2

        melodio_score = release_pts + stream_pts + engagement_pts + revenue_pts + platform_pts + momentum_pts

        if melodio_score >= 90:
            grade = "S"
        elif melodio_score >= 80:
            grade = "A"
        elif melodio_score >= 70:
            grade = "B"
        elif melodio_score >= 60:
            grade = "C"
        else:
            grade = "D"

        scores_map = {
            "release_activity": release_pts,
            "streaming_performance": stream_pts,
            "fan_engagement": engagement_pts,
            "revenue_health": revenue_pts,
            "platform_presence": platform_pts,
            "momentum": momentum_pts,
        }
        maxes = {
            "release_activity": 20, "streaming_performance": 20, "fan_engagement": 20,
            "revenue_health": 15, "platform_presence": 15, "momentum": 10,
        }
        biggest_gap = max(scores_map, key=lambda k: maxes[k] - scores_map[k])
        insight_map = {
            "release_activity": "Releasing more consistently would unlock major score gains.",
            "streaming_performance": "Growing stream counts is the fastest path to a higher score.",
            "fan_engagement": "Fan point sales are the biggest lever for score improvement.",
            "revenue_health": "Royalty collection is the key constraint holding this score down.",
            "platform_presence": "Distributing to more DSPs would meaningfully lift this score.",
            "momentum": "Recent revenue trend is flat — a new drop could unlock 10+ score points.",
        }
        insight = insight_map.get(biggest_gap, "Score is balanced across all dimensions.")

        try:
            await self.db_execute("ALTER TABLE artists ADD COLUMN IF NOT EXISTS melodio_score INTEGER")
            await self.db_execute(
                "UPDATE artists SET melodio_score = $1 WHERE id = $2::uuid",
                melodio_score,
                artist_id,
            )
        except Exception as e:
            logger.warning(f"[Analytics] Could not store melodio_score: {e}")

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "melodio_score": melodio_score,
                "grade": grade,
                "dimensions": {
                    "release_activity": {"score": release_pts, "max": 20},
                    "streaming_performance": {"score": stream_pts, "max": 20},
                    "fan_engagement": {"score": engagement_pts, "max": 20},
                    "revenue_health": {"score": revenue_pts, "max": 15},
                    "platform_presence": {"score": platform_pts, "max": 15},
                    "momentum": {"score": momentum_pts, "max": 10},
                },
                "insight": insight,
                "hero_skill": "melodio_score",
            },
        )

    # ----------------------------------------------------------------
    # Background loops
    # ----------------------------------------------------------------

    async def _anomaly_detection_loop(self):
        """Runs every hour — scans for anomalies, broadcasts critical ones to CEO."""
        while self._running:
            try:
                await asyncio.sleep(3600)
                if not self._running:
                    break
                dummy_task = AgentTask(
                    task_id=f"anomaly_auto_{int(datetime.now(timezone.utc).timestamp())}",
                    task_type="anomaly_scan",
                    payload={},
                )
                result = await self._task_anomaly_scan(dummy_task)
                critical_count = result.result.get("critical", 0)
                if critical_count > 0:
                    logger.warning(f"[Analytics] {critical_count} critical anomaly(ies) detected — broadcasted to CEO")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Analytics] Anomaly loop error: {e}")

    async def _daily_report_loop(self):
        """Runs at 6AM UTC — generates daily report, sends to CEO."""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                next_6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
                if now >= next_6am:
                    next_6am += timedelta(days=1)
                wait_secs = (next_6am - now).total_seconds()
                await asyncio.sleep(wait_secs)
                if not self._running:
                    break

                report_task = AgentTask(
                    task_id=f"daily_report_{int(datetime.now(timezone.utc).timestamp())}",
                    task_type="generate_weekly_report",
                    payload={},
                )
                result = await self._task_generate_weekly_report(report_task)
                await self.broadcast("agent.ceo", {
                    "topic": "daily_report",
                    "report": result.result,
                })
                logger.info("[Analytics] Daily report sent to CEO")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Analytics] Daily report loop error: {e}")
                await asyncio.sleep(60)
