from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timezone, timedelta

from database import get_db
from routers.auth import get_current_user, TokenData

router = APIRouter()


# ----------------------------------------------------------------
# Label Overview
# ----------------------------------------------------------------

@router.get("/overview")
async def get_label_overview(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Full label overview — signed artists, streams, revenue, points, demos."""
    try:
        result = await db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM artists WHERE status = 'signed') as signed_artists,
                (SELECT COUNT(*) FROM artists WHERE status = 'prospect') as prospects,
                (SELECT COUNT(*) FROM releases WHERE status = 'released') as released_tracks,
                (SELECT COUNT(*) FROM releases) as total_releases,
                (SELECT COALESCE(SUM(streams_total), 0) FROM releases) as total_streams,
                (SELECT COALESCE(SUM(revenue_total), 0) FROM releases) as total_revenue,
                (SELECT COUNT(*) FROM echo_points WHERE status = 'active') as active_point_holders,
                (SELECT COALESCE(SUM(points_purchased), 0) FROM echo_points) as total_points_sold,
                (SELECT COALESCE(SUM(price_paid), 0) FROM echo_points) as total_points_revenue,
                (SELECT COUNT(*) FROM submissions WHERE DATE(created_at) = CURRENT_DATE) as demos_today,
                (SELECT COUNT(*) FROM submissions WHERE status = 'pending') as demos_pending,
                (SELECT COUNT(*) FROM hub_beats WHERE status = 'available') as beats_available
        """))
        row = result.mappings().fetchone()
        stats = dict(row) if row else {}

        signed = int(stats.get("signed_artists") or 0)
        total_rev = float(stats.get("total_revenue") or 0)

        return {
            "signed_artists": signed,
            "prospects": int(stats.get("prospects") or 0),
            "released_tracks": int(stats.get("released_tracks") or 0),
            "total_releases": int(stats.get("total_releases") or 0),
            "total_streams": int(stats.get("total_streams") or 0),
            "total_revenue": total_rev,
            "active_point_holders": int(stats.get("active_point_holders") or 0),
            "total_points_sold": int(stats.get("total_points_sold") or 0),
            "total_points_revenue": float(stats.get("total_points_revenue") or 0),
            "demos_today": int(stats.get("demos_today") or 0),
            "demos_pending": int(stats.get("demos_pending") or 0),
            "beats_available": int(stats.get("beats_available") or 0),
            "avg_revenue_per_artist": round(total_rev / signed, 2) if signed > 0 else 0.0,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        return {
            "signed_artists": 0, "prospects": 0, "released_tracks": 0,
            "total_releases": 0, "total_streams": 0, "total_revenue": 0.0,
            "active_point_holders": 0, "total_points_sold": 0, "total_points_revenue": 0.0,
            "demos_today": 0, "demos_pending": 0, "beats_available": 0,
            "avg_revenue_per_artist": 0.0,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


# ----------------------------------------------------------------
# Per-Artist Dashboard
# ----------------------------------------------------------------

@router.get("/artists/{artist_id}")
async def get_artist_dashboard(
    artist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Per-artist analytics dashboard — streams, revenue, growth, points, recoupment."""
    artist_result = await db.execute(
        text("""SELECT id, name, stage_name, monthly_listeners, total_streams, echo_score, tier,
                       streams_total, revenue_total, advance_amount, recoupment_balance, status
                FROM artists WHERE id = :id"""),
        {"id": artist_id},
    )
    artist = artist_result.mappings().fetchone()
    if not artist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")

    releases_result = await db.execute(
        text("""SELECT id, title, status, streams_total, revenue_total, release_date,
                       spotify_url, apple_url
                FROM releases WHERE artist_id = :id ORDER BY release_date DESC"""),
        {"id": artist_id},
    )
    releases = [dict(r) for r in releases_result.mappings().all()]

    points_result = await db.execute(
        text("""SELECT COUNT(*) as holders,
                       COALESCE(SUM(points_purchased), 0) as total_sold,
                       COALESCE(SUM(price_paid), 0) as total_revenue
                FROM echo_points WHERE artist_id = :id AND status = 'active'"""),
        {"id": artist_id},
    )
    points_row = points_result.mappings().fetchone()
    points = dict(points_row) if points_row else {"holders": 0, "total_sold": 0, "total_revenue": 0}

    # Growth trend
    now = datetime.now(timezone.utc)
    first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_last_month = (first_this_month - timedelta(days=1)).replace(day=1)

    trend_result = await db.execute(
        text("""SELECT
                   COALESCE(SUM(CASE WHEN period_start >= :first_this THEN net_amount ELSE 0 END), 0) as this_month,
                   COALESCE(SUM(CASE WHEN period_start >= :first_last AND period_start < :first_this THEN net_amount ELSE 0 END), 0) as last_month
               FROM royalties WHERE artist_id = :id"""),
        {"id": artist_id, "first_this": first_this_month, "first_last": first_last_month},
    )
    trend_row = trend_result.mappings().fetchone()
    trend = dict(trend_row) if trend_row else {"this_month": 0, "last_month": 0}

    this_month = float(trend.get("this_month") or 0)
    last_month = float(trend.get("last_month") or 0)
    growth_pct = 0.0
    if last_month > 0:
        growth_pct = round(((this_month - last_month) / last_month) * 100, 1)

    advance = float(artist.get("advance_amount") or 0)
    recoup_balance = float(artist.get("recoupment_balance") or 0)
    recoup_pct = 0.0
    if advance > 0:
        recoup_pct = round(max(0, (advance - recoup_balance) / advance * 100), 1)

    return {
        "artist_id": artist_id,
        "name": artist["stage_name"] or artist["name"],
        "status": artist["status"],
        "streams_total": int(artist.get("streams_total") or 0),
        "revenue_total": float(artist.get("revenue_total") or 0),
        "echo_score": float(artist.get("echo_score") or 0),
        "tier": artist["tier"],
        "monthly_listeners": int(artist.get("monthly_listeners") or 0),
        "releases": releases,
        "points": {
            "holders": int(points.get("holders") or 0),
            "total_sold": int(points.get("total_sold") or 0),
            "total_revenue": float(points.get("total_revenue") or 0),
        },
        "recoupment": {
            "advance": advance,
            "balance_remaining": recoup_balance,
            "percent_recouped": recoup_pct,
            "fully_recouped": recoup_balance <= 0,
        },
        "growth_trend": {
            "this_month_revenue": this_month,
            "last_month_revenue": last_month,
            "growth_percent": growth_pct,
        },
    }


# ----------------------------------------------------------------
# Release Performance
# ----------------------------------------------------------------

@router.get("/releases/{release_id}")
async def get_release_performance(
    release_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Release performance — daily breakdown, revenue by source, point holders."""
    release_result = await db.execute(
        text("""SELECT id, title, artist_id, status, streams_total, revenue_total,
                       release_date, spotify_url, apple_url
                FROM releases WHERE id = :id"""),
        {"id": release_id},
    )
    release = release_result.mappings().fetchone()
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    daily_result = await db.execute(
        text("""SELECT DATE(period_start) as day,
                       COALESCE(SUM(net_amount), 0) as revenue,
                       COUNT(*) as royalty_records
                FROM royalties WHERE release_id = :id
                  AND period_start >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(period_start) ORDER BY day"""),
        {"id": release_id},
    )
    daily = [dict(r) for r in daily_result.mappings().all()]

    source_result = await db.execute(
        text("""SELECT source, platform, COALESCE(SUM(net_amount), 0) as revenue
                FROM royalties WHERE release_id = :id
                GROUP BY source, platform ORDER BY revenue DESC"""),
        {"id": release_id},
    )
    revenue_by_source = [dict(r) for r in source_result.mappings().all()]

    points_result = await db.execute(
        text("""SELECT COUNT(*) as holders, COALESCE(SUM(points_purchased), 0) as total_points
                FROM echo_points WHERE release_id = :id AND status = 'active'"""),
        {"id": release_id},
    )
    rel_points_row = points_result.mappings().fetchone()
    points = dict(rel_points_row) if rel_points_row else {"holders": 0, "total_points": 0}

    total_streams = int(release.get("streams_total") or 0)
    days_live = 1
    if release["release_date"]:
        delta = datetime.now(timezone.utc).date() - release["release_date"]
        days_live = max(1, delta.days)
    projected_streams = days_live * 1000
    perf_vs_proj = round((total_streams / projected_streams * 100), 1) if projected_streams > 0 else 0.0

    return {
        "release_id": release_id,
        "title": release["title"],
        "status": release["status"],
        "streams_total": total_streams,
        "revenue_total": float(release.get("revenue_total") or 0),
        "days_live": days_live,
        "daily_breakdown": daily,
        "revenue_by_source": revenue_by_source,
        "point_holders": {
            "count": int(points.get("holders") or 0),
            "total_points": int(points.get("total_points") or 0),
        },
        "performance_vs_projection_pct": perf_vs_proj,
        "playlist_adds": 0,
    }


# ----------------------------------------------------------------
# Points Analytics
# ----------------------------------------------------------------

@router.get("/points")
async def get_points_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """ECHO Points analytics — totals, top drops, exchange volume, demographics."""
    totals_result = await db.execute(text("""
        SELECT COUNT(*) as total_holders,
               COALESCE(SUM(points_purchased), 0) as total_points,
               COALESCE(SUM(price_paid), 0) as total_revenue
        FROM echo_points WHERE status = 'active'
    """))
    totals_row = totals_result.mappings().fetchone()
    totals = dict(totals_row) if totals_row else {"total_holders": 0, "total_points": 0, "total_revenue": 0}

    drops_result = await db.execute(text("""
        SELECT ep.release_id, r.title, a.name as artist_name,
               COUNT(ep.id) as holders,
               COALESCE(SUM(ep.points_purchased), 0) as points_sold,
               COALESCE(SUM(ep.price_paid), 0) as revenue
        FROM echo_points ep
        LEFT JOIN releases r ON ep.release_id = r.id
        LEFT JOIN artists a ON ep.artist_id = a.id
        WHERE ep.status = 'active'
        GROUP BY ep.release_id, r.title, a.name
        ORDER BY revenue DESC LIMIT 10
    """))
    top_drops = [dict(r) for r in drops_result.mappings().all()]

    exchange_result = await db.execute(text("""
        SELECT COALESCE(SUM(points_purchased), 0) as purchased,
               COALESCE(SUM(points_redeemed), 0) as redeemed
        FROM echo_points
    """))
    exchange_row = exchange_result.mappings().fetchone()
    exchange = dict(exchange_row) if exchange_row else {"purchased": 0, "redeemed": 0}

    demo_result = await db.execute(text("""
        SELECT u.country, COUNT(DISTINCT ep.user_id) as holders
        FROM echo_points ep
        JOIN users u ON ep.user_id = u.id
        WHERE ep.status = 'active'
        GROUP BY u.country ORDER BY holders DESC LIMIT 10
    """))
    demographics = [dict(r) for r in demo_result.mappings().all()]

    return {
        "total_holders": int(totals.get("total_holders") or 0),
        "total_points_sold": int(totals.get("total_points") or 0),
        "total_revenue": float(totals.get("total_revenue") or 0),
        "top_drops": top_drops,
        "exchange": {
            "purchased": int(exchange.get("purchased") or 0),
            "redeemed": int(exchange.get("redeemed") or 0),
        },
        "demographics_by_country": demographics,
    }


# ----------------------------------------------------------------
# Agent Performance
# ----------------------------------------------------------------

@router.get("/agents")
async def get_agent_performance(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Agent performance metrics — task counts, completion rates, avg duration."""
    result = await db.execute(
        text(f"""
            SELECT assigned_to as agent_id,
                   COUNT(*) as total_tasks,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                   COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                   COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
                   ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000)::numeric, 0) as avg_duration_ms
            FROM agent_tasks
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            GROUP BY assigned_to ORDER BY total_tasks DESC
        """)
    )
    agents = [dict(r) for r in result.mappings().all()]

    return {
        "period_days": days,
        "agents": agents,
        "total_agents_active": len(agents),
    }


# ----------------------------------------------------------------
# Weekly Report
# ----------------------------------------------------------------

@router.get("/weekly-report")
async def get_weekly_report(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Latest weekly report — highlights, metrics, top performer, alerts, recommendations."""
    now = datetime.now(timezone.utc)
    week_num = now.isocalendar()[1]
    week_label = f"{now.year}-W{week_num:02d}"

    # Overview
    overview_result = await db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM artists WHERE status = 'signed') as signed_artists,
            (SELECT COUNT(*) FROM releases WHERE status = 'released') as released_tracks,
            (SELECT COALESCE(SUM(streams_total), 0) FROM releases) as total_streams,
            (SELECT COALESCE(SUM(revenue_total), 0) FROM releases) as total_revenue,
            (SELECT COUNT(*) FROM echo_points WHERE status = 'active') as active_point_holders,
            (SELECT COALESCE(SUM(price_paid), 0) FROM echo_points WHERE status = 'active') as total_points_revenue,
            (SELECT COUNT(*) FROM submissions WHERE DATE(created_at) = CURRENT_DATE) as demos_today,
            (SELECT COUNT(*) FROM hub_beats WHERE status = 'available') as beats_available
    """))
    metrics_row = overview_result.mappings().fetchone()
    metrics = dict(metrics_row) if metrics_row else {}

    # Top performer this week
    top_result = await db.execute(text("""
        SELECT a.name, a.stage_name, r.title,
               COALESCE(SUM(roy.net_amount), 0) as week_revenue
        FROM royalties roy
        JOIN artists a ON roy.artist_id = a.id
        LEFT JOIN releases r ON roy.release_id = r.id
        WHERE roy.period_start >= NOW() - INTERVAL '7 days'
        GROUP BY a.name, a.stage_name, r.title
        ORDER BY week_revenue DESC LIMIT 1
    """))
    top_row = top_result.mappings().fetchone()
    top_performer = dict(top_row) if top_row else None

    # Agent error counts for alerts
    error_result = await db.execute(text("""
        SELECT assigned_to, COUNT(*) as failed
        FROM agent_tasks
        WHERE status = 'failed' AND created_at >= NOW() - INTERVAL '7 days'
        GROUP BY assigned_to
        HAVING COUNT(*) >= 3
    """))
    agent_errors = [dict(r) for r in error_result.mappings().all()]

    alerts = [
        {"type": "agent_errors", "agent": r["assigned_to"], "failed_count": int(r["failed"])}
        for r in agent_errors
    ]

    # Highlights
    highlights = []
    total_streams = int(metrics.get("total_streams") or 0)
    if total_streams > 0:
        highlights.append(f"Label total: {total_streams:,} streams")
    demos = int(metrics.get("demos_today") or 0)
    if demos > 0:
        highlights.append(f"{demos} demo submission(s) today")
    points_rev = float(metrics.get("total_points_revenue") or 0)
    if points_rev > 0:
        highlights.append(f"${points_rev:,.2f} total ECHO Points revenue")

    # Recommendations
    recommendations = []
    if len(alerts) > 0:
        recommendations.append("Review agent error rates — some agents have elevated failures this week")
    prospects = await db.execute(text("SELECT COUNT(*) as cnt FROM artists WHERE status = 'prospect'"))
    prospect_count = int((prospects.mappings().fetchone() or {}).get("cnt") or 0)
    if prospect_count > 5:
        recommendations.append(f"{prospect_count} prospects in AR pipeline — schedule showcase reviews")
    if int(metrics.get("beats_available") or 0) < 10:
        recommendations.append("Hub beat catalog running low — activate producer outreach")

    return {
        "week": week_label,
        "generated_at": now.isoformat(),
        "highlights": highlights,
        "metrics": {k: (float(v) if hasattr(v, "__float__") else v) for k, v in metrics.items()},
        "top_performer": top_performer,
        "alerts": alerts,
        "recommendations": recommendations,
    }


# ----------------------------------------------------------------
# Anomaly Scan
# ----------------------------------------------------------------

@router.post("/anomaly-scan")
async def trigger_anomaly_scan(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Trigger anomaly scan — stream drops, revenue discrepancies, agent error rates."""
    anomalies = []

    # 1. Stream drops > 50% day-over-day (revenue proxy)
    drops_result = await db.execute(text("""
        SELECT release_id,
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
               MAX(CASE WHEN day_rank = 2 THEN daily_rev END) * 0.5
    """))
    for row in drops_result.mappings().all():
        anomalies.append({
            "type": "stream_drop",
            "severity": "critical",
            "entity": "release",
            "entity_id": str(row["release_id"]),
            "message": "Revenue dropped >50% day-over-day — possible takedown or content issue",
            "today": float(row["today"] or 0),
            "yesterday": float(row["yesterday"] or 0),
        })

    # 2. Revenue discrepancy > 10%
    mismatch_result = await db.execute(text("""
        SELECT r.id, r.title, r.revenue_total,
               COALESCE(SUM(roy.net_amount), 0) as royalties_recorded
        FROM releases r
        LEFT JOIN royalties roy ON roy.release_id = r.id
        WHERE r.streams_total > 10000
        GROUP BY r.id, r.title, r.revenue_total
        HAVING r.revenue_total > 0
           AND ABS(r.revenue_total - COALESCE(SUM(roy.net_amount), 0)) / NULLIF(r.revenue_total, 0) > 0.1
    """))
    for row in mismatch_result.mappings().all():
        anomalies.append({
            "type": "revenue_discrepancy",
            "severity": "warning",
            "entity": "release",
            "entity_id": str(row["id"]),
            "message": f"Revenue discrepancy >10% on '{row['title']}' — flag for finance review",
            "reported": float(row["revenue_total"] or 0),
            "royalties_recorded": float(row["royalties_recorded"] or 0),
        })

    # 3. Agent error rate > 20% last 24h
    agent_result = await db.execute(text("""
        SELECT assigned_to as agent_id,
               COUNT(*) as total,
               COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
        FROM agent_tasks
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY assigned_to
        HAVING COUNT(*) >= 5
           AND COUNT(CASE WHEN status = 'failed' THEN 1 END)::float / COUNT(*) > 0.2
    """))
    for row in agent_result.mappings().all():
        anomalies.append({
            "type": "agent_error_rate",
            "severity": "warning",
            "entity": "agent",
            "entity_id": row["agent_id"],
            "message": f"Agent '{row['agent_id']}' has >20% error rate in last 24h",
            "total_tasks": int(row["total"]),
            "failed_tasks": int(row["failed"]),
        })

    return {
        "anomalies": anomalies,
        "total": len(anomalies),
        "critical": len([a for a in anomalies if a["severity"] == "critical"]),
        "warnings": len([a for a in anomalies if a["severity"] == "warning"]),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
