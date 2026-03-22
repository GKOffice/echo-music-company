import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
DEFAULT_FROM = "hello@melodio.io"

# ---------------------------------------------------------------------------
# HTML Templates
# ---------------------------------------------------------------------------

WELCOME_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#13131a;border-radius:12px;padding:48px 40px;">
        <tr><td align="center" style="padding-bottom:32px;">
          <span style="font-size:28px;font-weight:700;color:#8b5cf6;letter-spacing:-0.5px;">melodio</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:16px;">
          <h1 style="margin:0;font-size:22px;color:#f9fafb;">Welcome to Melodio{name_line}</h1>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            The future of music is here. We'll be in touch soon.
          </p>
        </td></tr>
        <tr><td align="center">
          <p style="margin:0;font-size:13px;color:#52525b;">&copy; 2026 Melodio &middot; melodio.io</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

WAITLIST_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#13131a;border-radius:12px;padding:48px 40px;">
        <tr><td align="center" style="padding-bottom:32px;">
          <span style="font-size:28px;font-weight:700;color:#8b5cf6;letter-spacing:-0.5px;">melodio</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:16px;">
          <h1 style="margin:0;font-size:22px;color:#f9fafb;">You're on the Melodio waitlist</h1>
        </td></tr>
        <tr><td align="center" style="padding-bottom:24px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            Melodio is an autonomous AI music company &mdash; 21 agents working together
            to scout, sign, produce, and release music without the traditional label overhead.
          </p>
        </td></tr>
        <tr><td align="center" style="padding-bottom:24px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            <strong style="color:#10b981;">What to expect:</strong> Early access invites are rolling out soon.
            You'll be among the first to experience the platform when we launch.
          </p>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            Sit tight &mdash; we'll reach out when your spot is ready.
          </p>
        </td></tr>
        <tr><td align="center">
          <p style="margin:0;font-size:13px;color:#52525b;">&copy; 2026 Melodio &middot; melodio.io</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

ARTIST_SIGNED_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#13131a;border-radius:12px;padding:48px 40px;">
        <tr><td align="center" style="padding-bottom:32px;">
          <span style="font-size:28px;font-weight:700;color:#8b5cf6;letter-spacing:-0.5px;">melodio</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:16px;">
          <h1 style="margin:0;font-size:22px;color:#f9fafb;">Welcome aboard, {artist_name}</h1>
        </td></tr>
        <tr><td align="center" style="padding-bottom:24px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            You've been signed to Melodio. Our 21-agent system is already spinning up
            your artist profile, production pipeline, and release strategy.
          </p>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            Check your dashboard for next steps. Let's make history.
          </p>
        </td></tr>
        <tr><td align="center">
          <p style="margin:0;font-size:13px;color:#52525b;">&copy; 2026 Melodio &middot; melodio.io</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

async def send_email(
    to: str,
    subject: str,
    html_content: str,
    from_email: str = DEFAULT_FROM,
) -> bool:
    """Send a single HTML email via SendGrid."""
    message = Mail(
        from_email=from_email,
        to_emails=to,
        subject=subject,
        html_content=html_content,
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info("Email sent to %s — status %s", to, response.status_code)
        return True
    except Exception as exc:
        logger.error("SendGrid error sending to %s: %s", to, exc)
        return False


async def send_template_email(
    to: str,
    template_id: str,
    dynamic_data: dict,
    from_email: str = DEFAULT_FROM,
) -> bool:
    """Send a dynamic template email via SendGrid."""
    message = Mail(from_email=from_email, to_emails=to)
    message.template_id = template_id
    message.dynamic_template_data = dynamic_data
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info("Template email sent to %s — status %s", to, response.status_code)
        return True
    except Exception as exc:
        logger.error("SendGrid template error sending to %s: %s", to, exc)
        return False


# ---------------------------------------------------------------------------
# Pre-built emails
# ---------------------------------------------------------------------------

async def welcome_email(to_email: str, name: str = "") -> bool:
    name_line = f", {name}" if name else ""
    html = WELCOME_HTML.replace("{name_line}", name_line)
    return await send_email(to_email, "Welcome to Melodio", html)


async def waitlist_confirmation(to_email: str) -> bool:
    return await send_email(to_email, "You're on the Melodio waitlist", WAITLIST_HTML)


async def artist_signed_email(to_email: str, artist_name: str) -> bool:
    html = ARTIST_SIGNED_HTML.replace("{artist_name}", artist_name)
    return await send_email(to_email, f"Welcome aboard, {artist_name}", html)


# ---------------------------------------------------------------------------
# Onboarding & Pipeline emails
# ---------------------------------------------------------------------------

ONBOARDING_WELCOME_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#13131a;border-radius:12px;padding:48px 40px;">
        <tr><td align="center" style="padding-bottom:32px;">
          <span style="font-size:28px;font-weight:700;color:#8b5cf6;letter-spacing:-0.5px;">melodio</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:16px;">
          <h1 style="margin:0;font-size:22px;color:#f9fafb;">Welcome to Melodio{name_line}</h1>
        </td></tr>
        <tr><td style="padding-bottom:24px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            Your artist profile is set up. Here is what happens next:
          </p>
          <ul style="color:#a1a1aa;font-size:15px;line-height:1.8;">
            <li><strong style="color:#10b981;">Connect your platforms</strong> &mdash; link Spotify, Instagram, and YouTube so our agents can analyze your audience.</li>
            <li><strong style="color:#10b981;">Upload a demo</strong> &mdash; our A&amp;R agent will review it within 24 hours.</li>
            <li><strong style="color:#10b981;">Review your growth report</strong> &mdash; personalized recommendations powered by 21 AI agents.</li>
          </ul>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <a href="https://melodio.io/onboarding" style="display:inline-block;background:#8b5cf6;color:#fff;font-size:16px;font-weight:600;padding:14px 32px;border-radius:8px;text-decoration:none;">Continue Onboarding</a>
        </td></tr>
        <tr><td align="center">
          <p style="margin:0;font-size:13px;color:#52525b;">&copy; 2026 Melodio &middot; melodio.io</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

DEMO_RECEIVED_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#13131a;border-radius:12px;padding:48px 40px;">
        <tr><td align="center" style="padding-bottom:32px;">
          <span style="font-size:28px;font-weight:700;color:#8b5cf6;letter-spacing:-0.5px;">melodio</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:16px;">
          <h1 style="margin:0;font-size:22px;color:#f9fafb;">Demo Received</h1>
        </td></tr>
        <tr><td align="center" style="padding-bottom:24px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            We received your demo <strong style="color:#f9fafb;">{title}</strong>.
            Our A&amp;R agent is now reviewing it &mdash; you will hear back within 24 hours.
          </p>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <p style="margin:0;font-size:15px;line-height:1.6;color:#a1a1aa;">
            In the meantime, check your <a href="https://melodio.io/dashboard" style="color:#8b5cf6;text-decoration:underline;">dashboard</a> for your growth report.
          </p>
        </td></tr>
        <tr><td align="center">
          <p style="margin:0;font-size:13px;color:#52525b;">&copy; 2026 Melodio &middot; melodio.io</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

RELEASE_SUBMITTED_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#13131a;border-radius:12px;padding:48px 40px;">
        <tr><td align="center" style="padding-bottom:32px;">
          <span style="font-size:28px;font-weight:700;color:#8b5cf6;letter-spacing:-0.5px;">melodio</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:16px;">
          <h1 style="margin:0;font-size:22px;color:#f9fafb;">Release Submitted</h1>
        </td></tr>
        <tr><td align="center" style="padding-bottom:24px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            Your release <strong style="color:#f9fafb;">{title}</strong> is being prepared for distribution.
            Our QC agent will review it, and once approved it will be sent to Spotify, Apple Music, and 150+ platforms.
          </p>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <a href="https://melodio.io/releases" style="display:inline-block;background:#8b5cf6;color:#fff;font-size:16px;font-weight:600;padding:14px 32px;border-radius:8px;text-decoration:none;">View Release Status</a>
        </td></tr>
        <tr><td align="center">
          <p style="margin:0;font-size:13px;color:#52525b;">&copy; 2026 Melodio &middot; melodio.io</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

RELEASE_LIVE_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#13131a;border-radius:12px;padding:48px 40px;">
        <tr><td align="center" style="padding-bottom:32px;">
          <span style="font-size:28px;font-weight:700;color:#8b5cf6;letter-spacing:-0.5px;">melodio</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:16px;">
          <h1 style="margin:0;font-size:22px;color:#f9fafb;">Your Music Is Live!</h1>
        </td></tr>
        <tr><td align="center" style="padding-bottom:24px;">
          <p style="margin:0;font-size:16px;line-height:1.6;color:#a1a1aa;">
            <strong style="color:#10b981;">{title}</strong> is now available on Spotify, Apple Music, and 150+ platforms worldwide.
          </p>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <a href="https://melodio.io/dashboard" style="display:inline-block;background:#10b981;color:#fff;font-size:16px;font-weight:600;padding:14px 32px;border-radius:8px;text-decoration:none;">View Analytics</a>
        </td></tr>
        <tr><td align="center">
          <p style="margin:0;font-size:13px;color:#52525b;">&copy; 2026 Melodio &middot; melodio.io</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


async def onboarding_welcome_email(to_email: str, name: str = "") -> bool:
    name_line = f", {name}" if name else ""
    html = ONBOARDING_WELCOME_HTML.replace("{name_line}", name_line)
    return await send_email(to_email, "Welcome to Melodio — here's what happens next", html)


async def demo_received_email(to_email: str, title: str = "your track") -> bool:
    html = DEMO_RECEIVED_HTML.replace("{title}", title)
    return await send_email(to_email, "We received your demo", html)


async def release_submitted_email(to_email: str, title: str = "your release") -> bool:
    html = RELEASE_SUBMITTED_HTML.replace("{title}", title)
    return await send_email(to_email, "Your release is being prepared for distribution", html)


async def release_live_email(to_email: str, title: str = "your release") -> bool:
    html = RELEASE_LIVE_HTML.replace("{title}", title)
    return await send_email(to_email, "Your music is now live!", html)
