from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging
import httpx
import redis.asyncio as aioredis
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import engine

logger = logging.getLogger(__name__)
from routers import auth, artists, releases, points, agents, hub, finance, legal, analytics, distribution, deal_room, songwriters
from routers.digital_merch import router as digital_merch_router
from routers.payments import router as payments_router
from routers.fan_intelligence import router as fan_intelligence_router
from routers.artist_intelligence import router as artist_intelligence_router
from routers.connections import router as connections_router
from routers.whatsapp import router as whatsapp_router
from routers.waitlist import router as waitlist_router
from routers.growth import router as growth_router
from routers.onboarding import router as onboarding_router
from routers.release_pipeline import router as release_pipeline_router
from routers.admin import router as admin_router
from routers.kyc import router as kyc_router
from routers.fan_economy import router as fan_economy_router

load_dotenv()

# ─── Sentry (no-op if SENTRY_DSN not set) ────────────────────────────────────────────
_sentry_dsn = os.getenv("SENTRY_DSN", "")
if _sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "development"),
    )

REDIS_URL = os.getenv("REDIS_URL", "redis://:melodio_redis_2026@localhost:6379")


# ─── Quarterly Payout Scheduler ───────────────────────────────────────────────────
async def trigger_quarterly_payouts():
    """Fires Jan 15, Apr 15, Jul 15, Oct 15 at 09:00 UTC to process point holder payouts."""
    logger.info("[scheduler] Quarterly payout triggered — firing /api/v1/points/payouts/process")
    service_token = os.getenv("SERVICE_TOKEN", "")
    api_url = os.getenv("INTERNAL_API_URL", "http://localhost:8000")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{api_url}/api/v1/points/payouts/process",
                headers={"Authorization": f"Bearer {service_token}", "X-Service": "scheduler"},
            )
        logger.info(f"[scheduler] Quarterly payout response: {resp.status_code}")
    except Exception as e:
        logger.error(f"[scheduler] Quarterly payout failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await aioredis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )

    # Start quarterly payout scheduler (production only)
    scheduler = AsyncIOScheduler()
    if os.getenv("ENVIRONMENT") == "production":
        scheduler.add_job(
            trigger_quarterly_payouts,
            trigger="cron",
            month="1,4,7,10",
            day=15,
            hour=9,
            minute=0,
            id="quarterly_payouts",
        )
        scheduler.start()
        logger.info("[scheduler] Quarterly payout cron started (Jan/Apr/Jul/Oct 15 @ 09:00 UTC)")
    app.state.scheduler = scheduler

    yield

    if scheduler.running:
        scheduler.shutdown(wait=False)
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(
    title="ECHO API",
    description="ECHO — Autonomous AI Music Company API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

ALLOWED_ORIGINS = [
    "https://melodio.io",
    "https://www.melodio.io",
    "https://web-production-6c66b.up.railway.app",
]
# In development, also allow localhost
if os.getenv("ENVIRONMENT") != "production":
    ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(artists.router, prefix="/api/v1/artists", tags=["artists"])
app.include_router(releases.router, prefix="/api/v1/releases", tags=["releases"])
app.include_router(points.router, prefix="/api/v1/points", tags=["points"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(hub.router, prefix="/api/v1/hub", tags=["hub"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["finance"])
app.include_router(legal.router, prefix="/api/v1/legal", tags=["legal"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(distribution.router, prefix="/api/v1/distribution", tags=["distribution"])
app.include_router(deal_room.router, prefix="/api/v1/deal-room", tags=["deal-room"])
app.include_router(songwriters.router, prefix="/api/v1/songwriters", tags=["songwriters"])
app.include_router(digital_merch_router, prefix="/api/v1/digital-merch", tags=["digital-merch"])
app.include_router(payments_router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(fan_intelligence_router, prefix="/api/v1/fan-intelligence", tags=["fan-intelligence"])
app.include_router(artist_intelligence_router, prefix="/api/v1/intelligence", tags=["artist-intelligence"])
app.include_router(connections_router, prefix="/api/v1/connections", tags=["connections"])
app.include_router(whatsapp_router)
app.include_router(waitlist_router, prefix="/api/v1/waitlist", tags=["waitlist"])
app.include_router(growth_router, prefix="/api/v1/growth", tags=["growth"])
app.include_router(onboarding_router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(release_pipeline_router, prefix="/api/v1/pipeline", tags=["pipeline"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(kyc_router, prefix="/api/v1/kyc", tags=["kyc"])
app.include_router(fan_economy_router, prefix="/api/v1/fan-economy", tags=["fan-economy"])


@app.get("/health", tags=["system"])
async def health_check():
    try:
        redis_ok = await app.state.redis.ping()
    except Exception:
        redis_ok = False

    return JSONResponse(
        content={
            "status": "ok",
            "service": "echo-api",
            "version": "0.1.0",
            "redis": "ok" if redis_ok else "error",
        }
    )


@app.get("/", tags=["system"])
async def root():
    return {"message": "ECHO API", "docs": "/docs"}
