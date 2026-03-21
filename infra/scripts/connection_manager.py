#!/usr/bin/env python3
"""
Melodio Connection Manager
B (CEO) — Autonomous service connection tool
Tests, validates, and monitors all external integrations without human involvement.
"""

import os
import sys
import json
import asyncio
import httpx
import socket
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env from project root
ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env", override=True)

# ──────────────────────────────────────────────
# COLORS
# ──────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✅ {msg}{RESET}")
def fail(msg): print(f"  {RED}❌ {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}⚠️  {msg}{RESET}")
def info(msg): print(f"  {CYAN}ℹ️  {msg}{RESET}")
def header(msg): print(f"\n{BOLD}{CYAN}{'─'*50}{RESET}\n{BOLD} {msg}{RESET}\n{'─'*50}")


# ──────────────────────────────────────────────
# RESULT STORE
# ──────────────────────────────────────────────
results = {}

def record(service: str, connected: bool, detail: str = ""):
    results[service] = {
        "connected": connected,
        "detail": detail,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


# ──────────────────────────────────────────────
# CHECKS
# ──────────────────────────────────────────────

async def check_postgres():
    header("PostgreSQL")
    url = os.getenv("DATABASE_URL", "")
    if not url:
        fail("DATABASE_URL not set")
        record("postgres", False, "no env var")
        return

    try:
        import asyncpg
        # asyncpg uses different URL format
        pg_url = url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncio.wait_for(asyncpg.connect(pg_url), timeout=5)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        ok(f"Connected — {version.split(',')[0]}")
        record("postgres", True, version.split(',')[0])
    except ImportError:
        warn("asyncpg not installed — trying pg_isready")
        try:
            r = subprocess.run(["pg_isready", "-h", "localhost", "-p", "5432"],
                               capture_output=True, timeout=5)
            if r.returncode == 0:
                ok("pg_isready: accepting connections")
                record("postgres", True, "pg_isready OK")
            else:
                fail("pg_isready: not accepting connections")
                record("postgres", False, "pg_isready failed")
        except FileNotFoundError:
            warn("pg_isready not found — checking Docker")
            _check_docker_container("echo_postgres", "postgres")
    except Exception as e:
        fail(f"Connection failed: {e}")
        record("postgres", False, str(e))


async def check_redis():
    header("Redis")
    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(url, socket_timeout=3)
        pong = await r.ping()
        info_data = await r.info("server")
        version = info_data.get("redis_version", "unknown")
        await r.aclose()
        ok(f"Connected — Redis {version}")
        record("redis", True, f"Redis {version}")
    except Exception as e:
        fail(f"Connection failed: {e}")
        record("redis", False, str(e))


async def check_stripe():
    header("Stripe")
    secret = os.getenv("STRIPE_SECRET_KEY", "")
    if not secret:
        fail("STRIPE_SECRET_KEY not set")
        record("stripe", False, "no key")
        return

    mode = "LIVE" if secret.startswith("sk_live") else "TEST"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.stripe.com/v1/balance",
                auth=(secret, "")
            )
        if r.status_code == 200:
            data = r.json()
            avail = data.get("available", [{}])
            ok(f"Connected [{mode} mode] — balance endpoint OK")
            if mode == "TEST":
                warn("Using TEST keys — switch to live keys before launch")
            record("stripe", True, f"{mode} mode")
        elif r.status_code == 401:
            fail("Invalid Stripe key")
            record("stripe", False, "401 unauthorized")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:100]}")
            record("stripe", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Request failed: {e}")
        record("stripe", False, str(e))

    # Webhook secret
    webhook = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if webhook:
        ok("Webhook secret configured")
    else:
        warn("STRIPE_WEBHOOK_SECRET not set — webhooks won't verify")

    # Connect client ID
    connect = os.getenv("STRIPE_CONNECT_CLIENT_ID", "")
    if connect:
        ok("Stripe Connect client ID configured")
    else:
        warn("STRIPE_CONNECT_CLIENT_ID not set — artist payouts need this")


async def check_anthropic():
    header("Anthropic (Claude AI)")
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        fail("ANTHROPIC_API_KEY not set")
        record("anthropic", False, "no key")
        return

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "ping"}]
                }
            )
        if r.status_code == 200:
            ok("Connected — Claude API live")
            record("anthropic", True, "claude-3-haiku OK")
        elif r.status_code == 401:
            fail("Invalid API key")
            record("anthropic", False, "401")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:100]}")
            record("anthropic", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Request failed: {e}")
        record("anthropic", False, str(e))


async def check_openai():
    header("OpenAI")
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        warn("OPENAI_API_KEY not set — skipping")
        record("openai", False, "not configured")
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"}
            )
        if r.status_code == 200:
            ok("Connected — OpenAI API live")
            record("openai", True, "models endpoint OK")
        else:
            fail(f"HTTP {r.status_code}")
            record("openai", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Request failed: {e}")
        record("openai", False, str(e))


async def check_spotify():
    header("Spotify")
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        warn("SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET not set")
        record("spotify", False, "not configured")
        info("Get keys at: https://developer.spotify.com/dashboard")
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(client_id, client_secret)
            )
        if r.status_code == 200:
            token = r.json().get("access_token", "")
            ok(f"Connected — token acquired")
            record("spotify", True, "client credentials OK")
        elif r.status_code == 400:
            fail("Invalid client credentials")
            record("spotify", False, "400 bad request")
        else:
            fail(f"HTTP {r.status_code}")
            record("spotify", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Request failed: {e}")
        record("spotify", False, str(e))


async def check_youtube():
    header("YouTube API")
    key = os.getenv("YOUTUBE_API_KEY", "")
    if not key:
        warn("YOUTUBE_API_KEY not set")
        record("youtube", False, "not configured")
        info("Get key at: https://console.developers.google.com")
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "snippet", "mine": "true", "key": key}
            )
        if r.status_code in [200, 401]:  # 401 means key works, just needs OAuth
            ok("API key valid — connected")
            record("youtube", True, "key valid")
        elif r.status_code == 400:
            data = r.json()
            err = data.get("error", {}).get("message", "")
            fail(f"Bad request: {err}")
            record("youtube", False, err)
        else:
            fail(f"HTTP {r.status_code}")
            record("youtube", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Request failed: {e}")
        record("youtube", False, str(e))


async def check_sendgrid():
    header("SendGrid (Email)")
    key = os.getenv("SENDGRID_API_KEY", "")
    if not key:
        warn("SENDGRID_API_KEY not set")
        record("sendgrid", False, "not configured")
        info("Get key at: https://app.sendgrid.com/settings/api_keys")
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.sendgrid.com/v3/user/profile",
                headers={"Authorization": f"Bearer {key}"}
            )
        if r.status_code == 200:
            data = r.json()
            username = data.get("username", "unknown")
            ok(f"Connected — account: {username}")
            record("sendgrid", True, f"user: {username}")
        elif r.status_code == 401:
            fail("Invalid API key")
            record("sendgrid", False, "401")
        else:
            fail(f"HTTP {r.status_code}")
            record("sendgrid", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Request failed: {e}")
        record("sendgrid", False, str(e))


async def check_whatsapp():
    header("WhatsApp Business API")
    token = os.getenv("WHATSAPP_API_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

    if not token or not phone_id:
        warn("WHATSAPP_API_TOKEN / WHATSAPP_PHONE_NUMBER_ID not set")
        record("whatsapp", False, "not configured")
        info("Get credentials at: https://developers.facebook.com/apps")
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"https://graph.facebook.com/v18.0/{phone_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
        if r.status_code == 200:
            data = r.json()
            ok(f"Connected — phone ID: {phone_id}")
            record("whatsapp", True, f"phone: {phone_id}")
        elif r.status_code == 401:
            fail("Invalid access token")
            record("whatsapp", False, "401")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:100]}")
            record("whatsapp", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Request failed: {e}")
        record("whatsapp", False, str(e))


async def check_persona():
    header("Persona (KYC)")
    key = os.getenv("PERSONA_API_KEY", "")
    if not key:
        warn("PERSONA_API_KEY not set")
        record("persona", False, "not configured")
        info("Get key at: https://app.withpersona.com/dashboard")
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://withpersona.com/api/v1/inquiries",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Persona-Version": "2023-01-05"
                },
                params={"page[size]": 1}
            )
        if r.status_code == 200:
            ok("Connected — Persona KYC API live")
            record("persona", True, "inquiries endpoint OK")
        elif r.status_code == 401:
            fail("Invalid API key")
            record("persona", False, "401")
        else:
            fail(f"HTTP {r.status_code}")
            record("persona", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Request failed: {e}")
        record("persona", False, str(e))


async def check_aws_s3():
    header("AWS S3 / Storage")
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    bucket = os.getenv("AWS_S3_BUCKET", "echo-assets")
    region = os.getenv("AWS_REGION", "us-west-2")

    if not access_key or not secret:
        warn("AWS credentials not set")
        record("s3", False, "not configured")
        info("Configure at: https://console.aws.amazon.com/iam")
        return

    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        s3 = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret,
            region_name=region
        )
        s3.head_bucket(Bucket=bucket)
        ok(f"Connected — bucket '{bucket}' accessible")
        record("s3", True, f"bucket: {bucket}")
    except ImportError:
        warn("boto3 not installed — skipping S3 check")
        record("s3", False, "boto3 not installed")
    except Exception as e:
        err = str(e)
        if "NoSuchBucket" in err or "404" in err:
            warn(f"Key valid but bucket '{bucket}' not found — needs creation")
            record("s3", False, f"bucket not found: {bucket}")
        elif "InvalidAccessKeyId" in err or "401" in err:
            fail("Invalid AWS credentials")
            record("s3", False, "invalid credentials")
        else:
            fail(f"Error: {err[:100]}")
            record("s3", False, err[:100])


async def check_chartmetric():
    header("Chartmetric (Analytics)")
    key = os.getenv("CHARTMETRIC_API_KEY", "")
    if not key:
        warn("CHARTMETRIC_API_KEY not set")
        record("chartmetric", False, "not configured")
        info("Get key at: https://api.chartmetric.com")
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://api.chartmetric.com/api/token",
                json={"refreshtoken": key}
            )
        if r.status_code == 200:
            ok("Connected — Chartmetric token acquired")
            record("chartmetric", True, "token OK")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:80]}")
            record("chartmetric", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Request failed: {e}")
        record("chartmetric", False, str(e))


async def check_railway():
    header("Railway (Deployment)")
    # Check if railway CLI is installed and logged in
    try:
        r = subprocess.run(["railway", "status"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            ok(f"Railway CLI connected\n     {r.stdout.strip()[:80]}")
            record("railway", True, "CLI connected")
        else:
            warn(f"Railway CLI error: {r.stderr.strip()[:80]}")
            record("railway", False, r.stderr.strip()[:80])
    except FileNotFoundError:
        warn("Railway CLI not installed")
        record("railway", False, "CLI not installed")
        info("Install: npm install -g @railway/cli")
    except subprocess.TimeoutExpired:
        fail("Railway CLI timed out")
        record("railway", False, "timeout")


async def check_docker():
    header("Docker")
    try:
        r = subprocess.run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            lines = r.stdout.strip().split("\n")
            echo_containers = [l for l in lines if "echo" in l.lower()]
            if echo_containers:
                ok(f"Docker running — {len(echo_containers)} Echo containers:")
                for c in echo_containers:
                    info(f"  {c}")
                record("docker", True, f"{len(echo_containers)} containers running")
            else:
                warn("Docker running but no Echo containers active")
                record("docker", False, "no echo containers")
                info("Run: cd ~/projects/echo && docker compose up -d")
        else:
            fail(f"Docker error: {r.stderr.strip()[:80]}")
            record("docker", False, "docker error")
    except FileNotFoundError:
        fail("Docker not installed")
        record("docker", False, "not installed")
    except subprocess.TimeoutExpired:
        fail("Docker timed out")
        record("docker", False, "timeout")


def _check_docker_container(name: str, service: str):
    try:
        r = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", name],
            capture_output=True, text=True, timeout=5
        )
        status = r.stdout.strip()
        if status == "running":
            ok(f"{service} container '{name}' is running")
            record(service, True, f"container: {name}")
        else:
            fail(f"{service} container '{name}' status: {status}")
            record(service, False, f"status: {status}")
    except Exception as e:
        fail(f"Cannot check container: {e}")
        record(service, False, str(e))


async def check_local_api():
    header("Melodio API (localhost:8000)")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://localhost:8000/health")
        if r.status_code == 200:
            ok("API server live — /health OK")
            record("local_api", True, "running")
        else:
            fail(f"HTTP {r.status_code}")
            record("local_api", False, f"HTTP {r.status_code}")
    except Exception:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get("http://localhost:8000/docs")
            if r.status_code == 200:
                ok("API server live — /docs reachable")
                record("local_api", True, "running (no /health)")
            else:
                fail("API server not responding")
                record("local_api", False, "not running")
        except Exception as e:
            fail(f"API server not running: {e}")
            record("local_api", False, "not running")


async def check_local_web():
    header("Melodio Web (localhost:3000)")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://localhost:3000")
        if r.status_code in [200, 307, 308]:
            ok("Web server live")
            record("local_web", True, "running")
        else:
            fail(f"HTTP {r.status_code}")
            record("local_web", False, f"HTTP {r.status_code}")
    except Exception as e:
        fail(f"Web server not running: {e}")
        record("local_web", False, "not running")


# ──────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────

def print_summary():
    print(f"\n\n{BOLD}{'═'*50}{RESET}")
    print(f"{BOLD}⚡ MELODIO CONNECTION REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')} PDT{RESET}")
    print(f"{'═'*50}\n")

    connected = {k: v for k, v in results.items() if v["connected"]}
    failed    = {k: v for k, v in results.items() if not v["connected"]}

    print(f"{GREEN}{BOLD}  CONNECTED ({len(connected)}){RESET}")
    for svc, data in connected.items():
        print(f"  {GREEN}✅ {svc.upper():<20}{RESET} {data['detail']}")

    if failed:
        print(f"\n{RED}{BOLD}  NEEDS ATTENTION ({len(failed)}){RESET}")
        for svc, data in failed.items():
            print(f"  {RED}❌ {svc.upper():<20}{RESET} {data['detail']}")

    total = len(results)
    score = len(connected)
    pct = int((score / total) * 100) if total else 0
    bar_filled = int(pct / 5)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)

    print(f"\n  {BOLD}Readiness: [{bar}] {pct}% ({score}/{total}){RESET}")

    if pct == 100:
        print(f"\n  {GREEN}{BOLD}🚀 ALL SYSTEMS GO — Ready for Railway deploy{RESET}")
    elif pct >= 75:
        print(f"\n  {YELLOW}{BOLD}⚡ MOSTLY READY — Fix remaining services then deploy{RESET}")
    elif pct >= 50:
        print(f"\n  {YELLOW}{BOLD}🔧 PARTIAL — Core services up, integrations needed{RESET}")
    else:
        print(f"\n  {RED}{BOLD}🛑 NOT READY — Critical services missing{RESET}")

    print(f"\n{'═'*50}\n")

    # Save JSON report
    report_path = ROOT / "infra" / "connection-report.json"
    with open(report_path, "w") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "score": f"{score}/{total}",
            "readiness_pct": pct,
            "services": results
        }, f, indent=2)
    info(f"Report saved: {report_path}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

async def run_all():
    print(f"\n{BOLD}{CYAN}⚡ MELODIO CONNECTION MANAGER — B (CEO){RESET}")
    print(f"{CYAN}Running autonomous connection checks...{RESET}\n")

    # Run all checks concurrently where safe
    await asyncio.gather(
        check_docker(),
        check_local_api(),
        check_local_web(),
        check_postgres(),
        check_redis(),
        return_exceptions=True
    )

    await asyncio.gather(
        check_stripe(),
        check_anthropic(),
        check_openai(),
        check_spotify(),
        check_youtube(),
        check_sendgrid(),
        check_whatsapp(),
        check_persona(),
        check_aws_s3(),
        check_chartmetric(),
        check_railway(),
        return_exceptions=True
    )

    print_summary()


if __name__ == "__main__":
    asyncio.run(run_all())
