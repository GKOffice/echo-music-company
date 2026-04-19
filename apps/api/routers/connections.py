"""
Melodio Connection Manager — API Router
Exposes /api/v1/connections/status and /api/v1/connections/check
B (CEO) can call this at any time to get real-time service status.
"""

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
import httpx
import os
import subprocess
import json
from datetime import datetime, timezone
from pathlib import Path

router = APIRouter()

ROOT = Path(__file__).parent.parent.parent.parent  # ~/projects/echo
REPORT_PATH = ROOT / "infra" / "connection-report.json"


async def _test_service(name: str, coro) -> dict:
    try:
        result = await asyncio.wait_for(coro, timeout=8)
        return {"service": name, "connected": result[0], "detail": result[1]}
    except asyncio.TimeoutError:
        return {"service": name, "connected": False, "detail": "timeout"}
    except Exception as e:
        return {"service": name, "connected": False, "detail": str(e)[:100]}


async def _check_stripe():
    key = os.getenv("STRIPE_SECRET_KEY", "")
    if not key:
        return False, "not configured"
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get("https://api.stripe.com/v1/balance", auth=(key, ""))
    mode = "LIVE" if key.startswith("sk_live") else "TEST"
    return r.status_code == 200, f"{mode} mode" if r.status_code == 200 else f"HTTP {r.status_code}"


async def _check_anthropic():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return False, "not configured"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-3-haiku-20240307", "max_tokens": 5, "messages": [{"role": "user", "content": "ping"}]}
        )
    return r.status_code == 200, "claude-3-haiku OK" if r.status_code == 200 else f"HTTP {r.status_code}"


async def _check_spotify():
    cid = os.getenv("SPOTIFY_CLIENT_ID", "")
    secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    if not cid or not secret:
        return False, "not configured"
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.post("https://accounts.spotify.com/api/token",
                              data={"grant_type": "client_credentials"}, auth=(cid, secret))
    return r.status_code == 200, "token acquired" if r.status_code == 200 else f"HTTP {r.status_code}"


async def _check_redis():
    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(url, socket_timeout=3)
        await r.ping()
        info = await r.info("server")
        v = info.get("redis_version", "unknown")
        await r.aclose()
        return True, f"Redis {v}"
    except Exception as e:
        return False, str(e)


async def _check_local_api():
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            r = await client.get("http://localhost:8000/health")
        return r.status_code == 200, "running"
    except Exception:
        try:
            async with httpx.AsyncClient(timeout=4) as client:
                r = await client.get("http://localhost:8000/docs")
            return r.status_code == 200, "running (no /health)"
        except:
            return False, "not running"


async def _check_postgres():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return False, "DATABASE_URL not set"
    try:
        import asyncpg
        pg_url = url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncio.wait_for(asyncpg.connect(pg_url), timeout=5)
        v = await conn.fetchval("SELECT version()")
        await conn.close()
        return True, v.split(",")[0]
    except Exception as e:
        return False, str(e)[:80]


async def run_all_checks() -> dict:
    checks = await asyncio.gather(
        _test_service("postgres", _check_postgres()),
        _test_service("redis", _check_redis()),
        _test_service("stripe", _check_stripe()),
        _test_service("anthropic", _check_anthropic()),
        _test_service("spotify", _check_spotify()),
        _test_service("local_api", _check_local_api()),
    )

    services = {c["service"]: {"connected": c["connected"], "detail": c["detail"]} for c in checks}
    connected = sum(1 for c in checks if c["connected"])
    total = len(checks)
    pct = int((connected / total) * 100) if total else 0

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "score": f"{connected}/{total}",
        "readiness_pct": pct,
        "ready_for_deploy": pct >= 80,
        "services": services
    }

    # Persist to disk
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    return report


@router.get("/status")
async def connection_status():
    """Return last saved connection report. Auto-runs check if no report exists."""
    if REPORT_PATH.exists():
        with open(REPORT_PATH) as f:
            return JSONResponse(json.load(f))
    # No cached report — run checks now and return
    report = await run_all_checks()
    return JSONResponse(report)


@router.post("/check")
async def run_connection_check(background_tasks: BackgroundTasks):
    """Trigger a full live connection check. Returns results immediately."""
    report = await run_all_checks()
    return JSONResponse(report)


@router.get("/health")
async def health_summary():
    """Quick readiness summary — no live checks."""
    if REPORT_PATH.exists():
        with open(REPORT_PATH) as f:
            data = json.load(f)
        return {
            "readiness_pct": data.get("readiness_pct", 0),
            "score": data.get("score", "0/0"),
            "ready_for_deploy": data.get("ready_for_deploy", False),
            "last_checked": data.get("generated_at")
        }
    return {"readiness_pct": 0, "score": "0/0", "ready_for_deploy": False, "last_checked": None}
