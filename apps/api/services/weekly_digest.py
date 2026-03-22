import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.email import send_email

logger = logging.getLogger(__name__)


async def generate_weekly_digest(db: AsyncSession) -> dict:
    """Generate weekly CEO digest with platform metrics and formatted HTML."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Total artists
    row = await db.execute(text("SELECT COUNT(*) FROM artists"))
    total_artists = row.scalar() or 0

    # New signups this week
    row = await db.execute(
        text("SELECT COUNT(*) FROM users WHERE created_at >= :since"),
        {"since": week_ago},
    )
    new_signups = row.scalar() or 0

    # Releases this week
    row = await db.execute(
        text("SELECT COUNT(*) FROM releases WHERE created_at >= :since"),
        {"since": week_ago},
    )
    releases_this_week = row.scalar() or 0

    # Total releases
    row = await db.execute(text("SELECT COUNT(*) FROM releases"))
    total_releases = row.scalar() or 0

    # Revenue (total royalties)
    row = await db.execute(
        text("SELECT COALESCE(SUM(amount), 0) FROM royalties")
    )
    total_revenue = float(row.scalar() or 0)

    # Revenue this week
    row = await db.execute(
        text("SELECT COALESCE(SUM(amount), 0) FROM royalties WHERE created_at >= :since"),
        {"since": week_ago},
    )
    revenue_this_week = float(row.scalar() or 0)

    # Agent tasks completed this week
    row = await db.execute(
        text(
            "SELECT COUNT(*) FROM agent_tasks WHERE status = 'completed' AND updated_at >= :since"
        ),
        {"since": week_ago},
    )
    tasks_completed = row.scalar() or 0

    # Total agent tasks
    row = await db.execute(text("SELECT COUNT(*) FROM agent_tasks"))
    total_tasks = row.scalar() or 0

    # Top agent this week (most tasks completed)
    row = await db.execute(
        text(
            """SELECT agent_type, COUNT(*) as cnt
               FROM agent_tasks
               WHERE status = 'completed' AND updated_at >= :since
               GROUP BY agent_type
               ORDER BY cnt DESC
               LIMIT 1"""
        ),
        {"since": week_ago},
    )
    top_agent_row = row.fetchone()
    top_agent = (
        {"name": top_agent_row[0], "tasks": top_agent_row[1]}
        if top_agent_row
        else {"name": "N/A", "tasks": 0}
    )

    # Top artist (most streams or latest signed)
    row = await db.execute(
        text(
            """SELECT name, COALESCE(monthly_listeners, 0) as listeners
               FROM artists
               ORDER BY monthly_listeners DESC NULLS LAST
               LIMIT 1"""
        )
    )
    top_artist_row = row.fetchone()
    top_artist = (
        {"name": top_artist_row[0], "listeners": top_artist_row[1]}
        if top_artist_row
        else {"name": "N/A", "listeners": 0}
    )

    # Submissions this week
    row = await db.execute(
        text("SELECT COUNT(*) FROM submissions WHERE created_at >= :since"),
        {"since": week_ago},
    )
    submissions_this_week = row.scalar() or 0

    metrics = {
        "generated_at": now.isoformat(),
        "period": f"{week_ago.strftime('%b %d')} — {now.strftime('%b %d, %Y')}",
        "total_artists": total_artists,
        "new_signups": new_signups,
        "releases_this_week": releases_this_week,
        "total_releases": total_releases,
        "total_revenue": total_revenue,
        "revenue_this_week": revenue_this_week,
        "tasks_completed": tasks_completed,
        "total_tasks": total_tasks,
        "top_agent": top_agent,
        "top_artist": top_artist,
        "submissions_this_week": submissions_this_week,
    }

    metrics["html"] = _render_html(metrics)
    return metrics


def _render_html(m: dict) -> str:
    """Render the weekly digest as an HTML email."""
    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#13131a;border-radius:12px;padding:48px 40px;">
        <!-- Header -->
        <tr><td align="center" style="padding-bottom:8px;">
          <span style="font-size:28px;font-weight:700;color:#8b5cf6;letter-spacing:-0.5px;">melodio</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <h1 style="margin:0;font-size:22px;color:#f9fafb;">Weekly CEO Digest</h1>
          <p style="margin:4px 0 0;font-size:14px;color:#6b7280;">{m["period"]}</p>
        </td></tr>

        <!-- Key Metrics -->
        <tr><td>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td width="50%" style="padding:12px;">
                <div style="background:#0a0a0f;border:1px solid #2a2a3a;border-radius:10px;padding:20px;text-align:center;">
                  <div style="font-size:28px;font-weight:800;color:#8b5cf6;">{m["total_artists"]}</div>
                  <div style="font-size:12px;color:#9ca3af;margin-top:4px;">Total Artists</div>
                </div>
              </td>
              <td width="50%" style="padding:12px;">
                <div style="background:#0a0a0f;border:1px solid #2a2a3a;border-radius:10px;padding:20px;text-align:center;">
                  <div style="font-size:28px;font-weight:800;color:#10b981;">+{m["new_signups"]}</div>
                  <div style="font-size:12px;color:#9ca3af;margin-top:4px;">New Signups This Week</div>
                </div>
              </td>
            </tr>
            <tr>
              <td width="50%" style="padding:12px;">
                <div style="background:#0a0a0f;border:1px solid #2a2a3a;border-radius:10px;padding:20px;text-align:center;">
                  <div style="font-size:28px;font-weight:800;color:#f59e0b;">{m["releases_this_week"]}</div>
                  <div style="font-size:12px;color:#9ca3af;margin-top:4px;">Releases This Week</div>
                </div>
              </td>
              <td width="50%" style="padding:12px;">
                <div style="background:#0a0a0f;border:1px solid #2a2a3a;border-radius:10px;padding:20px;text-align:center;">
                  <div style="font-size:28px;font-weight:800;color:#3b82f6;">${m["revenue_this_week"]:,.2f}</div>
                  <div style="font-size:12px;color:#9ca3af;margin-top:4px;">Revenue This Week</div>
                </div>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- Details -->
        <tr><td style="padding:24px 12px 0;">
          <h2 style="margin:0 0 16px;font-size:16px;color:#f9fafb;">Platform Summary</h2>
          <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;">
            <tr style="border-bottom:1px solid #2a2a3a;">
              <td style="padding:10px 0;color:#9ca3af;">Total Revenue</td>
              <td style="padding:10px 0;color:#f9fafb;text-align:right;font-weight:600;">${m["total_revenue"]:,.2f}</td>
            </tr>
            <tr style="border-bottom:1px solid #2a2a3a;">
              <td style="padding:10px 0;color:#9ca3af;">Total Releases</td>
              <td style="padding:10px 0;color:#f9fafb;text-align:right;font-weight:600;">{m["total_releases"]}</td>
            </tr>
            <tr style="border-bottom:1px solid #2a2a3a;">
              <td style="padding:10px 0;color:#9ca3af;">Submissions This Week</td>
              <td style="padding:10px 0;color:#f9fafb;text-align:right;font-weight:600;">{m["submissions_this_week"]}</td>
            </tr>
            <tr style="border-bottom:1px solid #2a2a3a;">
              <td style="padding:10px 0;color:#9ca3af;">Agent Tasks Completed</td>
              <td style="padding:10px 0;color:#f9fafb;text-align:right;font-weight:600;">{m["tasks_completed"]} / {m["total_tasks"]}</td>
            </tr>
            <tr style="border-bottom:1px solid #2a2a3a;">
              <td style="padding:10px 0;color:#9ca3af;">Top Agent</td>
              <td style="padding:10px 0;color:#8b5cf6;text-align:right;font-weight:600;">{m["top_agent"]["name"]} ({m["top_agent"]["tasks"]} tasks)</td>
            </tr>
            <tr>
              <td style="padding:10px 0;color:#9ca3af;">Top Artist</td>
              <td style="padding:10px 0;color:#10b981;text-align:right;font-weight:600;">{m["top_artist"]["name"]} ({m["top_artist"]["listeners"]:,} listeners)</td>
            </tr>
          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td align="center" style="padding-top:32px;">
          <p style="margin:0;font-size:13px;color:#52525b;">&copy; 2026 Melodio &middot; melodio.io</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


async def send_weekly_digest(to_email: str, db: AsyncSession) -> dict:
    """Generate the weekly digest and send it via email."""
    digest = await generate_weekly_digest(db)
    sent = await send_email(
        to=to_email,
        subject=f"Melodio Weekly Digest — {digest['period']}",
        html_content=digest["html"],
    )
    digest["email_sent"] = sent
    digest["sent_to"] = to_email
    return digest
