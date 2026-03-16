"""
Hub Agent
Manages the ECHO Producer Hub — onboarding, beat matching, brief management,
multi-producer combination tracks, and producer payments.
"""

import logging
import uuid
from datetime import datetime, timezone

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Match scoring weights
MATCH_WEIGHTS = {
    "genre_fit": 0.30,
    "mood_match": 0.25,
    "bpm_range": 0.20,
    "quality_score": 0.15,
    "producer_tier": 0.10,
}

# Producer payment structure
PAYMENT_STRUCTURE = {
    "non_exclusive": {
        "upfront_min": 100.0,
        "upfront_max": 300.0,
        "points": 0,
        "description": "Non-exclusive beat license",
    },
    "exclusive": {
        "upfront_min": 500.0,
        "upfront_max": 2000.0,
        "points_min": 2,
        "points_max": 4,
        "description": "Exclusive beat purchase",
    },
    "combination": {
        "upfront_min": 25.0,
        "upfront_max": 100.0,
        "points_total_min": 4,
        "points_total_max": 8,
        "description": "Multi-producer combination track (proportional split)",
    },
}

# Producer tiers
TIER_MULTIPLIERS = {
    "newcomer": 0.6,
    "rising": 0.75,
    "established": 0.90,
    "elite": 1.0,
}

LABEL_GENRES = {"r&b", "hip-hop", "pop", "electronic", "indie"}


class HubAgent(BaseAgent):
    agent_id = "hub"
    agent_name = "Hub Agent"
    subscriptions = ["beat.submitted", "artist.needs_production"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "onboard_producer": self._onboard_producer,
            "match_beat": self._match_beat,
            "process_brief": self._process_brief,
            "combine_beats": self._combine_beats,
            "approve_beat": self._approve_beat,
            "calculate_producer_payment": self._calculate_producer_payment,
            # Legacy
            "score_beat": self._approve_beat,
            "match_beat_to_artist": self._match_beat,
            "process_placement": self._process_placement,
            "pay_producer": self._pay_producer,
            "hub_stats": self._hub_stats,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    # ----------------------------------------------------------------
    # onboard_producer
    # ----------------------------------------------------------------

    async def _onboard_producer(self, task: AgentTask) -> dict:
        p = task.payload
        name = p.get("name") or p.get("producer_name", "")
        email = p.get("email", "")
        genres = p.get("genres", [])
        sample_beats = p.get("sample_beat_urls", [])
        instagram = p.get("instagram_url", "")
        portfolio_url = p.get("portfolio_url", "")

        if not name or not email:
            return {"error": "name and email required"}

        # Check for existing producer
        existing = await self.db_fetchrow("SELECT id FROM producers WHERE email = $1", email)
        if existing:
            return {"error": "Producer already registered", "producer_id": str(existing["id"])}

        # Evaluate genre fit
        genre_set = {g.lower().strip() for g in genres}
        genre_fit_score = len(genre_set & LABEL_GENRES) / max(len(genres), 1) * 100

        # Evaluate based on available signals
        has_samples = len(sample_beats) > 0
        has_social = bool(instagram)
        has_portfolio = bool(portfolio_url)

        initial_score = 50.0
        if has_samples:
            initial_score += 20.0
        if has_social:
            initial_score += 10.0
        if has_portfolio:
            initial_score += 10.0
        initial_score += genre_fit_score * 0.10
        initial_score = min(100.0, initial_score)

        # Assign initial tier
        tier = "newcomer" if initial_score < 65 else "rising" if initial_score < 80 else "established"

        # Check if approved
        approved = genre_fit_score >= 30 and has_samples

        if approved:
            producer_id = str(uuid.uuid4())
            await self.db_execute(
                """
                INSERT INTO producers (id, name, email, genres, portfolio_url, tier, status)
                VALUES ($1::uuid, $2, $3, $4, $5, $6, 'active')
                """,
                producer_id,
                name,
                email,
                genres,
                portfolio_url or instagram,
                tier,
            )

            await self.send_message("comms", "send_email", {
                "to_email": email,
                "to_name": name,
                "subject": "Welcome to ECHO Producer Hub",
                "body": (
                    f"Hey {name}! You're now part of the ECHO Producer Hub. "
                    f"Your beats are now eligible for placement on our artist roster. "
                    f"Upload your catalog at your dashboard and we'll get to matching."
                ),
            })

            await self.log_audit("producer_onboarded", "producers", producer_id, {
                "tier": tier,
                "genre_fit_score": genre_fit_score,
                "initial_score": initial_score,
            })

            logger.info(f"[Hub] Producer onboarded: {name} (tier={tier}, score={initial_score:.0f})")
        else:
            producer_id = None
            logger.info(f"[Hub] Producer not approved: {name} (genre_fit={genre_fit_score:.0f}%, samples={has_samples})")

        return {
            "name": name,
            "email": email,
            "approved": approved,
            "producer_id": producer_id,
            "tier": tier if approved else None,
            "initial_score": round(initial_score, 1),
            "genre_fit_score": round(genre_fit_score, 1),
            "rejection_reason": None if approved else "Insufficient genre fit or no sample beats provided",
        }

    # ----------------------------------------------------------------
    # match_beat
    # ----------------------------------------------------------------

    async def _match_beat(self, task: AgentTask) -> dict:
        p = task.payload
        artist_id = p.get("artist_id") or task.artist_id
        target_genre = (p.get("genre") or "").lower()
        target_mood = (p.get("mood") or "").lower()
        bpm_min = float(p.get("bpm_min") or 0)
        bpm_max = float(p.get("bpm_max") or 999)
        references = p.get("reference_tracks", [])

        # Pull artist data if not provided
        if artist_id and not target_genre:
            artist = await self.db_fetchrow("SELECT genre FROM artists WHERE id = $1::uuid", artist_id)
            if artist:
                target_genre = (artist.get("genre") or "").lower()

        # Fetch available beats
        beats = await self.db_fetch(
            """
            SELECT id, title, bpm, key, quality_score, uniqueness_score,
                   genre, mood, producer_id, tier, price_non_exclusive, price_exclusive
            FROM hub_beats
            WHERE status = 'available'
            ORDER BY quality_score DESC
            LIMIT 50
            """
        )

        if not beats:
            return {"artist_id": artist_id, "matches": [], "message": "No available beats in catalog"}

        scored_beats = []
        for beat in beats:
            score = self._score_beat_match(beat, target_genre, target_mood, bpm_min, bpm_max)
            scored_beats.append({**beat, "match_score": score})

        # Sort by match score, return top 5
        scored_beats.sort(key=lambda b: b["match_score"], reverse=True)
        top_matches = scored_beats[:5]

        return {
            "artist_id": artist_id,
            "brief": {
                "genre": target_genre,
                "mood": target_mood,
                "bpm_range": f"{bpm_min}-{bpm_max}" if bpm_max < 999 else f"{bpm_min}+",
                "references": references,
            },
            "matches": top_matches,
            "total_beats_evaluated": len(beats),
        }

    # ----------------------------------------------------------------
    # process_brief
    # ----------------------------------------------------------------

    async def _process_brief(self, task: AgentTask) -> dict:
        p = task.payload
        artist_id = p.get("artist_id") or task.artist_id
        release_id = p.get("release_id") or task.release_id
        genre = p.get("genre", "")
        mood = p.get("mood", "")
        bpm_range = p.get("bpm_range", "")
        deadline = p.get("deadline")
        budget_upfront = float(p.get("budget_upfront") or 0)
        notes = p.get("notes", "")

        brief_id = str(uuid.uuid4())

        brief = {
            "brief_id": brief_id,
            "artist_id": artist_id,
            "release_id": release_id,
            "genre": genre,
            "mood": mood,
            "bpm_range": bpm_range,
            "budget_upfront": budget_upfront,
            "deadline": deadline,
            "notes": notes,
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "status": "open",
        }

        # Broadcast brief to all producers (via bus)
        await self.broadcast("hub.brief.posted", {
            "brief": brief,
            "from_agent": self.agent_id,
        })

        # Also run immediate beat matching
        match_result = await self._match_beat(AgentTask(
            task_id=f"{task.task_id}_match",
            task_type="match_beat",
            payload={
                "artist_id": artist_id,
                "genre": genre,
                "mood": mood,
                "bpm_min": float(bpm_range.split("-")[0]) if bpm_range and "-" in bpm_range else 0,
                "bpm_max": float(bpm_range.split("-")[1]) if bpm_range and "-" in bpm_range else 999,
            },
        ))

        logger.info(f"[Hub] Brief posted: {genre}/{mood}/{bpm_range} — {len(match_result.get('matches', []))} immediate matches")

        return {
            "brief": brief,
            "immediate_matches": match_result.get("matches", []),
            "immediate_match_count": len(match_result.get("matches", [])),
        }

    # ----------------------------------------------------------------
    # combine_beats
    # ----------------------------------------------------------------

    async def _combine_beats(self, task: AgentTask) -> dict:
        p = task.payload
        beat_ids = p.get("beat_ids", [])
        artist_id = p.get("artist_id") or task.artist_id
        release_id = p.get("release_id") or task.release_id

        if not beat_ids or len(beat_ids) < 2:
            return {"error": "At least 2 beat_ids required for combination track"}

        beats = []
        for beat_id in beat_ids:
            beat = await self.db_fetchrow(
                "SELECT id, title, producer_id, bpm, key, quality_score FROM hub_beats WHERE id = $1::uuid",
                beat_id,
            )
            if beat:
                beats.append(dict(beat))

        if len(beats) < 2:
            return {"error": "Could not find all specified beats"}

        # Calculate payment split
        payment = self._calculate_combination_payment(beats)

        track_id = str(uuid.uuid4())

        combination_plan = {
            "combination_track_id": track_id,
            "beats": beats,
            "producer_count": len(beats),
            "payment_plan": payment,
            "production_notes": (
                f"Combination track featuring {len(beats)} producers. "
                f"Key alignment: check beat keys for harmonic compatibility. "
                f"BPM matching required before final mix."
            ),
            "next_steps": [
                "Send stems to Production Agent for mixing",
                "QC Agent checks final master",
                "Legal Agent drafts multi-producer split agreement",
            ],
        }

        # Notify production agent
        await self.send_message("production", "mix_combination_track", {
            "beat_ids": beat_ids,
            "artist_id": artist_id,
            "release_id": release_id,
            "combination_plan": combination_plan,
        })

        # Notify legal for split agreement
        await self.send_message("legal", "draft_producer_split", {
            "beat_ids": beat_ids,
            "artist_id": artist_id,
            "payment_plan": payment,
        })

        return combination_plan

    # ----------------------------------------------------------------
    # approve_beat
    # ----------------------------------------------------------------

    async def _approve_beat(self, task: AgentTask) -> dict:
        p = task.payload
        beat_id = p.get("beat_id")

        if not beat_id:
            return {"error": "beat_id required"}

        # QC checks
        quality = float(p.get("quality_score") or 75.0)
        uniqueness = float(p.get("uniqueness_score") or 70.0)
        sync_readiness = float(p.get("sync_readiness") or 65.0)
        bpm = p.get("bpm")
        key = p.get("key")
        format_ok = p.get("format_ok", True)

        issues = []
        if quality < 60:
            issues.append(f"Quality score {quality} below minimum (60)")
        if not format_ok:
            issues.append("Audio format does not meet specs (requires WAV/AIFF, 24-bit, 44.1kHz)")
        if bpm and (float(bpm) < 60 or float(bpm) > 200):
            issues.append(f"BPM {bpm} out of acceptable range (60-200)")

        approved = len(issues) == 0

        new_status = "available" if approved else "rejected"
        await self.db_execute(
            "UPDATE hub_beats SET quality_score = $2, uniqueness_score = $3, sync_readiness = $4, status = $5 WHERE id = $1::uuid",
            beat_id, quality, uniqueness, sync_readiness, new_status,
        )

        await self.log_audit("beat_qc", "hub_beats", beat_id, {
            "approved": approved,
            "quality": quality,
            "issues": issues,
        })

        if approved:
            logger.info(f"[Hub] Beat approved: {beat_id} (quality={quality})")
        else:
            logger.warning(f"[Hub] Beat rejected: {beat_id} — {issues}")

        return {
            "beat_id": beat_id,
            "approved": approved,
            "status": new_status,
            "scores": {
                "quality": quality,
                "uniqueness": uniqueness,
                "sync_readiness": sync_readiness,
            },
            "issues": issues,
        }

    # ----------------------------------------------------------------
    # calculate_producer_payment
    # ----------------------------------------------------------------

    async def _calculate_producer_payment(self, task: AgentTask) -> dict:
        p = task.payload
        deal_type = p.get("deal_type", "exclusive")
        producer_id = p.get("producer_id")
        beat_id = p.get("beat_id")
        combination_count = int(p.get("combination_count", 1))

        # Get producer tier for multiplier
        tier = "newcomer"
        if producer_id:
            producer = await self.db_fetchrow("SELECT tier FROM producers WHERE id = $1::uuid", producer_id)
            if producer:
                tier = producer.get("tier", "newcomer")

        multiplier = TIER_MULTIPLIERS.get(tier, 0.75)

        if deal_type == "non_exclusive":
            struct = PAYMENT_STRUCTURE["non_exclusive"]
            upfront = round(struct["upfront_min"] + (struct["upfront_max"] - struct["upfront_min"]) * multiplier, 2)
            points = 0
            points_from = None

        elif deal_type == "exclusive":
            struct = PAYMENT_STRUCTURE["exclusive"]
            upfront = round(struct["upfront_min"] + (struct["upfront_max"] - struct["upfront_min"]) * multiplier, 2)
            points = round(struct["points_min"] + (struct["points_max"] - struct["points_min"]) * multiplier, 1)
            points_from = "label_share"

        elif deal_type == "combination":
            struct = PAYMENT_STRUCTURE["combination"]
            # Each producer gets proportional share
            upfront_per_producer = round(
                (struct["upfront_min"] + (struct["upfront_max"] - struct["upfront_min"]) * multiplier),
                2,
            )
            total_points = struct["points_total_min"] + (struct["points_total_max"] - struct["points_total_min"]) * 0.5
            points = round(total_points / max(combination_count, 1), 2)
            upfront = upfront_per_producer
            points_from = "label_share"
        else:
            return {"error": f"Unknown deal_type: {deal_type}"}

        payment = {
            "producer_id": producer_id,
            "beat_id": beat_id,
            "deal_type": deal_type,
            "tier": tier,
            "tier_multiplier": multiplier,
            "upfront_usd": upfront,
            "echo_points": points,
            "points_source": points_from,
            "points_note": "All points from LABEL share — never from artist share" if points > 0 else None,
            "payment_channel": "stripe",
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

        if producer_id and upfront > 0:
            await self.db_execute(
                "UPDATE producers SET total_earned = total_earned + $2, updated_at = NOW() WHERE id = $1::uuid",
                producer_id, upfront,
            )
            await self.log_audit("producer_payment_calculated", "producers", producer_id, {
                "deal_type": deal_type,
                "upfront": upfront,
                "points": points,
            })

        return payment

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _score_beat_match(
        self,
        beat: dict,
        target_genre: str,
        target_mood: str,
        bpm_min: float,
        bpm_max: float,
    ) -> float:
        scores = {}

        # Genre fit (30%)
        beat_genre = (beat.get("genre") or "").lower()
        if target_genre and beat_genre:
            genre_score = 100.0 if target_genre in beat_genre or beat_genre in target_genre else 40.0
        else:
            genre_score = 60.0
        scores["genre_fit"] = genre_score

        # Mood match (25%)
        beat_mood = (beat.get("mood") or "").lower()
        if target_mood and beat_mood:
            mood_score = 100.0 if target_mood == beat_mood else (60.0 if any(w in beat_mood for w in target_mood.split()) else 30.0)
        else:
            mood_score = 60.0
        scores["mood_match"] = mood_score

        # BPM range (20%)
        bpm = float(beat.get("bpm") or 0)
        if bpm and bpm_max < 999:
            bpm_score = 100.0 if bpm_min <= bpm <= bpm_max else max(0.0, 100.0 - abs(bpm - (bpm_min + bpm_max) / 2) * 2)
        else:
            bpm_score = 70.0
        scores["bpm_range"] = min(100.0, bpm_score)

        # Quality score (15%) — directly from beat record
        quality = float(beat.get("quality_score") or 70.0)
        scores["quality_score"] = quality

        # Producer tier (10%)
        tier = (beat.get("tier") or "newcomer").lower()
        tier_score = {"elite": 100.0, "established": 80.0, "rising": 65.0, "newcomer": 50.0}.get(tier, 50.0)
        scores["producer_tier"] = tier_score

        total = round(sum(scores[k] * MATCH_WEIGHTS[k] for k in MATCH_WEIGHTS), 1)
        return total

    def _calculate_combination_payment(self, beats: list[dict]) -> dict:
        count = len(beats)
        total_upfront = sum(
            (PAYMENT_STRUCTURE["combination"]["upfront_min"] + PAYMENT_STRUCTURE["combination"]["upfront_max"]) / 2
            for _ in beats
        )
        total_points = (PAYMENT_STRUCTURE["combination"]["points_total_min"] + PAYMENT_STRUCTURE["combination"]["points_total_max"]) / 2

        per_producer = []
        for beat in beats:
            per_producer.append({
                "producer_id": str(beat.get("producer_id", "")),
                "beat_id": str(beat.get("id", "")),
                "beat_title": beat.get("title", ""),
                "upfront_usd": round(total_upfront / count, 2),
                "echo_points": round(total_points / count, 2),
                "points_source": "label_share",
            })

        return {
            "deal_type": "combination",
            "producer_count": count,
            "total_upfront_usd": round(total_upfront, 2),
            "total_points": round(total_points, 2),
            "per_producer": per_producer,
            "points_note": "All points from LABEL share — never from artist share",
        }

    # ----------------------------------------------------------------
    # Legacy handlers
    # ----------------------------------------------------------------

    async def _process_placement(self, task: AgentTask) -> dict:
        beat_id = task.payload.get("beat_id")
        track_id = task.payload.get("track_id")
        deal_type = task.payload.get("deal_type", "non_exclusive")
        price = task.payload.get("price", 0.0)
        await self.db_execute(
            "UPDATE hub_beats SET status = 'placed', placed_on_track_id = $2::uuid, purchase_count = purchase_count + 1 WHERE id = $1::uuid",
            beat_id, track_id,
        )
        await self.log_audit("beat_placement", "hub_beats", beat_id, {"track_id": track_id, "price": price})
        return {"beat_id": beat_id, "track_id": track_id, "deal_type": deal_type, "price": price}

    async def _pay_producer(self, task: AgentTask) -> dict:
        producer_id = task.payload.get("producer_id")
        amount = float(task.payload.get("amount", 0.0))
        await self.db_execute(
            "UPDATE producers SET total_earned = total_earned + $2, updated_at = NOW() WHERE id = $1::uuid",
            producer_id, amount,
        )
        return {"producer_id": producer_id, "amount_paid": amount, "channel": "stripe"}

    async def _hub_stats(self, task: AgentTask) -> dict:
        stats = await self.db_fetchrow(
            """
            SELECT
              COUNT(*) as total_beats,
              COUNT(*) FILTER (WHERE status = 'available') as available,
              COUNT(*) FILTER (WHERE status = 'placed') as placed,
              COALESCE(AVG(quality_score), 0) as avg_quality
            FROM hub_beats
            """
        )
        producer_count = await self.db_fetchrow("SELECT COUNT(*) as count FROM producers WHERE status = 'active'")
        return {
            **(dict(stats) if stats else {}),
            "active_producers": int(producer_count.get("count") or 0) if producer_count else 0,
        }

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Hub] Online — managing Producer Hub and beat matching")
