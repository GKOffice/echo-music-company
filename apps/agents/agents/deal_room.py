"""
Melodio Deal Room Agent
Creator-to-creator rights trading marketplace.
Artists, producers, and songwriters trade master points,
publishing points, co-write opportunities, and beats for cash or points.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

DEAL_FEE_PCT = Decimal("0.03")  # 3% platform fee on cash deals

# B2B price per point by artist tier (13% below fan store rate)
TIER_PRICES = {
    "seed": 150, "new": 150,
    "rising": 600,
    "established": 3000, "star": 3000,
    "hot": 5000,
    "diamond": 12000,
    "legend": 25000,
}
CREATOR_DISCOUNT = Decimal("0.87")


def _str(v) -> Optional[str]:
    return str(v) if v is not None else None


class DealRoomAgent(BaseAgent):
    agent_id = "deal_room"
    agent_name = "Deal Room Agent"
    subscriptions = ["deals.new", "deals.offer", "deals.accepted", "agent.deal_room"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        asyncio.create_task(self._expired_listings_loop())
        asyncio.create_task(self._deal_nudge_loop())
        logger.info("[DealRoom] Online. Creator marketplace active.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "create_listing":   self._task_create_listing,
            "browse_listings":  self._task_browse_listings,
            "make_offer":       self._task_make_offer,
            "counter_offer":    self._task_counter_offer,
            "accept_offer":     self._task_accept_offer,
            "reject_offer":     self._task_reject_offer,
            "complete_deal":    self._task_complete_deal,
            "send_message":     self._task_send_message,
            "get_thread":       self._task_get_thread,
            "my_listings":      self._task_my_listings,
            "my_offers":        self._task_my_offers,
            "my_deals":         self._task_my_deals,
            "suggest_price":    self._task_suggest_price,
            "match_creators":   self._task_match_creators,
            "rights_valuation": self._task_rights_valuation,
        }
        handler = handlers.get(task.task_type, self._task_default)
        return await handler(task)

    # ── Create Listing ───────────────────────────────────────────────

    async def _task_create_listing(self, task: AgentTask) -> AgentResult:
        p = task.payload
        creator_id = p.get("creator_id")
        listing_type = p.get("listing_type")
        points_qty = p.get("points_qty")
        track_id = p.get("track_id")

        # Validate point ownership for sell listings
        if listing_type in ("sell_master_points", "sell_publishing_points") and points_qty:
            point_type = "master" if listing_type == "sell_master_points" else "publishing"
            owned_row = await self.db_fetchrow(
                """
                SELECT COALESCE(SUM(points_purchased), 0) as total_owned
                FROM echo_points
                WHERE buyer_user_id = $1::uuid
                  AND track_id = $2::uuid
                  AND point_type = $3
                  AND status IN ('active', 'tradeable')
                """,
                creator_id, track_id, point_type,
            )
            owned = float(owned_row["total_owned"]) if owned_row else 0.0
            if float(points_qty) > owned:
                return AgentResult(
                    success=False, task_id=task.task_id, agent_id=self.agent_id,
                    error=f"Insufficient points. You own {owned} {point_type} points for this track.",
                )

        listing_id = str(uuid.uuid4())
        await self.db_execute(
            """
            INSERT INTO deal_listings (
                id, creator_id, creator_type, listing_type,
                title, description, track_id, release_id,
                points_qty, asking_price, accept_points, accept_cash,
                points_price, genre, mood, bpm_min, bpm_max,
                expires_at
            ) VALUES (
                $1::uuid, $2::uuid, $3, $4,
                $5, $6, $7::uuid, $8::uuid,
                $9, $10, $11, $12,
                $13, $14, $15::text[], $16, $17,
                $18
            )
            """,
            listing_id,
            creator_id,
            p.get("creator_type"),
            listing_type,
            p.get("title"),
            p.get("description"),
            track_id,
            p.get("release_id"),
            points_qty,
            p.get("asking_price"),
            p.get("accept_points", False),
            p.get("accept_cash", True),
            p.get("points_price"),
            p.get("genre"),
            p.get("mood", []) or [],
            p.get("bpm_min"),
            p.get("bpm_max"),
            p.get("expires_at"),
        )

        await self.broadcast("deals.new", {
            "listing_id": listing_id,
            "listing_type": listing_type,
            "creator_id": creator_id,
        })

        # Notify Analytics for point sale listings
        if listing_type in ("sell_master_points", "sell_publishing_points"):
            await self.send_message("analytics", "deal_room.listing_created", {
                "listing_id": listing_id,
                "listing_type": listing_type,
                "track_id": track_id,
                "points_qty": points_qty,
                "asking_price": p.get("asking_price"),
            })

        # Get price suggestion
        price_task = AgentTask(
            task_id=task.task_id,
            task_type="suggest_price",
            payload={
                "listing_type": listing_type,
                "points_qty": points_qty or 1,
                "artist_id": p.get("artist_id"),
            },
        )
        price_result = await self._task_suggest_price(price_task)

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "listing_id": listing_id,
                "listing_type": listing_type,
                "status": "active",
                "suggested_price": price_result.result,
            },
        )

    # ── Browse Listings ──────────────────────────────────────────────

    async def _task_browse_listings(self, task: AgentTask) -> AgentResult:
        p = task.payload
        listing_type = p.get("listing_type")
        genre = p.get("genre")
        accept_points = p.get("accept_points")
        accept_cash = p.get("accept_cash")
        creator_type = p.get("creator_type")
        min_price = p.get("min_price")
        max_price = p.get("max_price")
        sort = p.get("sort", "newest")
        limit = min(int(p.get("limit", 20)), 50)
        offset = int(p.get("offset", 0))

        conditions = ["dl.status = 'active'"]
        args = []
        i = 1

        if listing_type:
            conditions.append(f"dl.listing_type = ${i}"); args.append(listing_type); i += 1
        if genre:
            conditions.append(f"dl.genre ILIKE ${i}"); args.append(f"%{genre}%"); i += 1
        if accept_points is not None:
            conditions.append(f"dl.accept_points = ${i}"); args.append(accept_points); i += 1
        if accept_cash is not None:
            conditions.append(f"dl.accept_cash = ${i}"); args.append(accept_cash); i += 1
        if creator_type:
            conditions.append(f"dl.creator_type = ${i}"); args.append(creator_type); i += 1
        if min_price is not None:
            conditions.append(f"dl.asking_price >= ${i}"); args.append(min_price); i += 1
        if max_price is not None:
            conditions.append(f"dl.asking_price <= ${i}"); args.append(max_price); i += 1

        order_map = {
            "newest": "dl.created_at DESC",
            "price_low": "dl.asking_price ASC NULLS LAST",
            "price_high": "dl.asking_price DESC NULLS LAST",
            "most_viewed": "dl.views DESC",
        }
        order = order_map.get(sort, "dl.created_at DESC")
        where = " AND ".join(conditions)

        query = f"""
            SELECT
                dl.id, dl.creator_id, dl.creator_type, dl.listing_type,
                dl.title, dl.description, dl.points_qty, dl.asking_price,
                dl.accept_points, dl.accept_cash, dl.points_price,
                dl.genre, dl.mood, dl.bpm_min, dl.bpm_max,
                dl.status, dl.views, dl.created_at, dl.expires_at,
                t.title AS track_title, t.genre AS track_genre, t.bpm,
                r.title AS release_title
            FROM deal_listings dl
            LEFT JOIN tracks t ON dl.track_id = t.id
            LEFT JOIN releases r ON dl.release_id = r.id
            WHERE {where}
            ORDER BY {order}
            LIMIT ${i} OFFSET ${i+1}
        """
        args.extend([limit, offset])
        rows = await self.db_fetch(query, *args)

        # Increment view count for returned listings
        if rows:
            ids = [str(r["id"]) for r in rows]
            placeholders = ", ".join(f"${j+1}::uuid" for j in range(len(ids)))
            await self.db_execute(
                f"UPDATE deal_listings SET views = views + 1 WHERE id IN ({placeholders})",
                *ids,
            )

        total_row = await self.db_fetchrow(
            f"SELECT COUNT(*) as cnt FROM deal_listings dl WHERE {where}",
            *args[:-2],
        )
        total = int(total_row["cnt"]) if total_row else 0

        serialized = []
        for r in rows:
            row = dict(r)
            for k, v in row.items():
                if hasattr(v, "hex"):
                    row[k] = str(v)
                elif hasattr(v, "isoformat"):
                    row[k] = v.isoformat()
            serialized.append(row)

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"listings": serialized, "total": total, "limit": limit, "offset": offset},
        )

    # ── Make Offer ───────────────────────────────────────────────────

    async def _task_make_offer(self, task: AgentTask) -> AgentResult:
        p = task.payload
        listing_id = p.get("listing_id")
        offerer_id = p.get("offerer_id")
        offer_type = p.get("offer_type", "cash")
        points_offered = p.get("points_offered")
        points_track_id = p.get("points_track_id")

        # Validate listing is still active
        listing = await self.db_fetchrow(
            "SELECT id, creator_id, title, status, listing_type FROM deal_listings WHERE id = $1::uuid",
            listing_id,
        )
        if not listing:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error="Listing not found.")
        if listing["status"] != "active":
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error=f"Listing is {listing['status']}, not accepting offers.")
        if str(listing["creator_id"]) == str(offerer_id):
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error="Cannot make an offer on your own listing.")

        # Validate point ownership if paying with points
        if offer_type in ("points", "hybrid") and points_offered and points_track_id:
            owned = await self.db_fetchrow(
                """
                SELECT COALESCE(SUM(points_purchased), 0) as total
                FROM echo_points
                WHERE buyer_user_id = $1::uuid AND track_id = $2::uuid
                  AND status IN ('active', 'tradeable')
                """,
                offerer_id, points_track_id,
            )
            if float(owned["total"]) < float(points_offered):
                return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                                   error=f"Insufficient points. You own {float(owned['total'])} points for that track.")

        offer_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await self.db_execute(
            """
            INSERT INTO deal_offers (
                id, listing_id, offerer_id, offer_type,
                cash_amount, points_offered, points_track_id,
                message, expires_at
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid, $4,
                $5, $6, $7::uuid,
                $8, $9
            )
            """,
            offer_id, listing_id, offerer_id, offer_type,
            p.get("cash_amount"), points_offered, points_track_id,
            p.get("message"), expires_at,
        )

        # Notify listing creator via Comms
        await self.send_message("comms", "notification", {
            "user_id": str(listing["creator_id"]),
            "type": "new_offer",
            "subject": f"New offer on '{listing['title']}'",
            "body": f"You received a new {offer_type} offer on your Deal Room listing.",
            "metadata": {"offer_id": offer_id, "listing_id": listing_id},
        })

        await self.broadcast("deals.offer", {"offer_id": offer_id, "listing_id": listing_id})

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "offer_id": offer_id,
                "listing_id": listing_id,
                "status": "pending",
                "expires_at": expires_at.isoformat(),
            },
        )

    # ── Counter Offer ────────────────────────────────────────────────

    async def _task_counter_offer(self, task: AgentTask) -> AgentResult:
        p = task.payload
        offer_id = p.get("offer_id")
        responder_id = p.get("responder_id")

        # Validate offer belongs to this creator's listing
        offer = await self.db_fetchrow(
            """
            SELECT do2.id, do2.offerer_id, do2.listing_id, do2.status,
                   dl.creator_id, dl.title
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.id = $1::uuid
            """,
            offer_id,
        )
        if not offer:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error="Offer not found.")
        if str(offer["creator_id"]) != str(responder_id):
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error="Only the listing creator can counter.")
        if offer["status"] not in ("pending",):
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error=f"Offer status is '{offer['status']}', cannot counter.")

        counter_cash = p.get("counter_cash")
        counter_points = p.get("counter_points")
        counter_message = p.get("counter_message", "")

        await self.db_execute(
            """
            UPDATE deal_offers
            SET status = 'countered',
                counter_cash = $2,
                counter_points = $3,
                counter_message = $4,
                responded_at = NOW()
            WHERE id = $1::uuid
            """,
            offer_id, counter_cash, counter_points, counter_message,
        )

        # Build counter terms string for notification
        terms_parts = []
        if counter_cash:
            terms_parts.append(f"${counter_cash:.2f} cash")
        if counter_points:
            terms_parts.append(f"{counter_points} points")
        terms_str = " + ".join(terms_parts) or "see counter message"

        await self.send_message("comms", "notification", {
            "user_id": str(offer["offerer_id"]),
            "type": "offer_countered",
            "subject": f"Your offer was countered — '{offer['title']}'",
            "body": f"Counter offer: {terms_str}. {counter_message}",
            "metadata": {"offer_id": offer_id, "listing_id": str(offer["listing_id"])},
        })

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "offer_id": offer_id,
                "status": "countered",
                "counter_cash": counter_cash,
                "counter_points": counter_points,
                "counter_message": counter_message,
            },
        )

    # ── Accept Offer ─────────────────────────────────────────────────

    async def _task_accept_offer(self, task: AgentTask) -> AgentResult:
        p = task.payload
        offer_id = p.get("offer_id")
        acceptor_id = p.get("acceptor_id")

        offer = await self.db_fetchrow(
            """
            SELECT do2.id, do2.offerer_id, do2.listing_id, do2.offer_type,
                   do2.cash_amount, do2.points_offered, do2.points_track_id,
                   do2.counter_cash, do2.counter_points, do2.status,
                   dl.creator_id, dl.title, dl.listing_type, dl.track_id
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.id = $1::uuid
            """,
            offer_id,
        )
        if not offer:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error="Offer not found.")
        if str(offer["creator_id"]) != str(acceptor_id):
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error="Only the listing creator can accept.")
        if offer["status"] not in ("pending", "countered"):
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error=f"Offer cannot be accepted in '{offer['status']}' state.")

        # Use counter values if countered, otherwise original offer values
        final_cash = offer["counter_cash"] if offer["status"] == "countered" else offer["cash_amount"]
        final_points = offer["counter_points"] if offer["status"] == "countered" else offer["points_offered"]

        # Update offer and listing
        await self.db_execute(
            "UPDATE deal_offers SET status = 'accepted', responded_at = NOW() WHERE id = $1::uuid",
            offer_id,
        )
        await self.db_execute(
            "UPDATE deal_listings SET status = 'closed', closed_at = NOW() WHERE id = $1::uuid",
            str(offer["listing_id"]),
        )

        # Create deal record
        deal_id = str(uuid.uuid4())
        await self.db_execute(
            """
            INSERT INTO deals (
                id, listing_id, offer_id, seller_id, buyer_id,
                deal_type, track_id, cash_paid, points_paid, status
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid, $4::uuid, $5::uuid,
                $6, $7::uuid, $8, $9, 'pending_contract'
            )
            """,
            deal_id,
            str(offer["listing_id"]),
            offer_id,
            str(offer["creator_id"]),
            str(offer["offerer_id"]),
            offer["listing_type"],
            _str(offer["track_id"]),
            final_cash,
            final_points,
        )

        # Determine contract type and trigger Legal Agent
        contract_type_map = {
            "sell_master_points": "points_assignment",
            "sell_publishing_points": "points_assignment",
            "buy_master_points": "points_assignment",
            "seek_cowriter": "cowrite_agreement",
            "seek_producer": "beat_license",
            "offer_beat": "beat_license",
        }
        contract_type = contract_type_map.get(offer["listing_type"], "points_assignment")

        await self.send_message("legal", "generate_contract", {
            "contract_type": contract_type,
            "deal_id": deal_id,
            "seller_id": str(offer["creator_id"]),
            "buyer_id": str(offer["offerer_id"]),
            "track_id": _str(offer["track_id"]),
            "points_qty": float(final_points) if final_points else None,
            "cash_amount": float(final_cash) if final_cash else None,
            "listing_type": offer["listing_type"],
        })

        # Notify both parties
        await self.send_message("comms", "notification", {
            "user_id": str(offer["offerer_id"]),
            "type": "offer_accepted",
            "subject": f"Offer accepted — '{offer['title']}'",
            "body": "Your offer was accepted! A contract is being generated. Please review and sign.",
            "metadata": {"deal_id": deal_id},
        })
        await self.send_message("comms", "notification", {
            "user_id": str(offer["creator_id"]),
            "type": "deal_created",
            "subject": f"Deal created — '{offer['title']}'",
            "body": "Deal is moving forward. Contract generation in progress.",
            "metadata": {"deal_id": deal_id},
        })

        await self.broadcast("deals.accepted", {"deal_id": deal_id, "contract_type": contract_type})

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "deal_id": deal_id,
                "offer_id": offer_id,
                "status": "pending_contract",
                "contract_type": contract_type,
                "contract_generation": "triggered",
            },
        )

    # ── Reject Offer ─────────────────────────────────────────────────

    async def _task_reject_offer(self, task: AgentTask) -> AgentResult:
        p = task.payload
        offer_id = p.get("offer_id")
        rejector_id = p.get("rejector_id")

        offer = await self.db_fetchrow(
            """
            SELECT do2.id, do2.offerer_id, do2.status,
                   dl.creator_id, dl.title
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.id = $1::uuid
            """,
            offer_id,
        )
        if not offer:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error="Offer not found.")
        if str(offer["creator_id"]) != str(rejector_id):
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error="Only the listing creator can reject.")

        await self.db_execute(
            "UPDATE deal_offers SET status = 'rejected', responded_at = NOW() WHERE id = $1::uuid",
            offer_id,
        )
        await self.send_message("comms", "notification", {
            "user_id": str(offer["offerer_id"]),
            "type": "offer_rejected",
            "subject": f"Offer not accepted — '{offer['title']}'",
            "body": "Your offer was not accepted. The listing may still be active for new offers.",
            "metadata": {"offer_id": offer_id},
        })

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"offer_id": offer_id, "status": "rejected"},
        )

    # ── Complete Deal ────────────────────────────────────────────────

    async def _task_complete_deal(self, task: AgentTask) -> AgentResult:
        p = task.payload
        deal_id = p.get("deal_id")

        deal = await self.db_fetchrow(
            """
            SELECT d.*, dl.listing_type, dl.title as listing_title
            FROM deals d
            JOIN deal_listings dl ON d.listing_id = dl.id
            WHERE d.id = $1::uuid
            """,
            deal_id,
        )
        if not deal:
            return AgentResult(success=False, task_id=task.task_id, agent_id=self.agent_id,
                               error="Deal not found.")

        now = datetime.now(timezone.utc)

        # Transfer points ownership if this is a points deal
        points_transferred = None
        if deal["points_paid"] and deal["track_id"]:
            # Move echo_points from seller to buyer
            points_row = await self.db_fetchrow(
                """
                SELECT id FROM echo_points
                WHERE buyer_user_id = $1::uuid AND track_id = $2::uuid
                  AND status IN ('active', 'tradeable')
                ORDER BY created_at ASC LIMIT 1
                """,
                str(deal["seller_id"]), str(deal["track_id"]),
            )
            if points_row:
                await self.db_execute(
                    "UPDATE echo_points SET buyer_user_id = $2::uuid WHERE id = $1::uuid",
                    str(points_row["id"]), str(deal["buyer_id"]),
                )
                points_transferred = float(deal["points_paid"])

        # Update deal status
        await self.db_execute(
            """
            UPDATE deals
            SET status = 'completed',
                points_transferred = $2,
                points_transferred_at = $3,
                cash_settled_at = $4,
                completed_at = $3
            WHERE id = $1::uuid
            """,
            deal_id,
            deal["points_paid"],
            now,
            now if deal["cash_paid"] else None,
        )

        # Update offer to completed
        if deal["offer_id"]:
            await self.db_execute(
                "UPDATE deal_offers SET status = 'completed' WHERE id = $1::uuid",
                str(deal["offer_id"]),
            )

        # Notify Finance to update royalty splits
        await self.send_message("finance", "update_royalty_splits", {
            "deal_id": deal_id,
            "track_id": _str(deal["track_id"]),
            "seller_id": str(deal["seller_id"]),
            "buyer_id": str(deal["buyer_id"]),
            "points_transferred": points_transferred,
            "deal_type": deal["listing_type"],
        })

        # Notify both parties
        for user_id in (str(deal["seller_id"]), str(deal["buyer_id"])):
            await self.send_message("comms", "notification", {
                "user_id": user_id,
                "type": "deal_complete",
                "subject": "Deal complete! Rights transferred.",
                "body": f"Your Deal Room transaction for '{deal['listing_title']}' is complete.",
                "metadata": {"deal_id": deal_id},
            })

        # Audit log
        await self.log_audit(
            "deal_completed", "deal", deal_id,
            {
                "seller_id": str(deal["seller_id"]),
                "buyer_id": str(deal["buyer_id"]),
                "listing_type": deal["listing_type"],
                "points_transferred": points_transferred,
                "cash_paid": float(deal["cash_paid"]) if deal["cash_paid"] else None,
            },
        )

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "deal_id": deal_id,
                "status": "completed",
                "points_transferred": points_transferred,
                "cash_paid": float(deal["cash_paid"]) if deal["cash_paid"] else None,
                "completed_at": now.isoformat(),
            },
        )

    # ── Messaging ────────────────────────────────────────────────────

    async def _task_send_message(self, task: AgentTask) -> AgentResult:
        p = task.payload
        msg_id = str(uuid.uuid4())
        await self.db_execute(
            """
            INSERT INTO deal_messages (id, deal_offer_id, sender_id, message, attachment_url)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5)
            """,
            msg_id,
            p.get("deal_offer_id"),
            p.get("sender_id"),
            p.get("message"),
            p.get("attachment_url"),
        )
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"message_id": msg_id},
        )

    async def _task_get_thread(self, task: AgentTask) -> AgentResult:
        deal_offer_id = task.payload.get("deal_offer_id")
        rows = await self.db_fetch(
            """
            SELECT dm.id, dm.sender_id, dm.message, dm.attachment_url, dm.created_at
            FROM deal_messages dm
            WHERE dm.deal_offer_id = $1::uuid
            ORDER BY dm.created_at ASC
            """,
            deal_offer_id,
        )
        msgs = []
        for r in rows:
            row = dict(r)
            for k, v in row.items():
                if hasattr(v, "hex"):
                    row[k] = str(v)
                elif hasattr(v, "isoformat"):
                    row[k] = v.isoformat()
            msgs.append(row)
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"messages": msgs, "count": len(msgs)},
        )

    # ── My Listings / Offers / Deals ─────────────────────────────────

    async def _task_my_listings(self, task: AgentTask) -> AgentResult:
        creator_id = task.payload.get("creator_id")
        status_filter = task.payload.get("status")
        query = """
            SELECT dl.*, t.title AS track_title
            FROM deal_listings dl
            LEFT JOIN tracks t ON dl.track_id = t.id
            WHERE dl.creator_id = $1::uuid
        """
        args = [creator_id]
        if status_filter:
            query += " AND dl.status = $2"
            args.append(status_filter)
        query += " ORDER BY dl.created_at DESC LIMIT 50"
        rows = await self.db_fetch(query, *args)
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"listings": self._serialize_rows(rows)},
        )

    async def _task_my_offers(self, task: AgentTask) -> AgentResult:
        offerer_id = task.payload.get("offerer_id")
        rows = await self.db_fetch(
            """
            SELECT do2.*, dl.title AS listing_title, dl.listing_type
            FROM deal_offers do2
            JOIN deal_listings dl ON do2.listing_id = dl.id
            WHERE do2.offerer_id = $1::uuid
            ORDER BY do2.created_at DESC LIMIT 50
            """,
            offerer_id,
        )
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"offers": self._serialize_rows(rows)},
        )

    async def _task_my_deals(self, task: AgentTask) -> AgentResult:
        user_id = task.payload.get("user_id")
        rows = await self.db_fetch(
            """
            SELECT d.*, dl.title AS listing_title
            FROM deals d
            JOIN deal_listings dl ON d.listing_id = dl.id
            WHERE d.seller_id = $1::uuid OR d.buyer_id = $1::uuid
            ORDER BY d.created_at DESC LIMIT 50
            """,
            user_id,
        )
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"deals": self._serialize_rows(rows)},
        )

    # ── Suggest Price ────────────────────────────────────────────────

    async def _task_suggest_price(self, task: AgentTask) -> AgentResult:
        p = task.payload
        listing_type = p.get("listing_type")
        points_qty = Decimal(str(p.get("points_qty", 1)))
        artist_id = p.get("artist_id")

        artist = None
        if artist_id:
            artist = await self.db_fetchrow(
                "SELECT monthly_listeners, echo_score, tier FROM artists WHERE id = $1::uuid",
                artist_id,
            )

        tier = artist["tier"] if artist else "new"
        base_price_per_point = TIER_PRICES.get(tier, 150)
        suggested_per_point = (Decimal(str(base_price_per_point)) * CREATOR_DISCOUNT).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_suggested = (suggested_per_point * points_qty).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "suggested_price_per_point": float(suggested_per_point),
                "suggested_total": float(total_suggested),
                "tier": tier,
                "rationale": f"{tier.capitalize()} tier — B2B price (13% below fan store rate)",
                "range": {
                    "low": float((total_suggested * Decimal("0.8")).quantize(Decimal("1"))),
                    "high": float((total_suggested * Decimal("1.2")).quantize(Decimal("1"))),
                },
            },
        )

    # ── Match Creators ───────────────────────────────────────────────

    async def _task_match_creators(self, task: AgentTask) -> AgentResult:
        p = task.payload
        listing_type = p.get("listing_type")
        genre = p.get("genre")
        mood = p.get("mood", [])
        bpm = p.get("bpm")

        matches = []

        if listing_type == "seek_producer":
            # Match from hub_beats catalog
            rows = await self.db_fetch(
                """
                SELECT hb.id, hb.title, hb.producer_id, hb.genre, hb.bpm, hb.mood,
                       hb.price_usd, hb.accept_points,
                       u.name AS producer_name
                FROM hub_beats hb
                JOIN users u ON hb.producer_id = u.id
                WHERE hb.status = 'available'
                  AND ($1::text IS NULL OR hb.genre ILIKE $1)
                  AND ($2::int IS NULL OR ABS(hb.bpm - $2) <= 20)
                ORDER BY hb.created_at DESC LIMIT 5
                """,
                f"%{genre}%" if genre else None,
                bpm,
            )
            for i, r in enumerate(rows):
                row = self._serialize_row(dict(r))
                row["compatibility_score"] = max(60, 95 - i * 7)
                row["match_type"] = "beat"
                matches.append(row)

        elif listing_type == "seek_cowriter":
            # Match from active seek_cowriter listings
            rows = await self.db_fetch(
                """
                SELECT dl.id, dl.creator_id, dl.title, dl.genre, dl.description,
                       dl.asking_price, dl.created_at,
                       u.name AS creator_name
                FROM deal_listings dl
                JOIN users u ON dl.creator_id = u.id
                WHERE dl.listing_type = 'seek_cowriter'
                  AND dl.status = 'active'
                  AND ($1::text IS NULL OR dl.genre ILIKE $1)
                ORDER BY dl.created_at DESC LIMIT 5
                """,
                f"%{genre}%" if genre else None,
            )
            for i, r in enumerate(rows):
                row = self._serialize_row(dict(r))
                row["compatibility_score"] = max(55, 90 - i * 7)
                row["match_type"] = "cowriter"
                matches.append(row)

        elif listing_type in ("sell_master_points", "sell_publishing_points", "offer_beat"):
            # Match from active seek_producer listings
            rows = await self.db_fetch(
                """
                SELECT dl.id, dl.creator_id, dl.title, dl.genre, dl.description,
                       dl.asking_price, dl.accept_points, dl.created_at,
                       u.name AS creator_name
                FROM deal_listings dl
                JOIN users u ON dl.creator_id = u.id
                WHERE dl.listing_type = 'seek_producer'
                  AND dl.status = 'active'
                  AND ($1::text IS NULL OR dl.genre ILIKE $1)
                ORDER BY dl.created_at DESC LIMIT 5
                """,
                f"%{genre}%" if genre else None,
            )
            for i, r in enumerate(rows):
                row = self._serialize_row(dict(r))
                row["compatibility_score"] = max(55, 88 - i * 7)
                row["match_type"] = "artist_seeking_producer"
                matches.append(row)

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"matches": matches, "count": len(matches)},
        )

    # ── Rights Valuation AI ──────────────────────────────────────────

    async def _task_rights_valuation(self, task: AgentTask) -> AgentResult:
        p = task.payload
        release_id = p.get("release_id")
        rights_type = p.get("rights_type", "master")  # master|publishing|sync|full
        territory = p.get("territory", "worldwide")

        # Pull revenue data from DB
        rev = await self.db_fetchrow(
            """
            SELECT COALESCE(SUM(gross_amount), 0) as total_gross,
                   COUNT(DISTINCT period_start) as period_count
            FROM royalties
            WHERE release_id = $1::uuid
            """,
            release_id,
        ) if release_id else None

        total_revenue = float(rev["total_gross"]) if rev else 0.0
        periods = int(rev["period_count"]) if rev else 0

        # Annualize revenue
        annual_revenue = total_revenue if periods <= 4 else total_revenue / max(periods / 4, 1)
        if annual_revenue < 1000:
            annual_revenue = 5000.0  # floor for illustrative purposes

        # Base multiples by rights type
        MULTIPLES = {
            "master":     (10.0, 12.5, 15.0),
            "publishing": (12.0, 15.0, 18.0),
            "sync":       (5.0, 6.5, 8.0),
            "full":       (11.0, 14.0, 17.0),
        }
        low_mult, mid_mult, high_mult = MULTIPLES.get(rights_type, MULTIPLES["master"])

        # Full catalog premium
        if rights_type == "full":
            low_mult *= 1.10
            mid_mult *= 1.10
            high_mult *= 1.10

        # Artist catalog depth modifier
        release_count = 0
        artist_id_row = None
        if release_id:
            artist_id_row = await self.db_fetchrow(
                "SELECT artist_id FROM releases WHERE id = $1::uuid", release_id
            )
        if artist_id_row:
            rc = await self.db_fetchrow(
                "SELECT COUNT(*) as cnt FROM releases WHERE artist_id = $1::uuid AND status = 'distributed'",
                artist_id_row["artist_id"],
            )
            release_count = int(rc["cnt"]) if rc else 0

        depth_mod = 1.0
        if release_count >= 10:
            depth_mod = 1.20
        elif release_count >= 5:
            depth_mod = 1.10
        elif release_count <= 1:
            depth_mod = 0.85

        # Trend momentum modifier (use echo_score as proxy)
        trend_mod = 1.0
        if artist_id_row:
            artist = await self.db_fetchrow(
                "SELECT echo_score FROM artists WHERE id = $1::uuid", artist_id_row["artist_id"]
            )
            if artist:
                score = int(artist.get("echo_score") or 50)
                if score >= 75:
                    trend_mod = 1.15
                elif score <= 30:
                    trend_mod = 0.85

        # Territory modifier
        TERRITORY_MODS = {
            "worldwide": 1.0,
            "us": 0.6,
            "us_only": 0.6,
            "eu": 0.4,
            "eu_only": 0.4,
        }
        territory_mod = TERRITORY_MODS.get(territory.lower().replace(" ", "_"), 1.0)

        combined_mod = depth_mod * trend_mod * territory_mod

        val_low = round(annual_revenue * low_mult * combined_mod, 2)
        val_mid = round(annual_revenue * mid_mult * combined_mod, 2)
        val_high = round(annual_revenue * high_mult * combined_mod, 2)
        multiple_used = round(mid_mult * combined_mod, 2)

        # Famous comparable deals (hardcoded reference)
        COMPARABLE_DEALS = [
            {
                "deal": "Bruce Springsteen catalog sale to Sony Music",
                "year": 2021,
                "value": "$500M",
                "multiple": "~25x annual earnings",
                "note": "Iconic legacy catalog premium",
            },
            {
                "deal": "Justin Bieber publishing rights sale to Hipgnosis",
                "year": 2023,
                "value": "$200M",
                "multiple": "~18x annual publishing income",
                "note": "Pop catalog with strong sync and streaming income",
            },
            {
                "deal": "Imagine Dragons catalog acquisition",
                "year": 2022,
                "value": "$100M",
                "multiple": "~15x annual revenue",
                "note": "Active touring artist with strong sync history",
            },
        ]

        methodology = (
            f"{rights_type.capitalize()} rights valued at {low_mult:.1f}-{high_mult:.1f}x annual revenue "
            f"({territory} territory). Modifiers applied: catalog depth ({depth_mod:.2f}x), "
            f"trend momentum ({trend_mod:.2f}x), territory ({territory_mod:.2f}x)."
        )

        logger.info(f"[DealRoom] Rights valuation: {rights_type}/{territory} — ${val_mid:,.0f} mid")
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "rights_type": rights_type,
                "territory": territory,
                "annual_revenue_basis": round(annual_revenue, 2),
                "valuation_low": val_low,
                "valuation_mid": val_mid,
                "valuation_high": val_high,
                "multiple_used": multiple_used,
                "methodology": methodology,
                "comparable_deals": COMPARABLE_DEALS,
                "hero_skill": "rights_valuation_ai",
            },
        )

    # ── Background Loops ─────────────────────────────────────────────

    async def _expired_listings_loop(self):
        """Every hour: close expired listings and notify creators."""
        while self._running:
            try:
                expired = await self.db_fetch(
                    """
                    UPDATE deal_listings
                    SET status = 'expired', closed_at = NOW()
                    WHERE status = 'active' AND expires_at < NOW()
                    RETURNING id, creator_id, title
                    """
                )
                for listing in expired:
                    await self.send_message("comms", "notification", {
                        "user_id": str(listing["creator_id"]),
                        "type": "listing_expired",
                        "subject": f"Listing expired: '{listing['title']}'",
                        "body": "Your Deal Room listing has expired. You can re-list at any time.",
                        "metadata": {"listing_id": str(listing["id"])},
                    })
                    logger.info(f"[DealRoom] Expired listing {listing['id']}")
            except Exception as e:
                logger.error(f"[DealRoom] Expired listings loop error: {e}")
            await asyncio.sleep(3600)

    async def _deal_nudge_loop(self):
        """Every 6 hours: nudge stale pending offers and unsigned contracts."""
        while self._running:
            try:
                stale_offers = await self.db_fetch(
                    """
                    SELECT do2.id, do2.listing_id,
                           dl.creator_id, dl.title
                    FROM deal_offers do2
                    JOIN deal_listings dl ON do2.listing_id = dl.id
                    WHERE do2.status = 'pending'
                      AND do2.created_at < NOW() - INTERVAL '48 hours'
                    LIMIT 20
                    """
                )
                for offer in stale_offers:
                    await self.send_message("comms", "notification", {
                        "user_id": str(offer["creator_id"]),
                        "type": "pending_offer_reminder",
                        "subject": f"Offer waiting — '{offer['title']}'",
                        "body": "You have a pending offer over 48 hours old. Accept, counter, or decline.",
                        "metadata": {"offer_id": str(offer["id"])},
                    })

                stale_contracts = await self.db_fetch(
                    """
                    SELECT d.id, d.seller_id, d.buyer_id,
                           dl.title
                    FROM deals d
                    JOIN deal_listings dl ON d.listing_id = dl.id
                    WHERE d.status = 'pending_contract'
                      AND d.created_at < NOW() - INTERVAL '72 hours'
                    LIMIT 20
                    """
                )
                for deal in stale_contracts:
                    for uid in (str(deal["seller_id"]), str(deal["buyer_id"])):
                        await self.send_message("comms", "notification", {
                            "user_id": uid,
                            "type": "contract_signature_reminder",
                            "subject": f"Contract awaiting signature — '{deal['title']}'",
                            "body": "Your Deal Room contract has been waiting 72+ hours. Please review and sign.",
                            "metadata": {"deal_id": str(deal["id"])},
                        })
            except Exception as e:
                logger.error(f"[DealRoom] Nudge loop error: {e}")
            await asyncio.sleep(21600)

    # ── Default ──────────────────────────────────────────────────────

    async def _task_default(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            success=False, task_id=task.task_id, agent_id=self.agent_id,
            error=f"Unknown task type: {task.task_type}",
        )

    # ── Helpers ──────────────────────────────────────────────────────

    def _serialize_row(self, row: dict) -> dict:
        out = {}
        for k, v in row.items():
            if hasattr(v, "hex"):
                out[k] = str(v)
            elif hasattr(v, "isoformat"):
                out[k] = v.isoformat()
            elif isinstance(v, list):
                out[k] = v
            else:
                out[k] = v
        return out

    def _serialize_rows(self, rows: list) -> list:
        return [self._serialize_row(dict(r)) for r in rows]
