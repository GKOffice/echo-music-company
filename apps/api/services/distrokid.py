"""
DistroKid Distribution Service
──────────────────────────────
TODO: DistroKid does not expose a publicly documented REST API as of 2026.
      This module implements a mock interface that matches the expected contract.
      All calls are logged and return realistic stub data.
      When DistroKid opens API access (or we get partner credentials),
      swap the mock implementations for real HTTP calls.
"""

import os
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DISTROKID_API_KEY = os.getenv("DISTROKID_API_KEY", "")
BASE_URL = "https://app.distrokid.com/api/"

# TODO: Replace with real httpx client when API is available
# _client = httpx.AsyncClient(
#     base_url=BASE_URL,
#     headers={"Authorization": f"Bearer {DISTROKID_API_KEY}"},
#     timeout=30.0,
# )


async def submit_release(
    artist_name: str,
    track_title: str,
    audio_url: str,
    cover_url: str,
    release_date: str,
    isrc: Optional[str] = None,
) -> dict:
    """
    Submit a release to DistroKid for distribution across DSPs.

    TODO: Wire to real DistroKid API endpoint when available.
    Expected real endpoint: POST {BASE_URL}releases
    """
    payload = {
        "artist_name": artist_name,
        "track_title": track_title,
        "audio_url": audio_url,
        "cover_url": cover_url,
        "release_date": release_date,
        "isrc": isrc,
    }

    logger.info("[DistroKid MOCK] submit_release → %s - '%s'", artist_name, track_title)
    logger.debug("[DistroKid MOCK] payload: %s", payload)

    # TODO: Real implementation:
    # resp = await _client.post("releases", json=payload)
    # resp.raise_for_status()
    # return resp.json()

    distrokid_id = f"dk_{uuid.uuid4().hex[:16]}"
    return {
        "success": True,
        "distrokid_id": distrokid_id,
        "status": "processing",
        "message": f"Release '{track_title}' by {artist_name} queued for distribution",
        "estimated_live": "3-5 business days",
        "mock": True,
    }


async def get_release_status(distrokid_id: str) -> dict:
    """
    Check distribution status for a release.

    TODO: Wire to real DistroKid API endpoint when available.
    Expected real endpoint: GET {BASE_URL}releases/{distrokid_id}/status
    """
    logger.info("[DistroKid MOCK] get_release_status → %s", distrokid_id)

    # TODO: Real implementation:
    # resp = await _client.get(f"releases/{distrokid_id}/status")
    # resp.raise_for_status()
    # return resp.json()

    return {
        "distrokid_id": distrokid_id,
        "status": "live",
        "platforms": {
            "spotify": {"status": "live", "url": None},
            "apple_music": {"status": "live", "url": None},
            "amazon_music": {"status": "processing", "url": None},
            "tidal": {"status": "live", "url": None},
            "youtube_music": {"status": "processing", "url": None},
            "deezer": {"status": "live", "url": None},
            "tiktok_sound": {"status": "pending", "url": None},
            "instagram_music": {"status": "pending", "url": None},
        },
        "mock": True,
    }


async def get_streaming_stats(distrokid_id: str) -> dict:
    """
    Pull per-DSP stream counts for a release.

    TODO: Wire to real DistroKid API endpoint when available.
    Expected real endpoint: GET {BASE_URL}releases/{distrokid_id}/stats
    """
    logger.info("[DistroKid MOCK] get_streaming_stats → %s", distrokid_id)

    # TODO: Real implementation:
    # resp = await _client.get(f"releases/{distrokid_id}/stats")
    # resp.raise_for_status()
    # return resp.json()

    return {
        "distrokid_id": distrokid_id,
        "total_streams": 0,
        "platforms": {
            "spotify": {"streams": 0, "saves": 0, "listeners": 0},
            "apple_music": {"streams": 0, "saves": 0, "listeners": 0},
            "amazon_music": {"streams": 0, "saves": 0, "listeners": 0},
            "tidal": {"streams": 0, "saves": 0, "listeners": 0},
            "youtube_music": {"streams": 0, "saves": 0, "listeners": 0},
            "deezer": {"streams": 0, "saves": 0, "listeners": 0},
            "tiktok_sound": {"streams": 0, "uses": 0},
            "instagram_music": {"streams": 0, "uses": 0},
        },
        "period": "all_time",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "mock": True,
    }


async def list_releases(artist_name: str) -> dict:
    """
    Get all releases for an artist from DistroKid.

    TODO: Wire to real DistroKid API endpoint when available.
    Expected real endpoint: GET {BASE_URL}releases?artist={artist_name}
    """
    logger.info("[DistroKid MOCK] list_releases → %s", artist_name)

    # TODO: Real implementation:
    # resp = await _client.get("releases", params={"artist": artist_name})
    # resp.raise_for_status()
    # return resp.json()

    return {
        "artist_name": artist_name,
        "releases": [],
        "total": 0,
        "mock": True,
    }
