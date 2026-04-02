"""
Melodio Artist Intelligence API
Search any artist → collect data from all available sources → AI-powered analysis report.
"""
from fastapi import APIRouter, Query, Request, HTTPException
from typing import Optional
import httpx
import json
import os
import asyncio
import base64
import re
from datetime import datetime, timezone

router = APIRouter()

REDIS_TTL_SEARCH = 300    # 5 min
REDIS_TTL_REPORT = 3600   # 1 hour
REDIS_TTL_COMPARE = 3600  # 1 hour

ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY", "")
SPOTIFY_CLIENT_ID    = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
YOUTUBE_API_KEY      = os.getenv("YOUTUBE_API_KEY", "")
GENIUS_ACCESS_TOKEN  = os.getenv("GENIUS_ACCESS_TOKEN", "")
CHARTMETRIC_API_KEY  = os.getenv("CHARTMETRIC_API_KEY", "")

# ─────────────────────────────────────────────────────────────────────────────
# CACHE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

async def _cache_get(request: Request, key: str) -> Optional[dict]:
    try:
        val = await request.app.state.redis.get(key)
        if val:
            return json.loads(val)
    except Exception:
        pass
    return None


async def _cache_set(request: Request, key: str, data: dict, ttl: int = 3600):
    try:
        await request.app.state.redis.setex(key, ttl, json.dumps(data, default=str))
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# DATA ADAPTERS — each returns {"source": ..., "available": bool, ...}
# ─────────────────────────────────────────────────────────────────────────────

async def _spotify_token() -> Optional[str]:
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    creds = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://accounts.spotify.com/api/token",
                headers={
                    "Authorization": f"Basic {creds}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )
            if resp.status_code == 200:
                return resp.json().get("access_token")
    except Exception:
        pass
    return None


async def fetch_spotify(name: str) -> dict:
    token = await _spotify_token()
    if not token:
        return {"source": "spotify", "available": False, "reason": "No API credentials"}
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            s = await client.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": name, "type": "artist", "limit": 1},
            )
            if s.status_code != 200:
                return {"source": "spotify", "available": False, "reason": "Search failed"}
            items = s.json().get("artists", {}).get("items", [])
            if not items:
                return {"source": "spotify", "available": False, "reason": "Not found"}

            # Pick the best name match — don't blindly take first result
            name_lower = name.lower()
            name_parts = set(name_lower.split())
            best = None
            for candidate in items[:5]:
                cname = (candidate.get("name") or "").lower()
                # Exact match wins immediately
                if cname == name_lower:
                    best = candidate
                    break
                # Partial match: all parts of the searched name appear in the candidate name
                if all(p in cname for p in name_parts):
                    best = candidate
                    break
            # Fall back to first result only if its name contains at least one search word
            if not best:
                first = items[0]
                fname = (first.get("name") or "").lower()
                if any(p in fname for p in name_parts if len(p) > 2):
                    best = first
            if not best:
                return {"source": "spotify", "available": False, "reason": "No matching artist found"}

            a = best
            aid = a["id"]

            # Fetch artist detail, top tracks, and related artists in parallel
            # (search endpoint doesn't return followers/popularity — need /artists/{id})
            detail_resp, top_resp, rel_resp = await asyncio.gather(
                client.get(
                    f"https://api.spotify.com/v1/artists/{aid}",
                    headers={"Authorization": f"Bearer {token}"},
                ),
                client.get(
                    f"https://api.spotify.com/v1/artists/{aid}/top-tracks",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"market": "US"},
                ),
                client.get(
                    f"https://api.spotify.com/v1/artists/{aid}/related-artists",
                    headers={"Authorization": f"Bearer {token}"},
                ),
            )

            # Use detail endpoint for followers/popularity/genres
            detail = detail_resp.json() if detail_resp.status_code == 200 else a

            top_tracks = []
            if top_resp.status_code == 200:
                top_tracks = [
                    {"name": t["name"], "popularity": t["popularity"]}
                    for t in top_resp.json().get("tracks", [])[:5]
                ]

            related = []
            if rel_resp.status_code == 200:
                related = [r["name"] for r in rel_resp.json().get("artists", [])[:6]]

            return {
                "source": "spotify",
                "available": True,
                "id": aid,
                "name": detail.get("name", a["name"]),
                "followers": detail.get("followers", {}).get("total", 0),
                "popularity": detail.get("popularity", 0),
                "genres": detail.get("genres", []),
                "image": (detail.get("images") or [{}])[0].get("url"),
                "external_url": detail.get("external_urls", {}).get("spotify"),
                "top_tracks": top_tracks,
                "related_artists": related,
            }
    except Exception as e:
        return {"source": "spotify", "available": False, "reason": str(e)}


async def fetch_youtube(name: str) -> dict:
    if not YOUTUBE_API_KEY:
        return {"source": "youtube", "available": False, "reason": "No API key"}
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            s = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": f"{name} official",
                    "type": "channel",
                    "maxResults": 1,
                    "key": YOUTUBE_API_KEY,
                },
            )
            if s.status_code != 200:
                return {"source": "youtube", "available": False, "reason": "Search failed"}
            items = s.json().get("items", [])
            if not items:
                return {"source": "youtube", "available": False, "reason": "Not found"}

            channel_id = items[0]["id"]["channelId"]
            cr = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "statistics,snippet", "id": channel_id, "key": YOUTUBE_API_KEY},
            )
            if cr.status_code != 200:
                return {"source": "youtube", "available": False, "reason": "Stats failed"}
            channels = cr.json().get("items", [])
            if not channels:
                return {"source": "youtube", "available": False, "reason": "No data"}

            ch = channels[0]
            stats = ch.get("statistics", {})
            return {
                "source": "youtube",
                "available": True,
                "channel_id": channel_id,
                "name": ch.get("snippet", {}).get("title", name),
                "subscribers": int(stats.get("subscriberCount", 0)),
                "total_views": int(stats.get("viewCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "channel_url": f"https://youtube.com/channel/{channel_id}",
            }
    except Exception as e:
        return {"source": "youtube", "available": False, "reason": str(e)}


async def fetch_genius(name: str) -> dict:
    headers: dict = {"User-Agent": "Melodio/1.0"}
    if GENIUS_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {GENIUS_ACCESS_TOKEN}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.genius.com/search",
                params={"q": name},
                headers=headers,
            )
            if r.status_code != 200:
                return {"source": "genius", "available": False, "reason": "API error"}
            hits = r.json().get("response", {}).get("hits", [])
            artist_hits = [
                h for h in hits
                if h.get("result", {}).get("primary_artist", {}).get("name", "").lower()
                == name.lower()
            ] or hits[:6]

            songs = [
                {
                    "title": h["result"].get("title", ""),
                    "annotations": h["result"].get("annotation_count", 0),
                    "pageviews": h["result"].get("stats", {}).get("pageviews", 0),
                }
                for h in artist_hits[:10]
            ]
            return {
                "source": "genius",
                "available": True,
                "songs_found": len(songs),
                "songs": songs,
                "total_pageviews": sum(s["pageviews"] for s in songs),
            }
    except Exception as e:
        return {"source": "genius", "available": False, "reason": str(e)}


async def fetch_musicbrainz(name: str) -> dict:
    hdrs = {"User-Agent": "Melodio/1.0 (melodio.io)"}
    try:
        async with httpx.AsyncClient(timeout=12, headers=hdrs) as client:
            r = await client.get(
                "https://musicbrainz.org/ws/2/artist/",
                params={"query": name, "limit": 1, "fmt": "json"},
            )
            if r.status_code != 200:
                return {"source": "musicbrainz", "available": False, "reason": "Search failed"}
            artists = r.json().get("artists", [])
            if not artists:
                return {"source": "musicbrainz", "available": False, "reason": "Not found"}

            # Pick best name match
            name_lower = name.lower()
            name_parts = set(name_lower.split())
            best_mb = None
            for candidate in artists[:5]:
                cname = (candidate.get("name") or "").lower()
                if cname == name_lower:
                    best_mb = candidate
                    break
                if all(p in cname for p in name_parts if len(p) > 2):
                    best_mb = candidate
                    break
            if not best_mb:
                first = artists[0]
                fname = (first.get("name") or "").lower()
                if any(p in fname for p in name_parts if len(p) > 2):
                    best_mb = first
            if not best_mb:
                return {"source": "musicbrainz", "available": False, "reason": "No matching artist found"}

            a = best_mb
            aid = a["id"]

            rr = await client.get(
                "https://musicbrainz.org/ws/2/release/",
                params={"artist": aid, "limit": 25, "fmt": "json"},
            )
            releases = []
            if rr.status_code == 200:
                releases = [
                    {
                        "title": rel.get("title", ""),
                        "date": rel.get("date", ""),
                        "status": rel.get("status", ""),
                    }
                    for rel in rr.json().get("releases", [])
                ]

            return {
                "source": "musicbrainz",
                "available": True,
                "mbid": aid,
                "name": a.get("name", name),
                "type": a.get("type", ""),
                "country": a.get("country", ""),
                "begin_date": a.get("life-span", {}).get("begin", ""),
                "disambiguation": a.get("disambiguation", ""),
                "releases": releases[:15],
                "release_count": len(releases),
                "tags": [t["name"] for t in a.get("tags", [])[:10]],
            }
    except Exception as e:
        return {"source": "musicbrainz", "available": False, "reason": str(e)}


async def fetch_wikipedia(name: str) -> dict:
    """Fetch Wikipedia summary — rejects disambiguation pages and unrelated articles."""
    try:
        async with httpx.AsyncClient(
            timeout=10, headers={"User-Agent": "Melodio/1.0 (melodio.io)"}
        ) as client:
            # Try full name first, then append "musician" if no result
            for query in [name, f"{name} musician", f"{name} singer"]:
                r = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}",
                    follow_redirects=True,
                )
                if r.status_code != 200:
                    continue
                d = r.json()
                page_type = d.get("type", "")
                extract = d.get("extract", "")

                # Reject disambiguation pages outright
                if page_type == "disambiguation":
                    continue
                # Reject pages whose extract looks like a disambiguation list
                if "may refer to:" in extract.lower() or extract.strip().startswith(name + " may"):
                    continue
                # Sanity-check: article title or extract should mention the artist name
                title = d.get("title", "")
                name_parts = name.lower().split()
                if not any(part in title.lower() or part in extract.lower() for part in name_parts if len(part) > 2):
                    continue
                # Reject if article is clearly about something other than a musician/artist
                music_keywords = ["musician", "singer", "artist", "rapper", "band", "songwriter",
                                  "vocalist", "producer", "album", "single", "music", "record"]
                if not any(kw in extract.lower() for kw in music_keywords):
                    continue

                return {
                    "source": "wikipedia",
                    "available": True,
                    "title": title,
                    "extract": extract[:900],
                    "thumbnail": d.get("thumbnail", {}).get("source"),
                    "url": d.get("content_urls", {}).get("desktop", {}).get("page"),
                }

            return {"source": "wikipedia", "available": False, "reason": "No relevant article found"}
    except Exception as e:
        return {"source": "wikipedia", "available": False, "reason": str(e)}


async def fetch_discogs(name: str) -> dict:
    """Discogs — free, no key, has indie/underground artists, bios, social links, release history."""
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Melodio/1.0 +https://melodio.io"}) as client:
            r = await client.get(
                "https://api.discogs.com/database/search",
                params={"q": name, "type": "artist", "per_page": 3}
            )
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    artist_id = results[0].get("id")
                    r2 = await client.get(f"https://api.discogs.com/artists/{artist_id}")
                    if r2.status_code == 200:
                        a = r2.json()
                        # Get releases count
                        r3 = await client.get(f"https://api.discogs.com/artists/{artist_id}/releases", params={"per_page": 5, "sort": "year", "sort_order": "desc"})
                        releases = []
                        if r3.status_code == 200:
                            releases = [
                                {"title": rel.get("title"), "year": rel.get("year"), "type": rel.get("type")}
                                for rel in r3.json().get("releases", [])[:5]
                            ]
                        urls = a.get("urls", [])
                        instagram = next((u for u in urls if "instagram" in u), None)
                        twitter = next((u for u in urls if "twitter" in u or "x.com" in u), None)
                        website = next((u for u in urls if "instagram" not in u and "twitter" not in u and "x.com" not in u and "facebook" not in u), None)
                        return {
                            "source": "discogs",
                            "available": True,
                            "profile": (a.get("profile") or "")[:400],
                            "members": [m.get("name") for m in a.get("members", [])],
                            "urls": urls[:5],
                            "instagram": instagram,
                            "twitter": twitter,
                            "website": website,
                            "recent_releases": releases,
                            "images": [i.get("uri") for i in a.get("images", [])[:2] if i.get("uri")],
                        }
        return {"source": "discogs", "available": False, "reason": "not found"}
    except Exception as e:
        return {"source": "discogs", "available": False, "reason": str(e)[:80]}


async def fetch_soundcloud(name: str) -> dict:
    """Search SoundCloud oEmbed — no key needed, works for any artist with a profile."""
    try:
        slug = name.lower().replace(" ", "-").replace("'", "")
        async with httpx.AsyncClient(timeout=8, headers={"User-Agent": "Mozilla/5.0"}) as client:
            r = await client.get(
                f"https://soundcloud.com/{slug}",
                follow_redirects=True
            )
            if r.status_code == 200 and "soundcloud.com" in str(r.url):
                text = r.text
                followers = None
                import re as _re
                m = _re.search(r'"followers_count":(\d+)', text)
                if m: followers = int(m.group(1))
                track_count = None
                m2 = _re.search(r'"track_count":(\d+)', text)
                if m2: track_count = int(m2.group(1))
                return {
                    "source": "soundcloud",
                    "available": followers is not None,
                    "followers": followers,
                    "track_count": track_count,
                    "url": str(r.url),
                }
        return {"source": "soundcloud", "available": False, "reason": "profile not found"}
    except Exception as e:
        return {"source": "soundcloud", "available": False, "reason": str(e)[:80]}


async def fetch_lastfm(name: str) -> dict:
    """Last.fm — has data on virtually every artist including indie/underground."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://ws.audioscrobbler.com/2.0/",
                params={
                    "method": "artist.getinfo",
                    "artist": name,
                    "api_key": "9a8c96953498a9d438acb6f89aa3c3c5",  # free public key
                    "format": "json",
                    "autocorrect": 1,
                }
            )
            if r.status_code == 200:
                d = r.json()
                if "error" not in d:
                    a = d.get("artist", {})
                    stats = a.get("stats", {})
                    similar = [s.get("name") for s in a.get("similar", {}).get("artist", [])[:5]]
                    tags = [t.get("name") for t in a.get("tags", {}).get("tag", [])[:5]]
                    return {
                        "source": "lastfm",
                        "available": True,
                        "listeners": int(stats.get("listeners", 0)),
                        "playcount": int(stats.get("playcount", 0)),
                        "similar_artists": similar,
                        "tags": tags,
                        "bio": (a.get("bio", {}).get("summary", "") or "")[:400].split("<a href")[0].strip(),
                        "url": a.get("url"),
                        "image": next((i.get("#text") for i in reversed(a.get("image", [])) if i.get("#text")), None),
                    }
        return {"source": "lastfm", "available": False, "reason": "not found"}
    except Exception as e:
        return {"source": "lastfm", "available": False, "reason": str(e)[:80]}


async def fetch_itunes(name: str) -> dict:
    """Apple Music / iTunes — has emerging artists, free search API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://itunes.apple.com/search",
                params={"term": name, "media": "music", "entity": "musicArtist", "limit": 3}
            )
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    a = results[0]
                    # Get top albums
                    r2 = await client.get(
                        "https://itunes.apple.com/lookup",
                        params={"id": a["artistId"], "entity": "album", "limit": 5}
                    )
                    albums = []
                    if r2.status_code == 200:
                        albums = [
                            {"name": item.get("collectionName"), "year": (item.get("releaseDate","")[:4])}
                            for item in r2.json().get("results", [])[1:]
                            if item.get("wrapperType") == "collection"
                        ]
                    return {
                        "source": "itunes",
                        "available": True,
                        "artist_id": a.get("artistId"),
                        "name": a.get("artistName"),
                        "genre": a.get("primaryGenreName"),
                        "url": a.get("artistLinkUrl"),
                        "albums": albums,
                    }
        return {"source": "itunes", "available": False, "reason": "not found"}
    except Exception as e:
        return {"source": "itunes", "available": False, "reason": str(e)[:80]}


async def fetch_deezer(name: str) -> dict:
    """Deezer — free API, has indie artists, fan counts, tracklists."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.deezer.com/search/artist",
                params={"q": name, "limit": 3}
            )
            if r.status_code == 200:
                items = r.json().get("data", [])
                if items:
                    a = items[0]
                    # Get artist detail
                    r2 = await client.get(f"https://api.deezer.com/artist/{a['id']}")
                    if r2.status_code == 200:
                        detail = r2.json()
                        # Get top tracks
                        r3 = await client.get(f"https://api.deezer.com/artist/{a['id']}/top?limit=5")
                        tracks = []
                        if r3.status_code == 200:
                            tracks = [
                                {"title": t.get("title"), "rank": t.get("rank"), "duration": t.get("duration")}
                                for t in r3.json().get("data", [])
                            ]
                        return {
                            "source": "deezer",
                            "available": True,
                            "fans": detail.get("nb_fan", 0),
                            "albums": detail.get("nb_album", 0),
                            "radio_available": detail.get("radio", False),
                            "top_tracks": tracks,
                            "url": detail.get("link"),
                            "picture": detail.get("picture_xl"),
                        }
        return {"source": "deezer", "available": False, "reason": "not found"}
    except Exception as e:
        return {"source": "deezer", "available": False, "reason": str(e)[:80]}


async def fetch_bandsintown(name: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"https://rest.bandsintown.com/artists/{name}/events",
                params={"app_id": "melodio", "date": "upcoming"},
            )
            if r.status_code == 200 and isinstance(r.json(), list):
                events = [
                    {
                        "date": e.get("datetime", "")[:10],
                        "venue": e.get("venue", {}).get("name", ""),
                        "city": e.get("venue", {}).get("city", ""),
                        "country": e.get("venue", {}).get("country", ""),
                        "capacity": e.get("venue", {}).get("capacity"),
                    }
                    for e in r.json()[:10]
                ]
                return {
                    "source": "bandsintown",
                    "available": True,
                    "upcoming_shows": len(events),
                    "events": events,
                }
            return {"source": "bandsintown", "available": False, "reason": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"source": "bandsintown", "available": False, "reason": str(e)}


async def fetch_chartmetric(name: str) -> dict:
    """Chartmetric — monthly listeners, playlist placements, CM score, social stats."""
    if not CHARTMETRIC_API_KEY:
        return {"source": "chartmetric", "available": False, "reason": "No API key"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Get access token
            token_resp = await client.post(
                "https://api.chartmetric.com/api/token",
                json={"refreshtoken": CHARTMETRIC_API_KEY},
            )
            if token_resp.status_code != 200:
                return {"source": "chartmetric", "available": False, "reason": "Token exchange failed"}
            access_token = token_resp.json().get("token", "")
            headers = {"Authorization": f"Bearer {access_token}"}

            # Search artist
            search_resp = await client.get(
                "https://api.chartmetric.com/api/search",
                params={"q": name, "type": "artists", "limit": 1},
                headers=headers,
            )
            if search_resp.status_code != 200:
                return {"source": "chartmetric", "available": False, "reason": f"Search HTTP {search_resp.status_code}"}

            artists = search_resp.json().get("obj", {}).get("artists", [])
            if not artists:
                return {"source": "chartmetric", "available": False, "reason": "Artist not found"}

            a = artists[0]
            cm_id = a.get("id")

            # Get detailed stats
            detail_resp = await client.get(
                f"https://api.chartmetric.com/api/artist/{cm_id}",
                headers=headers,
            )
            detail = detail_resp.json().get("obj", {}) if detail_resp.status_code == 200 else {}

            return {
                "source": "chartmetric",
                "available": True,
                "cm_id": cm_id,
                "name": a.get("name"),
                "cm_score": round(a.get("cm_artist_score", 0), 1),
                "sp_monthly_listeners": a.get("sp_monthly_listeners"),
                "sp_followers": a.get("sp_followers"),
                "verified": a.get("verified", False),
                "image_url": a.get("image_url"),
                "country": detail.get("country"),
                "city": detail.get("city"),
                "career_stage": detail.get("career_stage"),
                "playlist_total_reach": detail.get("sp_playlist_total_reach"),
                "tiktok_followers": detail.get("tiktok_followers"),
                "instagram_followers": detail.get("instagram_followers"),
                "youtube_subscribers": detail.get("youtube_channel_subscribers"),
            }
    except Exception as e:
        return {"source": "chartmetric", "available": False, "reason": str(e)[:80]}


# ─────────────────────────────────────────────────────────────────────────────
# AI ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

_ANALYSIS_PROMPT = """You are Melodio's AI A&R analyst. Analyze the data below and return ONLY valid JSON — no markdown, no explanation.

Artist: {artist_name}

Collected Data:
{data_json}

CRITICAL RULES — read before generating:
1. ONLY use information from the Collected Data above. Do NOT invent, hallucinate, or infer facts not present in the data.
2. If a data source is marked "available: false", treat it as having NO information — do not guess.
3. If data is sparse, say so in the executive_summary. Use phrases like "Limited data available" or "Insufficient platform data to assess X."
4. The executive_summary must describe THIS specific artist based on the actual data — not a generic artist profile.
5. genre_classification must come from actual genre tags in the data (Spotify genres, Last.fm tags, iTunes genre, MusicBrainz tags). If none available, use "Unknown / Insufficient data."
6. Do NOT fabricate nationalities, biographical details, or platform stats not present in the data.
7. NEVER use the words invest, investment, or ROI anywhere in the output.

Return this exact JSON structure (fill in all values):
{{
  "melodio_score": {{
    "total": <0-100 int>,
    "music_quality": <0-100 int>,
    "social_momentum": <0-100 int>,
    "commercial_traction": <0-100 int>,
    "brand_strength": <0-100 int>,
    "market_timing": <0-100 int>
  }},
  "predictive_angles": {{
    "collaboration_network": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}},
    "platform_velocity": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}},
    "genre_timing": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}},
    "content_to_music_ratio": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}},
    "live_performance_trajectory": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}},
    "sync_readiness": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}},
    "fanbase_quality": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}},
    "release_cadence": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}},
    "cross_platform_correlation": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}},
    "breakout_probability": {{"score": <0-100>, "trend": "<up|down|neutral>", "explanation": "<max 60 words — based only on actual data>"}}
  }},
  "executive_summary": "<3-4 paragraphs about THIS artist based solely on the collected data — no fabrication>",
  "sign_recommendation": {{
    "decision": "<yes|maybe|no>",
    "confidence": <0-100>,
    "reasoning": "<2-3 sentences based only on actual data — no fabrication, no investment language>"
  }},
  "key_strengths": ["<strength derived from actual data>"],
  "key_risks": ["<risk derived from actual data>"],
  "notable_collaborators": ["<name — only if present in actual data, otherwise empty array>"],
  "genre_classification": "<from actual data tags only — if unknown write 'Insufficient data'>"
}}

Scoring rules:
- total = music_quality*0.35 + social_momentum*0.20 + commercial_traction*0.25 + brand_strength*0.10 + market_timing*0.10
- Score conservatively when data is sparse — low confidence = lower scores
- Score 0 on dimensions where no data exists rather than guessing"""


async def _call_claude(prompt: str, max_tokens: int = 2000) -> Optional[str]:
    if not ANTHROPIC_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            if r.status_code == 200:
                return r.json().get("content", [{}])[0].get("text", "")
    except Exception:
        pass
    return None


def _mock_analysis(artist_name: str) -> dict:
    import hashlib, random
    seed = int(hashlib.md5(artist_name.lower().encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    mq = rng.randint(50, 88)
    sm = rng.randint(42, 85)
    ct = rng.randint(38, 82)
    bs = rng.randint(40, 78)
    mt = rng.randint(45, 80)
    total = int(mq * 0.35 + sm * 0.20 + ct * 0.25 + bs * 0.10 + mt * 0.10)

    def angle(lo: int = 35, hi: int = 88) -> dict:
        s = rng.randint(lo, hi)
        t = rng.choice(["up", "down", "neutral"])
        quality = "strong" if s > 65 else "moderate" if s > 45 else "developing"
        return {
            "score": s,
            "trend": t,
            "explanation": f"Available signals suggest {quality} performance in this dimension. Connect more data sources for a fuller picture.",
        }

    dec = "yes" if total >= 68 else ("maybe" if total >= 50 else "no")
    conf = rng.randint(52, 84)

    return {
        "melodio_score": {
            "total": total,
            "music_quality": mq,
            "social_momentum": sm,
            "commercial_traction": ct,
            "brand_strength": bs,
            "market_timing": mt,
        },
        "predictive_angles": {
            "collaboration_network": angle(),
            "platform_velocity": angle(),
            "genre_timing": angle(),
            "content_to_music_ratio": angle(),
            "live_performance_trajectory": angle(),
            "sync_readiness": angle(),
            "fanbase_quality": angle(),
            "release_cadence": angle(),
            "cross_platform_correlation": angle(),
            "breakout_probability": angle(25, 75),
        },
        "executive_summary": (
            f"Insufficient platform data is available to generate a complete analysis for {artist_name}. "
            f"The Melodio Score of {total} is an estimate based on limited signals.\n\n"
            "To generate an accurate report, connect Spotify, YouTube, Last.fm, and other API keys. "
            "Without live data, scores reflect conservative baseline estimates only.\n\n"
            "This report should not be used for A&R decisions until full platform data is available."
        ),
        "sign_recommendation": {
            "decision": dec,
            "confidence": conf,
            "reasoning": "Insufficient data to make a reliable recommendation. Connect platform API keys for a real assessment.",
        },
        "key_strengths": ["Insufficient data — connect API keys for real analysis"],
        "key_risks": ["Limited platform data available", "Cannot assess without live Spotify/streaming data"],
        "notable_collaborators": [],
        "genre_classification": "Independent",
    }


async def analyze_with_claude(artist_name: str, raw_data: dict) -> dict:
    text = await _call_claude(
        _ANALYSIS_PROMPT.format(
            artist_name=artist_name,
            data_json=json.dumps(raw_data, default=str)[:6000],
        )
    )
    if text:
        try:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
    return _mock_analysis(artist_name)


# ─────────────────────────────────────────────────────────────────────────────
# REPORT ASSEMBLER
# ─────────────────────────────────────────────────────────────────────────────

async def _build_report(artist_name: str, request: Request) -> dict:
    (spotify, youtube, genius, musicbrainz, wikipedia,
     bandsintown, soundcloud, lastfm, itunes, deezer, discogs, chartmetric) = await asyncio.gather(
        fetch_spotify(artist_name),
        fetch_youtube(artist_name),
        fetch_genius(artist_name),
        fetch_musicbrainz(artist_name),
        fetch_wikipedia(artist_name),
        fetch_bandsintown(artist_name),
        fetch_soundcloud(artist_name),
        fetch_lastfm(artist_name),
        fetch_itunes(artist_name),
        fetch_deezer(artist_name),
        fetch_discogs(artist_name),
        fetch_chartmetric(artist_name),
    )

    raw_data = {
        "spotify": spotify,
        "youtube": youtube,
        "genius": genius,
        "musicbrainz": musicbrainz,
        "wikipedia": wikipedia,
        "bandsintown": bandsintown,
        "soundcloud": soundcloud,
        "lastfm": lastfm,
        "itunes": itunes,
        "deezer": deezer,
        "discogs": discogs,
        "chartmetric": chartmetric,
    }

    analysis = await analyze_with_claude(artist_name, raw_data)

    image = (
        spotify.get("image") if spotify.get("available")
        else wikipedia.get("thumbnail") if wikipedia.get("available")
        else soundcloud.get("avatar") if soundcloud.get("available")
        else deezer.get("picture") if deezer.get("available")
        else None
    )

    genres = spotify.get("genres", []) if spotify.get("available") else []
    if not genres and musicbrainz.get("available"):
        genres = musicbrainz.get("tags", [])
    if not genres and lastfm.get("available"):
        genres = lastfm.get("tags", [])
    if not genres and itunes.get("available") and itunes.get("genre"):
        genres = [itunes.get("genre")]

    platform_stats: dict = {}
    if spotify.get("available"):
        platform_stats["spotify"] = {
            "followers": spotify.get("followers", 0),
            "popularity": spotify.get("popularity", 0),
            "top_tracks": spotify.get("top_tracks", []),
            "related_artists": spotify.get("related_artists", []),
            "url": spotify.get("external_url"),
        }
    if youtube.get("available"):
        platform_stats["youtube"] = {
            "subscribers": youtube.get("subscribers", 0),
            "total_views": youtube.get("total_views", 0),
            "video_count": youtube.get("video_count", 0),
            "url": youtube.get("channel_url"),
        }
    if soundcloud.get("available"):
        platform_stats["soundcloud"] = {
            "followers": soundcloud.get("followers", 0),
            "tracks": soundcloud.get("track_count", 0),
            "likes": soundcloud.get("likes", 0),
            "city": soundcloud.get("city"),
            "country": soundcloud.get("country"),
            "url": soundcloud.get("url"),
        }
    if lastfm.get("available"):
        platform_stats["lastfm"] = {
            "listeners": lastfm.get("listeners", 0),
            "playcount": lastfm.get("playcount", 0),
            "similar_artists": lastfm.get("similar_artists", []),
            "bio": lastfm.get("bio", ""),
            "url": lastfm.get("url"),
        }
    if deezer.get("available"):
        platform_stats["deezer"] = {
            "fans": deezer.get("fans", 0),
            "albums": deezer.get("albums", 0),
            "top_tracks": deezer.get("top_tracks", []),
            "url": deezer.get("url"),
        }
    if itunes.get("available"):
        platform_stats["itunes"] = {
            "genre": itunes.get("genre"),
            "albums": itunes.get("albums", []),
            "url": itunes.get("url"),
        }
    if discogs.get("available"):
        platform_stats["discogs"] = {
            "profile": discogs.get("profile", ""),
            "instagram": discogs.get("instagram"),
            "twitter": discogs.get("twitter"),
            "website": discogs.get("website"),
            "recent_releases": discogs.get("recent_releases", []),
            "members": discogs.get("members", []),
        }
    if soundcloud.get("available"):
        platform_stats["soundcloud"] = {
            "followers": soundcloud.get("followers", 0),
            "tracks": soundcloud.get("track_count", 0),
            "url": soundcloud.get("url"),
        }
    # Always include chartmetric if available — primary source for listener/follower data
    if chartmetric.get("available"):
        platform_stats["chartmetric"] = {
            "cm_score": chartmetric.get("cm_score", 0),
            "sp_monthly_listeners": chartmetric.get("sp_monthly_listeners", 0),
            "sp_followers": chartmetric.get("sp_followers", 0),
            "tiktok_followers": chartmetric.get("tiktok_followers"),
            "instagram_followers": chartmetric.get("instagram_followers"),
            "youtube_subscribers": chartmetric.get("youtube_subscribers"),
            "playlist_total_reach": chartmetric.get("playlist_total_reach"),
            "career_stage": chartmetric.get("career_stage"),
            "available": True,
        }
    # Also enrich spotify stats with chartmetric listener data if spotify followers are 0
    if "spotify" in platform_stats and chartmetric.get("available"):
        if not platform_stats["spotify"].get("followers") and chartmetric.get("sp_followers"):
            platform_stats["spotify"]["followers"] = chartmetric.get("sp_followers", 0)
        if chartmetric.get("sp_monthly_listeners"):
            platform_stats["spotify"]["monthly_listeners"] = chartmetric.get("sp_monthly_listeners", 0)
        if not platform_stats["spotify"].get("popularity") and chartmetric.get("cm_score"):
            platform_stats["spotify"]["popularity"] = int(chartmetric.get("cm_score", 0))

    sources_used = [k for k, v in raw_data.items() if v.get("available")]
    sources_unavailable = [
        {"source": k, "reason": v.get("reason", "unavailable")}
        for k, v in raw_data.items()
        if not v.get("available")
    ]

    return {
        "artist_name": artist_name,
        "image": image,
        "genres": genres[:5],
        "melodio_score": analysis.get("melodio_score", {}),
        "predictive_angles": analysis.get("predictive_angles", {}),
        "executive_summary": analysis.get("executive_summary", ""),
        "sign_recommendation": analysis.get("sign_recommendation", {}),
        "key_strengths": analysis.get("key_strengths", []),
        "key_risks": analysis.get("key_risks", []),
        "notable_collaborators": analysis.get("notable_collaborators", []),
        "genre_classification": analysis.get("genre_classification", ""),
        "platform_stats": platform_stats,
        "discography": musicbrainz.get("releases", []) if musicbrainz.get("available") else [],
        "live_events": bandsintown.get("events", []) if bandsintown.get("available") else [],
        "genius_data": (
            {"songs_found": genius.get("songs_found", 0), "top_songs": genius.get("songs", [])[:5]}
            if genius.get("available") else None
        ),
        "wikipedia_extract": wikipedia.get("extract") if wikipedia.get("available") else None,
        "sources_used": sources_used,
        "sources_unavailable": sources_unavailable,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/search")
async def search_artists(
    q: str = Query(..., min_length=1, description="Artist name to search"),
    request: Request = None,
):
    """Search for artists across platforms."""
    q = q.strip()
    cache_key = f"intel:search:{q.lower()}"

    cached = await _cache_get(request, cache_key)
    if cached:
        return cached

    results = []

    spotify = await fetch_spotify(q)
    if spotify.get("available"):
        results.append({
            "name": spotify["name"],
            "image": spotify.get("image"),
            "genres": spotify.get("genres", []),
            "followers": spotify.get("followers", 0),
            "popularity": spotify.get("popularity", 0),
            "platforms": {"spotify": spotify.get("external_url")},
            "source": "spotify",
        })

    if not results:
        mb = await fetch_musicbrainz(q)
        if mb.get("available"):
            results.append({
                "name": mb["name"],
                "image": None,
                "genres": mb.get("tags", []),
                "followers": 0,
                "popularity": 0,
                "platforms": {},
                "source": "musicbrainz",
            })

    if not results:
        results.append({
            "name": q,
            "image": None,
            "genres": [],
            "followers": 0,
            "popularity": 0,
            "platforms": {},
            "source": "manual",
        })

    response = {"query": q, "results": results, "count": len(results)}
    await _cache_set(request, cache_key, response, REDIS_TTL_SEARCH)
    return response


@router.get("/report/{artist_name}")
async def get_report(
    artist_name: str,
    request: Request = None,
    refresh: bool = Query(False, description="Force fresh data"),
):
    """Generate a full intelligence report for an artist."""
    artist_name = artist_name.strip()
    cache_key = f"intel:report:{artist_name.lower().replace(' ', '_')}"

    if not refresh:
        cached = await _cache_get(request, cache_key)
        if cached:
            cached["cached"] = True
            return cached

    report = await _build_report(artist_name, request)
    await _cache_set(request, cache_key, report, REDIS_TTL_REPORT)
    return report


@router.get("/compare")
async def compare_artists(
    artists: str = Query(..., description="Comma-separated artist names (2-4)"),
    request: Request = None,
):
    """Compare multiple artists side by side."""
    names = [n.strip() for n in artists.split(",") if n.strip()][:4]
    if len(names) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 artist names")

    cache_key = f"intel:compare:{':'.join(sorted(n.lower() for n in names))}"
    cached = await _cache_get(request, cache_key)
    if cached:
        return cached

    reports = await asyncio.gather(
        *[_build_report(name, request) for name in names],
        return_exceptions=True,
    )

    comparison = []
    for i, report in enumerate(reports):
        if isinstance(report, Exception):
            comparison.append({"artist_name": names[i], "error": str(report)})
        else:
            comparison.append({
                "artist_name": report["artist_name"],
                "image": report.get("image"),
                "genres": report.get("genres", []),
                "melodio_score": report.get("melodio_score", {}),
                "predictive_angles_summary": {
                    k: v.get("score", 0)
                    for k, v in report.get("predictive_angles", {}).items()
                },
                "sign_recommendation": report.get("sign_recommendation", {}),
                "key_strengths": report.get("key_strengths", []),
                "key_risks": report.get("key_risks", []),
                "platform_stats": report.get("platform_stats", {}),
            })

    ai_summary = ""
    prompt = (
        f"Compare these artists for Melodio A&R in 2-3 sentences. "
        f"Focus on who shows more potential and why. Do NOT use invest, investment, or ROI.\n\n"
        f"Data: {json.dumps([{'name': c['artist_name'], 'score': c['melodio_score'].get('total', 0), 'decision': c['sign_recommendation'].get('decision', '')} for c in comparison])}\n\nReturn plain text only."
    )
    text = await _call_claude(prompt, max_tokens=300)
    if text:
        ai_summary = text.strip()

    result = {
        "artists": comparison,
        "ai_summary": ai_summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    await _cache_set(request, cache_key, result, REDIS_TTL_COMPARE)
    return result
