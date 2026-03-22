from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import redis.asyncio as aioredis
from dotenv import load_dotenv

from database import engine
from routers import auth, artists, releases, points, agents, hub, finance, legal, analytics, distribution, deal_room, songwriters
from routers.digital_merch import router as digital_merch_router
from routers.payments import router as payments_router
from routers.fan_intelligence import router as fan_intelligence_router
from routers.artist_intelligence import router as artist_intelligence_router
from routers.connections import router as connections_router
from routers.whatsapp import router as whatsapp_router
from routers.waitlist import router as waitlist_router
from routers.growth import router as growth_router

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await aioredis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    yield
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
