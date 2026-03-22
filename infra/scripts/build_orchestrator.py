#!/usr/bin/env python3
"""
Melodio Autonomous Build Orchestrator
Executes the full deployment build plan without human intervention.
Uses Claude Opus for complex decisions, spawns sub-agents per task group.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"/tmp/melodio-build-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"),
    ],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─── BUILD PLAN ──────────────────────────────────────────────────────────────

CRITICAL_BLOCKERS = [
    {
        "id": "fix_waitlist",
        "name": "Fix waitlist → save to Postgres",
        "priority": "CRITICAL",
        "parallel": False,
        "prompt": """
Fix the Melodio waitlist system at ~/projects/echo.

PROBLEM: apps/web/app/api/waitlist/route.ts saves to a JSON file that gets wiped on every Railway deploy.

FIX NEEDED:
1. Create a new API endpoint in apps/api/routers/waitlist.py:
   - POST /api/v1/waitlist — accepts {email, source (optional)}
   - Saves to PostgreSQL `waitlist` table
   - Returns {success, message, already_exists}
   - Add CREATE TABLE IF NOT EXISTS in the router on startup

2. Update apps/web/app/api/waitlist/route.ts:
   - Instead of writing to a file, POST to the FastAPI backend: ${NEXT_PUBLIC_API_URL}/api/v1/waitlist
   - Keep the same response interface

3. Register the router in apps/api/main.py

4. Add waitlist table migration: apps/api/migrations/add_waitlist.sql:
   CREATE TABLE IF NOT EXISTS waitlist (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     email VARCHAR(255) UNIQUE NOT NULL,
     source VARCHAR(100) DEFAULT 'landing_page',
     created_at TIMESTAMPTZ DEFAULT NOW(),
     notified_at TIMESTAMPTZ
   );

5. Run migration on Railway Postgres:
   DB_URL is: postgresql://postgres:KpnrMApfyDKlrNOHyBBuXmdAdsPQiCWG@caboose.proxy.rlwy.net:38496/railway
   Use python3 with asyncpg to run the migration.

6. Test: curl -X POST https://api-production-14b6.up.railway.app/api/v1/waitlist -H "Content-Type: application/json" -d '{"email":"test@melodio.io"}'

7. Deploy API: cd ~/projects/echo/apps/api && railway service link API && railway up --service API

8. Commit: git add -A && git commit -m "fix: waitlist saves to Postgres — persists across deploys"

When done: openclaw system event --text "Done: Waitlist now saves to Postgres" --mode now
""",
    },
    {
        "id": "create_admin_account",
        "name": "Create Mike's admin account",
        "priority": "CRITICAL",
        "parallel": False,
        "prompt": """
Create an admin account for Mike B. in the Melodio platform at ~/projects/echo.

Tasks:
1. Connect to Railway Postgres:
   DB URL: postgresql://postgres:KpnrMApfyDKlrNOHyBBuXmdAdsPQiCWG@caboose.proxy.rlwy.net:38496/railway
   Use asyncpg or psycopg2 to connect.

2. Check the users table schema: SELECT column_name, data_type FROM information_schema.columns WHERE table_name='users';

3. If users table doesn't exist, check what tables exist: SELECT tablename FROM pg_tables WHERE schemaname='public';

4. Create the admin user by calling the live API:
   POST https://api-production-14b6.up.railway.app/api/v1/auth/register
   Body: {"email": "mike@melodio.io", "password": "MelodioCEO2026!", "role": "owner"}
   
   Note: The register endpoint only allows roles: developer, owner, artist, producer
   Use "owner" role.

5. Then manually upgrade to admin in DB:
   UPDATE users SET role = 'admin' WHERE email = 'mike@melodio.io';

6. Test login:
   POST https://api-production-14b6.up.railway.app/api/v1/auth/token
   Form data: username=mike@melodio.io&password=MelodioCEO2026!
   Save the access_token

7. Test authenticated endpoint:
   GET https://api-production-14b6.up.railway.app/api/v1/auth/me
   Header: Authorization: Bearer <token>

8. Write credentials to ~/projects/echo/ADMIN_CREDENTIALS.md (gitignored):
   Email: mike@melodio.io
   Password: MelodioCEO2026!
   Platform URL: https://melodio.io/platform
   API URL: https://api-production-14b6.up.railway.app

9. Add ADMIN_CREDENTIALS.md to .gitignore

10. Commit: git add -A && git commit -m "fix: admin account created, credentials documented"

When done: openclaw system event --text "Done: Admin account created — mike@melodio.io / MelodioCEO2026!" --mode now
""",
    },
    {
        "id": "wire_auth_frontend",
        "name": "Wire auth to frontend — remove mock data",
        "priority": "CRITICAL",
        "parallel": False,
        "prompt": """
Wire real authentication to the Melodio frontend at ~/projects/echo/apps/web.

CURRENT STATE: The frontend has mock/hardcoded data. Users can't actually log in.

TASKS:

1. Check the current auth setup:
   - Read apps/web/app/auth/login/page.tsx
   - Read apps/web/app/auth/signup/page.tsx
   - Read apps/web/providers.tsx
   - Check if there's a NextAuth or custom auth context

2. Create/update apps/web/lib/auth.ts:
   - API_URL = process.env.NEXT_PUBLIC_API_URL
   - login(email, password) → POST /api/v1/auth/token → store JWT in localStorage/cookie
   - register(email, password, role) → POST /api/v1/auth/register
   - logout() → clear token
   - getMe() → GET /api/v1/auth/me with Bearer token
   - isAuthenticated() → check if valid token exists

3. Create apps/web/lib/api-client.ts:
   - Axios or fetch wrapper that auto-attaches Authorization: Bearer <token>
   - Handles 401 → redirect to /auth/login
   - Base URL: process.env.NEXT_PUBLIC_API_URL

4. Update login page (apps/web/app/auth/login/page.tsx):
   - Wire form to real auth.login()
   - On success: redirect to /dashboard
   - On error: show real error message

5. Update signup page (apps/web/app/auth/signup/page.tsx):
   - Wire form to real auth.register()
   - Role selector: artist / producer / developer
   - On success: redirect to /dashboard

6. Update apps/web/app/dashboard/page.tsx:
   - Replace any mock data with real API calls
   - Protect route: redirect to /auth/login if not authenticated
   - Call GET /api/v1/auth/me to show real user info

7. Update apps/web/app/platform/page.tsx:
   - Add auth protection (redirect if not logged in)

8. Build check: cd apps/web && npm run build 2>&1 | tail -20

9. Deploy: cd ~/projects/echo && railway service link Web && railway up --service Web

10. Commit: git add -A && git commit -m "feat: wire real auth to frontend — JWT login/signup/dashboard"

When done: openclaw system event --text "Done: Auth wired to frontend — real login/signup working" --mode now
""",
    },
    {
        "id": "run_db_migrations",
        "name": "Run all DB migrations on Railway Postgres",
        "priority": "CRITICAL",
        "parallel": True,
        "prompt": """
Run all pending database migrations on Railway Postgres for Melodio.

Railway Postgres connection:
DB_URL = postgresql://postgres:KpnrMApfyDKlrNOHyBBuXmdAdsPQiCWG@caboose.proxy.rlwy.net:38496/railway

Tasks:

1. Connect to Railway Postgres using asyncpg (pip install asyncpg if needed):

2. Check existing tables: SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;

3. Run these migrations IN ORDER:

   A. Main schema (find it in apps/api/ — look for schema.sql, models.py or alembic migrations):
      - Check if core tables exist (users, artists, releases, agent_tasks, audit_log, etc.)
      - If not, find the CREATE TABLE statements in apps/api/models/ or similar
      - Run them

   B. apps/api/migrations/add_agent_memory.sql — agent learning memory table

   C. apps/api/migrations/add_waitlist.sql — waitlist table (create this file first if it doesn't exist):
      CREATE TABLE IF NOT EXISTS waitlist (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        source VARCHAR(100) DEFAULT 'landing_page',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        notified_at TIMESTAMPTZ
      );

4. Verify all tables exist after migration:
   SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;

5. Write migration log to: ~/projects/echo/infra/migration-log.json
   {"run_at": "...", "tables_created": [...], "status": "success"}

6. Commit: git add -A && git commit -m "chore: DB migrations run on Railway Postgres"

When done: openclaw system event --text "Done: All DB migrations applied to Railway Postgres" --mode now
""",
    },
    {
        "id": "deploy_agents_service",
        "name": "Deploy Agents service to Railway",
        "priority": "CRITICAL",
        "parallel": True,
        "prompt": """
Deploy the Melodio Agents service to Railway production.

Project: ~/projects/echo
Agents directory: apps/agents/

CURRENT STATE: The agents service is not deployed to Railway. The railway.toml has no agents service entry.

Tasks:

1. Check railway.toml at ~/projects/echo/railway.toml — see current services

2. Check apps/agents/Dockerfile — make sure it's valid

3. Check apps/agents/requirements.txt — make sure all deps are listed including:
   - anthropic
   - asyncpg
   - langchain (if used)
   - redis
   - pydantic
   - tenacity
   (Fix any obvious missing deps)

4. Add agents service to railway.toml:
   [[services]]
   name = "agents"
   source = "apps/agents"
   dockerfile = "apps/agents/Dockerfile"
   
   [services.deploy]
   startCommand = "python3 main.py"
   restartPolicyType = "on_failure"
   restartPolicyMaxRetries = 3

5. Create the service on Railway if it doesn't exist:
   cd ~/projects/echo && railway add --service agents 2>/dev/null || echo "service may exist"

6. Deploy: cd ~/projects/echo/apps/agents && railway service link agents 2>/dev/null && railway up --service agents 2>&1

   If "service not found" error: use railway CLI to create and link manually.

7. Set required env vars on the agents service:
   railway variables set ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY DATABASE_URL=<railway internal url> REDIS_URL=<railway internal redis url> --service agents

8. Check deployment status: railway service status

9. Commit: git add -A && git commit -m "feat: agents service deployed to Railway"

When done: openclaw system event --text "Done: Agents service deployed to Railway — 23 agents running in production" --mode now
""",
    },
    {
        "id": "register_whatsapp_webhook",
        "name": "Register WhatsApp webhook with Meta",
        "priority": "CRITICAL",
        "parallel": True,
        "prompt": """
Register the Melodio WhatsApp webhook with Meta's Graph API.

CONTEXT:
- WhatsApp API Token (never expires): EAAXVu5Lh0JkBRK3U1ZCyHl6fPstjcLKZC7ZAU9LIxffb1bbRyxPZBKHzteCKFPjGi0CvQR6i4CccaQnHXJobEEHOAeMyM36jebRLtYeNEzQtaoHJ5q5CCy3LUOfGvbFchXUxWCeOx4uP9SMgyVsTM2fYgbs5qSYbhHwnXZBaZCE2eoKpFwnJ2e8tJE8v9NKwZDZD
- App ID: 1642376483426457
- Phone Number ID: 1086543297868419
- Webhook URL: https://api-production-14b6.up.railway.app/api/v1/whatsapp/webhook
- Verify token: melodio_webhook_2026

TASKS:

1. First verify the webhook endpoint is responding:
   curl "https://api-production-14b6.up.railway.app/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=melodio_webhook_2026&hub.challenge=test123"
   Expected: "test123"

2. Get the app access token using App ID + App Secret:
   - App Secret is needed. Check ~/projects/echo/.env for WHATSAPP_APP_SECRET or FACEBOOK_APP_SECRET
   - If not found, generate app token: GET https://graph.facebook.com/oauth/access_token?client_id=1642376483426457&client_secret=<secret>&grant_type=client_credentials
   
3. Register webhook subscription:
   POST https://graph.facebook.com/v18.0/1642376483426457/subscriptions
   Params: object=whatsapp_business_account, callback_url=..., verify_token=..., fields=messages

4. If app secret not available, document the manual step needed:
   - Save instructions to ~/projects/echo/infra/WHATSAPP_WEBHOOK_MANUAL_STEP.md
   - Include exact curl command to run once app secret is obtained

5. Verify subscription was registered:
   GET https://graph.facebook.com/v18.0/1642376483426457/subscriptions

6. Update .env with WHATSAPP_VERIFY_TOKEN=melodio_webhook_2026

7. Commit: git add -A && git commit -m "feat: WhatsApp webhook registration attempted + manual steps documented"

When done: openclaw system event --text "Done: WhatsApp webhook registration complete or manual steps documented" --mode now
""",
    },
    {
        "id": "wire_sendgrid",
        "name": "Wire SendGrid — welcome emails + notifications",
        "priority": "CRITICAL",
        "parallel": True,
        "prompt": """
Wire SendGrid email system into Melodio at ~/projects/echo.

SendGrid API key is already in .env as SENDGRID_API_KEY.

Tasks:

1. Create apps/api/services/email.py — email service module:
   - Use sendgrid Python SDK (add to requirements.txt if not present)
   - send_email(to, subject, html_content, from_email="hello@melodio.io")
   - send_template_email(to, template_id, dynamic_data) for future templates
   - welcome_email(to_email, name="") — sends branded welcome
   - waitlist_confirmation(to_email) — "You're on the list" email
   - artist_signed_email(to_email, artist_name) — onboarding email
   
2. HTML email templates (inline in email.py):
   WELCOME_HTML: Clean dark Melodio branded email
   - Subject: "Welcome to Melodio"
   - Body: "The future of music is here. We'll be in touch soon."
   - Melodio purple/dark design
   
   WAITLIST_HTML:
   - Subject: "You're on the Melodio waitlist"
   - Body: What Melodio is, what to expect, when launching

3. Wire to waitlist endpoint (apps/api/routers/waitlist.py):
   - After saving email to DB, send waitlist_confirmation()
   - Non-blocking: use asyncio.create_task() so it doesn't slow the response

4. Wire to auth register (apps/api/routers/auth.py):
   - After successful registration, send welcome_email()

5. Test: python3 -c "
   import asyncio
   import sys
   sys.path.insert(0, 'apps/api')
   from services.email import send_email
   asyncio.run(send_email('mike@melodio.io', 'Test', '<h1>It works!</h1>'))
   print('Email sent')
   "

6. Deploy API: cd ~/projects/echo/apps/api && railway service link API && railway up --service API

7. Commit: git add -A && git commit -m "feat: SendGrid wired — welcome emails + waitlist confirmation"

When done: openclaw system event --text "Done: SendGrid wired — emails sending on signup and waitlist" --mode now
""",
    },
]

HIGH_PRIORITY_TASKS = [
    {
        "id": "wire_stripe_connect",
        "name": "Set up Stripe Connect for artist payouts",
        "priority": "HIGH",
        "parallel": True,
        "prompt": """
Set up Stripe Connect for artist payouts in Melodio at ~/projects/echo.

CONTEXT: Stripe keys are in .env (currently test mode). Stripe Connect allows artists to receive payouts directly.

Tasks:

1. Read apps/api/routers/payments.py — understand current Stripe setup

2. Create apps/api/services/stripe_connect.py:
   - create_connect_account(email, country="US") → creates Stripe Express account
   - create_onboarding_link(account_id, refresh_url, return_url) → get onboarding URL
   - get_account_status(account_id) → check if fully onboarded
   - create_payout(account_id, amount_cents, currency="usd") → send money to artist
   - get_payout_history(account_id) → list payouts

3. Add to apps/api/routers/payments.py:
   - POST /api/v1/payments/connect/onboard → creates Connect account + returns onboarding link
   - GET /api/v1/payments/connect/status → check artist's Connect account status
   - POST /api/v1/payments/connect/payout → trigger artist payout (admin only)

4. Add stripe_connect_id column to artists table:
   ALTER TABLE artists ADD COLUMN IF NOT EXISTS stripe_connect_id VARCHAR(255);
   ALTER TABLE artists ADD COLUMN IF NOT EXISTS stripe_connect_status VARCHAR(50) DEFAULT 'not_started';
   Run on Railway DB: postgresql://postgres:KpnrMApfyDKlrNOHyBBuXmdAdsPQiCWG@caboose.proxy.rlwy.net:38496/railway

5. Update STRIPE_CONNECT_CLIENT_ID in .env (already set — verify it's the right test key)

6. Deploy: cd ~/projects/echo/apps/api && railway service link API && railway up --service API

7. Commit: git add -A && git commit -m "feat: Stripe Connect — artist payout onboarding + payout flow"

When done: openclaw system event --text "Done: Stripe Connect wired for artist payouts" --mode now
""",
    },
    {
        "id": "wire_distrokid",
        "name": "Wire DistroKid distribution API",
        "priority": "HIGH",
        "parallel": True,
        "prompt": """
Wire DistroKid API into the Melodio distribution system at ~/projects/echo.

CONTEXT: DISTROKID_API_KEY is in .env.

Tasks:

1. Read apps/api/routers/distribution.py — understand current distribution endpoints

2. Create apps/api/services/distrokid.py:
   - Base URL: https://app.distrokid.com/api/
   - submit_release(artist_name, track_title, audio_url, cover_url, release_date, isrc=None) 
   - get_release_status(distrokid_id) → check distribution status
   - get_streaming_stats(distrokid_id) → pull stream counts per DSP
   - list_releases(artist_name) → get all releases

3. Wire into distribution router:
   - POST /api/v1/distribution/releases/{release_id}/submit → calls distrokid.submit_release()
   - GET /api/v1/distribution/releases/{release_id}/stats → calls distrokid.get_streaming_stats()

4. Add distrokid_id column to releases table:
   ALTER TABLE releases ADD COLUMN IF NOT EXISTS distrokid_id VARCHAR(255);
   ALTER TABLE releases ADD COLUMN IF NOT EXISTS distribution_status VARCHAR(50) DEFAULT 'pending';
   Run on: postgresql://postgres:KpnrMApfyDKlrNOHyBBuXmdAdsPQiCWG@caboose.proxy.rlwy.net:38496/railway

5. NOTE: If DistroKid API is not publicly documented, create a mock implementation 
   that matches expected interface and logs what would be sent. Add TODO comments.

6. Deploy API and commit.

When done: openclaw system event --text "Done: DistroKid distribution API wired" --mode now
""",
    },
]


async def run_claude_agent(task: dict, model: str = "claude-opus-4-6") -> dict:
    """Run a Claude Code agent for a specific task."""
    task_id = task["id"]
    task_name = task["name"]
    prompt = task["prompt"]

    logger.info(f"[{task_id}] Starting: {task_name}")
    start_time = time.time()

    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

    cmd = [
        "claude",
        "--model", model,
        "--permission-mode", "bypassPermissions",
        "--print",
        prompt,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=900)
        elapsed = int(time.time() - start_time)

        output = stdout.decode("utf-8", errors="replace")
        error = stderr.decode("utf-8", errors="replace")

        success = proc.returncode == 0

        result = {
            "task_id": task_id,
            "task_name": task_name,
            "success": success,
            "elapsed_seconds": elapsed,
            "output_preview": output[-500:] if output else "",
            "error": error[-200:] if error and not success else "",
        }

        if success:
            logger.info(f"[{task_id}] ✅ Complete in {elapsed}s")
        else:
            logger.error(f"[{task_id}] ❌ Failed after {elapsed}s: {error[-200:]}")

        return result

    except asyncio.TimeoutError:
        logger.error(f"[{task_id}] ⏰ Timed out after 900s")
        return {"task_id": task_id, "task_name": task_name, "success": False, "error": "timeout"}
    except Exception as e:
        logger.error(f"[{task_id}] 💥 Exception: {e}")
        return {"task_id": task_id, "task_name": task_name, "success": False, "error": str(e)}


async def run_phase(tasks: list, phase_name: str, model: str) -> list:
    """Run a phase of tasks — parallel where allowed, sequential where required."""
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE: {phase_name}")
    logger.info(f"Tasks: {len(tasks)}")
    logger.info(f"Model: {model}")
    logger.info(f"{'='*60}\n")

    results = []

    # Separate sequential and parallel tasks
    sequential = [t for t in tasks if not t.get("parallel", False)]
    parallel = [t for t in tasks if t.get("parallel", False)]

    # Run sequential tasks first
    for task in sequential:
        result = await run_claude_agent(task, model)
        results.append(result)
        # Wait a moment between sequential tasks
        await asyncio.sleep(5)

    # Run parallel tasks simultaneously
    if parallel:
        logger.info(f"Running {len(parallel)} tasks in parallel...")
        parallel_results = await asyncio.gather(
            *[run_claude_agent(task, model) for task in parallel]
        )
        results.extend(parallel_results)

    return results


def save_build_report(all_results: list):
    """Save build report to disk."""
    report_path = PROJECT_ROOT / "infra" / "build-report.json"
    report_path.parent.mkdir(exist_ok=True)

    report = {
        "run_at": datetime.now().isoformat(),
        "total_tasks": len(all_results),
        "successful": sum(1 for r in all_results if r.get("success")),
        "failed": sum(1 for r in all_results if not r.get("success")),
        "results": all_results,
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nBuild report saved: {report_path}")
    return report


async def main():
    logger.info("⚡ MELODIO AUTONOMOUS BUILD ORCHESTRATOR")
    logger.info("=" * 60)
    logger.info(f"Project: {PROJECT_ROOT}")
    logger.info(f"Model: claude-opus-4-6")
    logger.info(f"Tasks: {len(CRITICAL_BLOCKERS)} critical + {len(HIGH_PRIORITY_TASKS)} high priority")
    logger.info("=" * 60)

    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    all_results = []

    # Phase 1: Critical blockers
    critical_results = await run_phase(
        CRITICAL_BLOCKERS,
        "CRITICAL BLOCKERS — Must fix before launch",
        model="claude-opus-4-6",
    )
    all_results.extend(critical_results)

    # Phase 2: High priority
    high_results = await run_phase(
        HIGH_PRIORITY_TASKS,
        "HIGH PRIORITY — Before first artist",
        model="claude-opus-4-6",
    )
    all_results.extend(high_results)

    # Final report
    report = save_build_report(all_results)

    logger.info("\n" + "=" * 60)
    logger.info("BUILD COMPLETE")
    logger.info(f"✅ Successful: {report['successful']}/{report['total_tasks']}")
    logger.info(f"❌ Failed: {report['failed']}/{report['total_tasks']}")
    logger.info("=" * 60)

    # Notify
    subprocess.run([
        "openclaw", "system", "event",
        "--text", f"Melodio autonomous build complete: {report['successful']}/{report['total_tasks']} tasks succeeded",
        "--mode", "now"
    ], capture_output=True)

    return report["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
