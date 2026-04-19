"""
ECHO Vault Agent — Points Store & Exchange
The money engine. Manages all ECHO Points transactions, pricing, payouts, and the Exchange.

CRITICAL LANGUAGE RULE: NEVER use "invest", "investment", "ROI", "returns" anywhere.
Always use: "buy", "purchase", "own", "earn", "points", "royalties"
"""
import asyncio
import json
import logging
import math
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Artist tiers and price ranges per point
PRICE_TIERS = {
    "new":         {"min": 100,   "max": 300,   "listeners_max": 10000},
    "rising":      {"min": 300,   "max": 1500,  "listeners_max": 50000},
    "established": {"min": 1500,  "max": 8000,  "listeners_max": 200000},
    "star":        {"min": 8000,  "max": 40000, "listeners_max": float("inf")},
}

FACILITATOR_FEE_STORE = Decimal("0.05")       # 5% on store purchases
FACILITATOR_FEE_EXCHANGE = Decimal("0.025")   # 2.5% per side on exchange
MARKETING_RULE_PCT = Decimal("0.80")          # 80% of artist point sales → marketing
ARTIST_POCKET_PCT = Decimal("0.20")           # 20% → artist
HOLDING_PERIOD_DAYS = 365                      # 12-month lock before Exchange resale allowed
MAX_POINTS_PER_TRACK = Decimal("25")          # Max sold to fans per track
ARTIST_MIN_RETAINED = Decimal("30")           # Artist always keeps 30 pts minimum
MARKET_MAKER_SPREAD = Decimal("0.05")         # ±5% spread on Exchange
QUARTERLY_PAYOUT_MONTHS = {1: 15, 4: 15, 7: 15, 10: 15}  # month: day
MIN_PAYOUT_USD = Decimal("50.00")


class VaultAgent(BaseAgent):
    agent_id = "vault"
    agent_name = "Vault Agent"
    subscriptions = ["points.new", "points.purchase", "agent.vault", "exchange.order"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        asyncio.create_task(self._payout_checker_loop())
        asyncio.create_task(self._exchange_monitor_loop())
        asyncio.create_task(self._dynamic_pricing_loop())
        logger.info("[Vault] Online. Points Store + Exchange active.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "price_points": self._task_price_points,
            "create_drop": self._task_create_drop,
            "process_purchase": self._task_process_purchase,
            "calculate_holder_payouts": self._task_calculate_holder_payouts,
            "process_quarterly_payout": self._task_process_quarterly_payout,
            "exchange_list": self._task_exchange_list,
            "exchange_buy": self._task_exchange_buy,
            "exchange_sell": self._task_exchange_sell,
            "get_portfolio": self._task_get_portfolio,
            "ai_confidence_score": self._task_ai_confidence_score,
            "enforce_marketing_rule": self._task_enforce_marketing_rule,
            "check_manipulation": self._task_check_manipulation,
            "demand_forecast": self._task_demand_forecast,
        }
        handler = handlers.get(task.task_type, self._task_default)
        return await handler(task)

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _task_price_points(self, task: AgentTask) -> AgentResult:
        monthly_listeners = task.payload.get("monthly_listeners", 0)
        growth_rate = task.payload.get("growth_rate_pct", 0)  # monthly % growth
        genre = task.payload.get("genre", "")

        # Determine tier
        tier = "star"
        for t, data in PRICE_TIERS.items():
            if monthly_listeners <= data["listeners_max"]:
                tier = t
                break

        tier_data = PRICE_TIERS[tier]
        base_price = Decimal(str((tier_data["min"] + tier_data["max"]) / 2))

        # Growth multiplier: faster growth = higher price
        if growth_rate > 50:
            multiplier = Decimal("1.3")
        elif growth_rate > 20:
            multiplier = Decimal("1.15")
        elif growth_rate > 0:
            multiplier = Decimal("1.0")
        else:
            multiplier = Decimal("0.85")

        recommended_price = (base_price * multiplier).quantize(Decimal("1"), ROUND_HALF_UP)

        # AI Confidence Score (0-100)
        confidence = min(100, int(
            (monthly_listeners / 1000) * 0.4 +
            min(growth_rate, 100) * 0.3 +
            50 * 0.3  # base confidence
        ))

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "tier": tier,
                "recommended_price_per_point": float(recommended_price),
                "price_range": {"min": tier_data["min"], "max": tier_data["max"]},
                "ai_confidence_score": confidence,
                "multiplier": float(multiplier),
                "rationale": f"{tier.capitalize()} tier artist, {growth_rate}% monthly growth",
            }
        )

    async def _task_create_drop(self, task: AgentTask) -> AgentResult:
        artist_id = task.payload.get("artist_id") or task.artist_id
        track_id = task.payload.get("track_id")
        release_id = task.payload.get("release_id") or task.release_id
        points_to_sell = Decimal(str(task.payload.get("points_to_sell", 0)))
        price_per_point = Decimal(str(task.payload.get("price_per_point", 0)))
        early_bird_discount = Decimal(str(task.payload.get("early_bird_discount_pct", 0.20)))

        if not track_id or not artist_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="artist_id and track_id required",
            )
        if points_to_sell <= 0 or price_per_point <= 0:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="points_to_sell and price_per_point must be positive",
            )
        if points_to_sell > MAX_POINTS_PER_TRACK:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error=f"Cannot sell more than {MAX_POINTS_PER_TRACK} points per track",
            )

        # Check existing drops don't push total past 25
        existing = await self.db_fetchrow(
            """
            SELECT COALESCE(SUM(total_points_available), 0) as already_listed
            FROM point_drops
            WHERE track_id = $1::uuid AND status IN ('active', 'sold_out')
            """,
            track_id,
        )
        already_listed = Decimal(str(existing["already_listed"])) if existing else Decimal("0")
        if already_listed + points_to_sell > MAX_POINTS_PER_TRACK:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error=f"Total points across all drops ({float(already_listed + points_to_sell)}) would exceed {MAX_POINTS_PER_TRACK} max per track",
            )

        # KYC: artist must exist and be in valid status
        artist = await self.db_fetchrow(
            "SELECT id, name, status, monthly_listeners FROM artists WHERE id = $1::uuid",
            artist_id,
        )
        if not artist:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="Artist not found",
            )
        if artist["status"] not in ("signed", "active", "prospect"):
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error=f"Artist KYC/status check failed: status is '{artist['status']}'",
            )

        # Revenue projections
        gross_revenue = (points_to_sell * price_per_point).quantize(Decimal("0.01"), ROUND_HALF_UP)
        facilitator_fee = (gross_revenue * FACILITATOR_FEE_STORE).quantize(Decimal("0.01"), ROUND_HALF_UP)
        net_revenue = gross_revenue - facilitator_fee
        marketing_budget = (net_revenue * MARKETING_RULE_PCT).quantize(Decimal("0.01"), ROUND_HALF_UP)
        artist_proceeds = (net_revenue * ARTIST_POCKET_PCT).quantize(Decimal("0.01"), ROUND_HALF_UP)

        import uuid
        drop_id = str(uuid.uuid4())
        early_bird_ends = datetime.now(timezone.utc) + timedelta(days=7)
        closes_at = datetime.now(timezone.utc) + timedelta(days=90)
        ai_confidence = min(100, int((artist.get("monthly_listeners") or 0) / 1000 * 0.4 + 30))

        await self.db_execute(
            """
            INSERT INTO point_drops (
                id, track_id, release_id, artist_id,
                total_points_available, price_per_point,
                early_bird_discount_pct, early_bird_ends_at,
                ai_confidence_score, status, marketing_budget_allocated, closes_at
            )
            VALUES (
                $1::uuid, $2::uuid, $3::uuid, $4::uuid,
                $5, $6,
                $7, $8,
                $9, 'active', $10, $11
            )
            """,
            drop_id, track_id, release_id, artist_id,
            float(points_to_sell), float(price_per_point),
            float(early_bird_discount), early_bird_ends,
            ai_confidence, float(marketing_budget), closes_at,
        )

        await self.log_audit(
            "create_drop", "point_drops", drop_id,
            {"artist_id": artist_id, "track_id": track_id, "points": float(points_to_sell), "price": float(price_per_point)},
        )

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "drop_id": drop_id,
                "track_id": track_id,
                "artist_id": artist_id,
                "points_to_sell": float(points_to_sell),
                "price_per_point": float(price_per_point),
                "revenue_if_sold_out": {
                    "gross": float(gross_revenue),
                    "facilitator_fee": float(facilitator_fee),
                    "net": float(net_revenue),
                    "marketing_budget": float(marketing_budget),
                    "artist_proceeds": float(artist_proceeds),
                },
                "early_bird_discount_pct": float(early_bird_discount),
                "early_bird_ends_at": early_bird_ends.isoformat(),
                "ai_confidence_score": ai_confidence,
                "closes_at": closes_at.isoformat(),
                "status": "active",
            }
        )

    async def _task_process_purchase(self, task: AgentTask) -> AgentResult:
        track_id = task.payload.get("track_id")
        buyer_user_id = task.payload.get("buyer_user_id")
        points_qty = Decimal(str(task.payload.get("points_qty", 0)))
        price_per_point = Decimal(str(task.payload.get("price_per_point", 0)))
        stripe_payment_id = task.payload.get("stripe_payment_id")

        if not track_id or not buyer_user_id or points_qty <= 0:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="track_id, buyer_user_id, and positive points_qty required",
            )

        # Validate drop is active and has points available
        drop = await self.db_fetchrow(
            """
            SELECT id, total_points_available, points_sold, price_per_point, artist_id, status
            FROM point_drops
            WHERE track_id = $1::uuid AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
            """,
            track_id,
        )
        if not drop:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="No active drop found for this track",
            )

        available = Decimal(str(drop["total_points_available"])) - Decimal(str(drop["points_sold"]))
        if points_qty > available:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error=f"Only {float(available)} points remaining in this drop",
            )

        # Validate buyer KYC
        buyer = await self.db_fetchrow(
            "SELECT id, status FROM users WHERE id = $1::uuid",
            buyer_user_id,
        )
        if not buyer or buyer["status"] not in ("active",):
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="Buyer KYC check failed or user not found",
            )

        if price_per_point <= 0:
            price_per_point = Decimal(str(drop["price_per_point"]))

        gross_amount = (points_qty * price_per_point).quantize(Decimal("0.01"), ROUND_HALF_UP)
        facilitator_fee = (gross_amount * FACILITATOR_FEE_STORE).quantize(Decimal("0.01"), ROUND_HALF_UP)
        net_amount = gross_amount - facilitator_fee
        marketing_allocation = (net_amount * MARKETING_RULE_PCT).quantize(Decimal("0.01"), ROUND_HALF_UP)
        artist_payment = (net_amount * ARTIST_POCKET_PCT).quantize(Decimal("0.01"), ROUND_HALF_UP)
        holding_ends = datetime.now(timezone.utc) + timedelta(days=HOLDING_PERIOD_DAYS)

        import uuid
        point_id = str(uuid.uuid4())

        await self.db_execute(
            """
            INSERT INTO echo_points (
                id, track_id, buyer_user_id, point_type,
                points_purchased, price_paid, price_per_point,
                holding_period_ends, status, stripe_payment_id
            )
            VALUES (
                $1::uuid, $2::uuid, $3::uuid, 'master',
                $4, $5, $6,
                $7, 'active', $8
            )
            """,
            point_id, track_id, buyer_user_id,
            float(points_qty), float(gross_amount), float(price_per_point),
            holding_ends, stripe_payment_id,
        )

        # Update drop points_sold
        await self.db_execute(
            """
            UPDATE point_drops
            SET points_sold = points_sold + $2,
                status = CASE
                    WHEN points_sold + $2 >= total_points_available THEN 'sold_out'
                    ELSE status
                END
            WHERE id = $1::uuid
            """,
            str(drop["id"]), float(points_qty),
        )

        await self.broadcast("points.sold", {
            "track_id": track_id,
            "buyer_user_id": buyer_user_id,
            "points_qty": float(points_qty),
            "gross_amount": float(gross_amount),
        })

        # 80% → marketing budget
        await self.broadcast("marketing.budget.add", {
            "track_id": track_id,
            "artist_id": str(drop["artist_id"]),
            "amount": float(marketing_allocation),
            "source": "points_sale",
        })

        await self.log_audit(
            "process_purchase", "echo_points", point_id,
            {"track_id": track_id, "buyer": buyer_user_id, "points": float(points_qty), "gross": float(gross_amount)},
        )

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "echo_point_id": point_id,
                "track_id": track_id,
                "buyer_user_id": buyer_user_id,
                "points_purchased": float(points_qty),
                "price_per_point": float(price_per_point),
                "gross_amount": float(gross_amount),
                "facilitator_fee": float(facilitator_fee),
                "net_amount": float(net_amount),
                "marketing_allocation": float(marketing_allocation),
                "artist_payment": float(artist_payment),
                "holding_period_ends": holding_ends.isoformat(),
                "license": {
                    "type": "fractional_master",
                    "royalty_per_point": "1% of master streaming revenue per point owned",
                    "tradeable_after": holding_ends.isoformat(),
                    "disclaimer": "NOT A GUARANTEE — estimated earnings based on comparable data",
                },
            }
        )

    async def _task_calculate_holder_payouts(self, task: AgentTask) -> AgentResult:
        track_id = task.payload.get("track_id")
        revenue_amount = Decimal(str(task.payload.get("revenue_amount", 0)))

        if not track_id or revenue_amount <= 0:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="track_id and positive revenue_amount required",
            )

        holders = await self.db_fetch(
            """
            SELECT id, buyer_user_id, points_purchased
            FROM echo_points
            WHERE track_id = $1::uuid AND status IN ('active', 'tradeable')
            ORDER BY points_purchased DESC
            """,
            track_id,
        )

        if not holders:
            return AgentResult(
                success=True, task_id=task.task_id, agent_id=self.agent_id,
                result={"track_id": track_id, "payouts": [], "total_to_holders": 0.0,
                        "revenue_amount": float(revenue_amount)},
            )

        payouts = []
        total_to_holders = Decimal("0")
        for h in holders:
            pts = Decimal(str(h["points_purchased"]))
            # Each point = 1% of revenue
            payout = (revenue_amount * pts / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
            if payout >= MIN_PAYOUT_USD:
                payouts.append({
                    "echo_point_id": str(h["id"]),
                    "user_id": str(h["buyer_user_id"]),
                    "points": float(pts),
                    "payout_amount": float(payout),
                })
                total_to_holders += payout

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "track_id": track_id,
                "revenue_amount": float(revenue_amount),
                "total_holders": len(holders),
                "holders_above_threshold": len(payouts),
                "holders_below_threshold": len(holders) - len(payouts),
                "total_to_holders": float(total_to_holders),
                "payouts": payouts,
            }
        )

    async def _task_process_quarterly_payout(self, task: AgentTask) -> AgentResult:
        now = datetime.now(timezone.utc)
        quarter_num = (now.month - 1) // 3 + 1
        quarter_label = task.payload.get("quarter", f"{now.year}-Q{quarter_num}")

        # Get all tracks with undistributed royalty revenue
        tracks = await self.db_fetch(
            """
            SELECT DISTINCT t.id as track_id, t.title,
                COALESCE(SUM(r.net_amount), 0) as revenue_pool
            FROM tracks t
            JOIN royalties r ON r.track_id = t.id
            WHERE r.distributed = FALSE
            GROUP BY t.id, t.title
            HAVING SUM(r.net_amount) > 0
            """
        )

        all_payouts = []
        total_paid = Decimal("0")
        by_track = []

        for track in tracks:
            track_id = str(track["track_id"])
            revenue_pool = Decimal(str(track["revenue_pool"]))

            holders = await self.db_fetch(
                """
                SELECT id, buyer_user_id, points_purchased
                FROM echo_points
                WHERE track_id = $1::uuid AND status IN ('active', 'tradeable')
                """,
                track_id,
            )

            track_payouts = []
            track_total = Decimal("0")

            for h in holders:
                pts = Decimal(str(h["points_purchased"]))
                payout = (revenue_pool * pts / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
                if payout < MIN_PAYOUT_USD:
                    continue

                import uuid as _uuid
                payout_id = str(_uuid.uuid4())
                await self.db_execute(
                    """
                    INSERT INTO point_payouts (
                        id, user_id, track_id, echo_point_id,
                        quarter, points_held, revenue_pool, payout_amount, status
                    )
                    VALUES (
                        $1::uuid, $2::uuid, $3::uuid, $4::uuid,
                        $5, $6, $7, $8, 'pending'
                    )
                    """,
                    payout_id, str(h["buyer_user_id"]), track_id, str(h["id"]),
                    quarter_label, float(pts), float(revenue_pool), float(payout),
                )

                await self.db_execute(
                    "UPDATE echo_points SET royalties_earned = royalties_earned + $2 WHERE id = $1::uuid",
                    str(h["id"]), float(payout),
                )

                track_payouts.append({
                    "payout_id": payout_id,
                    "user_id": str(h["buyer_user_id"]),
                    "points": float(pts),
                    "payout_amount": float(payout),
                })
                track_total += payout

            if track_payouts:
                by_track.append({
                    "track_id": track_id,
                    "track_title": track["title"],
                    "revenue_pool": float(revenue_pool),
                    "holders_paid": len(track_payouts),
                    "total_paid": float(track_total),
                })
                all_payouts.extend(track_payouts)
                total_paid += track_total

        await self.broadcast("payout.ready", {
            "quarter": quarter_label,
            "total_paid": float(total_paid),
            "num_payouts": len(all_payouts),
            "by_track": by_track,
            "source": "vault",
        })

        await self.log_audit(
            "process_quarterly_payout", "point_payouts",
            details={"quarter": quarter_label, "total_paid": float(total_paid), "payouts": len(all_payouts)},
        )

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "quarter": quarter_label,
                "total_paid": float(total_paid),
                "num_holders": len(all_payouts),
                "by_track": by_track,
            }
        )

    async def _task_exchange_list(self, task: AgentTask) -> AgentResult:
        echo_point_id = task.payload.get("echo_point_id")
        list_price = Decimal(str(task.payload.get("list_price", 0)))
        list_type = task.payload.get("list_type", "sell")  # "buy" or "sell"
        user_id = task.payload.get("user_id")
        points_qty = Decimal(str(task.payload.get("points_qty", 0)))

        if not user_id or list_price <= 0:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="user_id and positive list_price required",
            )

        track_id = None
        if list_type == "sell":
            if not echo_point_id:
                return AgentResult(
                    success=False, task_id=task.task_id, agent_id=self.agent_id,
                    error="echo_point_id required for sell orders",
                )
            # Validate seller owns the points and holding period has passed
            point = await self.db_fetchrow(
                """
                SELECT id, track_id, buyer_user_id, points_purchased, holding_period_ends, status
                FROM echo_points WHERE id = $1::uuid
                """,
                echo_point_id,
            )
            if not point:
                return AgentResult(
                    success=False, task_id=task.task_id, agent_id=self.agent_id,
                    error="Echo point not found",
                )
            if str(point["buyer_user_id"]) != str(user_id):
                return AgentResult(
                    success=False, task_id=task.task_id, agent_id=self.agent_id,
                    error="You do not own these points",
                )
            if point["holding_period_ends"] and point["holding_period_ends"] > datetime.now(timezone.utc):
                days_left = (point["holding_period_ends"] - datetime.now(timezone.utc)).days
                return AgentResult(
                    success=False, task_id=task.task_id, agent_id=self.agent_id,
                    error=f"Holding period not yet complete. {days_left} days remaining.",
                )
            track_id = str(point["track_id"])
            if points_qty <= 0:
                points_qty = Decimal(str(point["points_purchased"]))
        else:
            track_id = task.payload.get("track_id")
            if not track_id or points_qty <= 0:
                return AgentResult(
                    success=False, task_id=task.task_id, agent_id=self.agent_id,
                    error="track_id and positive points_qty required for buy orders",
                )

        # Anti-manipulation: check for wash trading
        manip = await self._check_wash_trading(user_id, track_id)
        if manip.get("flagged"):
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="Order flagged: potential wash trading detected. Review required.",
            )

        import uuid as _uuid
        order_id = str(_uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)  # exchange order expiry (listing TTL, not hold period)

        await self.db_execute(
            """
            INSERT INTO exchange_orders (
                id, track_id, user_id, order_type,
                points_qty, price_per_point, status,
                echo_point_id, expires_at
            )
            VALUES (
                $1::uuid, $2::uuid, $3::uuid, $4,
                $5, $6, 'open',
                $7, $8
            )
            """,
            order_id, track_id, user_id, list_type,
            float(points_qty), float(list_price),
            echo_point_id, expires_at,
        )

        matched = await self._attempt_order_match(order_id, list_type, track_id, list_price, points_qty, user_id)

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "order_id": order_id,
                "track_id": track_id,
                "order_type": list_type,
                "points_qty": float(points_qty),
                "price_per_point": float(list_price),
                "status": "filled" if matched else "open",
                "matched": matched,
                "expires_at": expires_at.isoformat(),
            }
        )

    async def _task_exchange_buy(self, task: AgentTask) -> AgentResult:
        """Execute a market buy — immediately buy from best available sell order."""
        track_id = task.payload.get("track_id")
        buyer_id = task.payload.get("buyer_id")
        points_qty = Decimal(str(task.payload.get("points_qty", 0)))
        max_price = task.payload.get("max_price_per_point")

        if not track_id or not buyer_id or points_qty <= 0:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="track_id, buyer_id, and positive points_qty required",
            )

        query = """
            SELECT id, user_id, points_qty, price_per_point, echo_point_id,
                   points_qty - points_filled as qty_available
            FROM exchange_orders
            WHERE track_id = $1::uuid
              AND order_type = 'sell'
              AND status = 'open'
              AND user_id != $2::uuid
        """
        params = [track_id, buyer_id]
        if max_price:
            query += f" AND price_per_point <= ${len(params) + 1}"
            params.append(float(max_price))
        query += " ORDER BY price_per_point ASC LIMIT 1"

        sell_order = await self.db_fetchrow(query, *params)
        if not sell_order:
            return AgentResult(
                success=True, task_id=task.task_id, agent_id=self.agent_id,
                result={"status": "no_match", "message": "No matching sell orders available"},
            )

        fill_qty = min(points_qty, Decimal(str(sell_order["qty_available"])))
        trade_result = await self._execute_trade(
            sell_order_id=str(sell_order["id"]),
            buy_order_id=None,
            buyer_id=buyer_id,
            seller_id=str(sell_order["user_id"]),
            echo_point_id=str(sell_order["echo_point_id"]) if sell_order["echo_point_id"] else None,
            track_id=track_id,
            points_qty=fill_qty,
            price_per_point=Decimal(str(sell_order["price_per_point"])),
        )

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result=trade_result,
        )

    async def _task_exchange_sell(self, task: AgentTask) -> AgentResult:
        """Execute a market sell — immediately sell to best available buy order."""
        track_id = task.payload.get("track_id")
        seller_id = task.payload.get("seller_id")
        echo_point_id = task.payload.get("echo_point_id")
        points_qty = Decimal(str(task.payload.get("points_qty", 0)))
        min_price = task.payload.get("min_price_per_point")

        if not track_id or not seller_id or not echo_point_id or points_qty <= 0:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="track_id, seller_id, echo_point_id, and positive points_qty required",
            )

        query = """
            SELECT id, user_id, points_qty, price_per_point,
                   points_qty - points_filled as qty_available
            FROM exchange_orders
            WHERE track_id = $1::uuid
              AND order_type = 'buy'
              AND status = 'open'
              AND user_id != $2::uuid
        """
        params = [track_id, seller_id]
        if min_price:
            query += f" AND price_per_point >= ${len(params) + 1}"
            params.append(float(min_price))
        query += " ORDER BY price_per_point DESC LIMIT 1"

        buy_order = await self.db_fetchrow(query, *params)
        if not buy_order:
            return AgentResult(
                success=True, task_id=task.task_id, agent_id=self.agent_id,
                result={"status": "no_match", "message": "No matching buy orders available"},
            )

        fill_qty = min(points_qty, Decimal(str(buy_order["qty_available"])))
        trade_result = await self._execute_trade(
            sell_order_id=None,
            buy_order_id=str(buy_order["id"]),
            buyer_id=str(buy_order["user_id"]),
            seller_id=seller_id,
            echo_point_id=echo_point_id,
            track_id=track_id,
            points_qty=fill_qty,
            price_per_point=Decimal(str(buy_order["price_per_point"])),
        )

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result=trade_result,
        )

    async def _task_get_portfolio(self, task: AgentTask) -> AgentResult:
        user_id = task.payload.get("user_id")
        if not user_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="user_id required",
            )

        holdings = await self.db_fetch(
            """
            SELECT
                ep.id, ep.track_id, ep.points_purchased,
                ep.price_paid, ep.price_per_point as cost_per_point,
                ep.royalties_earned, ep.holding_period_ends, ep.status, ep.purchase_date,
                t.title as track_title,
                a.name as artist_name, a.genre,
                COALESCE(
                    (SELECT price_per_point FROM exchange_trades
                     WHERE track_id = ep.track_id ORDER BY traded_at DESC LIMIT 1),
                    ep.price_per_point
                ) as current_price_per_point
            FROM echo_points ep
            JOIN tracks t ON ep.track_id = t.id
            JOIN artists a ON t.artist_id = a.id
            WHERE ep.buyer_user_id = $1::uuid AND ep.status IN ('active', 'tradeable')
            ORDER BY ep.purchase_date DESC
            """,
            user_id,
        )

        total_cost_basis = Decimal("0")
        total_current_value = Decimal("0")
        total_royalties = Decimal("0")
        items = []

        for h in holdings:
            pts = Decimal(str(h["points_purchased"]))
            cost_per = Decimal(str(h["cost_per_point"]))
            current_per = Decimal(str(h["current_price_per_point"]))
            cost_basis = (pts * cost_per).quantize(Decimal("0.01"), ROUND_HALF_UP)
            current_value = (pts * current_per).quantize(Decimal("0.01"), ROUND_HALF_UP)
            unrealized_gain = (current_value - cost_basis).quantize(Decimal("0.01"), ROUND_HALF_UP)
            royalties = Decimal(str(h["royalties_earned"]))
            total_cost_basis += cost_basis
            total_current_value += current_value
            total_royalties += royalties

            holding_ends = h["holding_period_ends"]
            tradeable = h["status"] == "tradeable" or (
                holding_ends and holding_ends <= datetime.now(timezone.utc)
            )
            items.append({
                "echo_point_id": str(h["id"]),
                "track_id": str(h["track_id"]),
                "track_title": h["track_title"],
                "artist_name": h["artist_name"],
                "genre": h["genre"],
                "points_owned": float(pts),
                "cost_per_point": float(cost_per),
                "cost_basis": float(cost_basis),
                "current_price_per_point": float(current_per),
                "current_value": float(current_value),
                "unrealized_gain": float(unrealized_gain),
                "royalties_earned": float(royalties),
                "status": h["status"],
                "holding_period_ends": holding_ends.isoformat() if holding_ends else None,
                "tradeable": tradeable,
            })

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "user_id": user_id,
                "holdings": items,
                "summary": {
                    "total_cost_basis": float(total_cost_basis),
                    "total_current_value": float(total_current_value),
                    "total_unrealized_gain": float(total_current_value - total_cost_basis),
                    "total_royalties_earned": float(total_royalties),
                    "num_holdings": len(items),
                },
            }
        )

    async def _task_ai_confidence_score(self, task: AgentTask) -> AgentResult:
        artist_id = task.payload.get("artist_id") or task.artist_id
        if not artist_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="artist_id required",
            )

        artist = await self.db_fetchrow(
            "SELECT id, name, monthly_listeners, echo_score, genre, total_streams, tier FROM artists WHERE id = $1::uuid",
            artist_id,
        )
        if not artist:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="Artist not found",
            )

        monthly_listeners = int(artist.get("monthly_listeners") or 0)
        total_streams = int(artist.get("total_streams") or 0)
        echo_score = float(artist.get("echo_score") or 0)

        # Monthly listeners: 0–30 pts, log scale
        listeners_score = (
            min(30, int(math.log10(monthly_listeners + 1) / math.log10(1_000_001) * 30))
            if monthly_listeners > 0 else 0
        )

        # Growth rate (proxy via echo_score): 0–25 pts
        growth_score = min(25, int(echo_score / 100 * 25))

        # Engagement (streams / monthly_listeners): 0–20 pts
        if monthly_listeners > 0 and total_streams > 0:
            streams_per_listener = total_streams / monthly_listeners
            engagement_score = min(20, int(streams_per_listener / 100 * 20))
        else:
            engagement_score = 5  # base

        # Release consistency: tracks in last 12 months: 0–15 pts
        recent_tracks = await self.db_fetchrow(
            "SELECT COUNT(*) as cnt FROM tracks WHERE artist_id = $1::uuid AND created_at >= NOW() - INTERVAL '12 months'",
            artist_id,
        )
        track_count = int(recent_tracks["cnt"]) if recent_tracks else 0
        consistency_score = min(15, track_count * 3)

        # Revenue per stream: 0–10 pts
        royalty_row = await self.db_fetchrow(
            "SELECT COALESCE(SUM(net_amount), 0) as total_revenue FROM royalties WHERE artist_id = $1::uuid",
            artist_id,
        )
        total_revenue = float(royalty_row["total_revenue"]) if royalty_row else 0.0
        if total_streams > 0 and total_revenue > 0:
            revenue_per_stream = total_revenue / total_streams
            revenue_score = min(10, int(revenue_per_stream * 10_000))
        else:
            revenue_score = 0

        total_score = listeners_score + growth_score + engagement_score + consistency_score + revenue_score

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "artist_id": artist_id,
                "artist_name": artist["name"],
                "ai_confidence_score": total_score,
                "breakdown": {
                    "monthly_listeners": {"score": listeners_score, "max": 30, "value": monthly_listeners},
                    "growth_signal": {"score": growth_score, "max": 25, "value": echo_score},
                    "engagement": {"score": engagement_score, "max": 20},
                    "release_consistency": {"score": consistency_score, "max": 15, "tracks_last_12mo": track_count},
                    "revenue_per_stream": {"score": revenue_score, "max": 10},
                },
                "disclaimer": "NOT A GUARANTEE — predictive estimate based on comparable data",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _task_enforce_marketing_rule(self, task: AgentTask) -> AgentResult:
        point_sale_id = task.payload.get("point_sale_id")
        if not point_sale_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="point_sale_id required",
            )

        point = await self.db_fetchrow(
            "SELECT id, track_id, price_paid FROM echo_points WHERE id = $1::uuid",
            point_sale_id,
        )
        if not point:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="Point sale record not found",
            )

        price_paid = Decimal(str(point["price_paid"]))
        fee = (price_paid * FACILITATOR_FEE_STORE).quantize(Decimal("0.01"), ROUND_HALF_UP)
        net = price_paid - fee
        expected_marketing = (net * MARKETING_RULE_PCT).quantize(Decimal("0.01"), ROUND_HALF_UP)

        drop = await self.db_fetchrow(
            """
            SELECT id, marketing_budget_allocated FROM point_drops
            WHERE track_id = $1::uuid ORDER BY created_at DESC LIMIT 1
            """,
            str(point["track_id"]),
        )

        compliant = False
        actual_marketing = Decimal("0")
        if drop:
            actual_marketing = Decimal(str(drop["marketing_budget_allocated"]))
            compliant = actual_marketing >= expected_marketing * Decimal("0.95")  # 5% tolerance

        if not compliant:
            await self.broadcast("compliance.violation", {
                "type": "marketing_rule_80pct",
                "point_sale_id": point_sale_id,
                "expected_marketing": float(expected_marketing),
                "actual_marketing": float(actual_marketing),
                "shortfall": float(expected_marketing - actual_marketing),
                "severity": "high",
            })
            await self.send_message("ceo", "compliance.alert", {
                "violation": "marketing_rule_80pct",
                "point_sale_id": point_sale_id,
                "details": f"Marketing allocation shortfall: expected ${float(expected_marketing):.2f}, actual ${float(actual_marketing):.2f}",
            })

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "point_sale_id": point_sale_id,
                "compliant": compliant,
                "price_paid": float(price_paid),
                "expected_marketing_allocation": float(expected_marketing),
                "actual_marketing_allocation": float(actual_marketing),
                "violation_flagged": not compliant,
                "status": "compliant" if compliant else "violation_flagged",
            }
        )

    async def _task_check_manipulation(self, task: AgentTask) -> AgentResult:
        track_id = task.payload.get("track_id")
        if not track_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="track_id required",
            )

        flags = []
        circuit_breaker_triggered = False
        cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)

        # 1. Wash trading: same user as both buyer and seller within 24h
        wash_rows = await self.db_fetch(
            """
            SELECT buyer_id, seller_id, COUNT(*) as trades
            FROM exchange_trades
            WHERE track_id = $1::uuid AND traded_at >= $2
            GROUP BY buyer_id, seller_id
            HAVING buyer_id = seller_id
            """,
            track_id, cutoff_24h,
        )
        for row in wash_rows:
            flags.append({
                "type": "wash_trading",
                "user_id": str(row["buyer_id"]),
                "trades_in_24h": int(row["trades"]),
                "severity": "critical",
            })

        # 2. Circuit breaker: price movement > 20% in 24h
        prices = await self.db_fetch(
            """
            SELECT price_per_point, traded_at FROM exchange_trades
            WHERE track_id = $1::uuid AND traded_at >= $2
            ORDER BY traded_at ASC
            """,
            track_id, cutoff_24h,
        )
        if len(prices) >= 2:
            oldest_price = Decimal(str(prices[0]["price_per_point"]))
            newest_price = Decimal(str(prices[-1]["price_per_point"]))
            if oldest_price > 0:
                change_pct = abs((newest_price - oldest_price) / oldest_price * 100)
                if change_pct > Decimal("20"):
                    circuit_breaker_triggered = True
                    flags.append({
                        "type": "circuit_breaker",
                        "price_change_pct": float(change_pct),
                        "from_price": float(oldest_price),
                        "to_price": float(newest_price),
                        "severity": "high",
                    })

        # 3. High volume: > 10% of total points in one day
        volume_row = await self.db_fetchrow(
            "SELECT COALESCE(SUM(points_qty), 0) as daily_volume FROM exchange_trades WHERE track_id = $1::uuid AND traded_at >= $2",
            track_id, cutoff_24h,
        )
        total_pts_row = await self.db_fetchrow(
            "SELECT COALESCE(SUM(points_purchased), 0) as total FROM echo_points WHERE track_id = $1::uuid AND status IN ('active', 'tradeable')",
            track_id,
        )
        if volume_row and total_pts_row:
            daily_volume = Decimal(str(volume_row["daily_volume"]))
            total_points = Decimal(str(total_pts_row["total"]))
            if total_points > 0 and (daily_volume / total_points) > Decimal("0.10"):
                flags.append({
                    "type": "high_volume",
                    "daily_volume": float(daily_volume),
                    "total_points": float(total_points),
                    "volume_pct": float(daily_volume / total_points * 100),
                    "severity": "medium",
                })

        if flags:
            await self.broadcast("exchange.manipulation_alert", {
                "track_id": track_id,
                "flags": flags,
                "circuit_breaker_triggered": circuit_breaker_triggered,
            })

        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "track_id": track_id,
                "clean": len(flags) == 0,
                "flags": flags,
                "circuit_breaker_triggered": circuit_breaker_triggered,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _task_demand_forecast(self, task: AgentTask) -> AgentResult:
        release_id = task.payload.get("release_id")
        artist_id = task.payload.get("artist_id")
        points_available = int(task.payload.get("points_available") or 100)
        price_per_point = float(task.payload.get("price_per_point") or 0.0)

        # Get Melodio Score from DB (default 50)
        melodio_score = 50
        if artist_id:
            artist = await self.db_fetchrow(
                "SELECT echo_score, genre FROM artists WHERE id = $1::uuid", artist_id
            )
            if artist:
                melodio_score = int(artist.get("echo_score") or 50)
                genre = (artist.get("genre") or "other").lower()
            else:
                genre = "other"
        else:
            genre = "other"

        # Historical sell-through from previous drops
        hist = await self.db_fetchrow(
            """
            SELECT COUNT(*) as drop_count,
                   COALESCE(AVG(points_purchased), 0) as avg_purchased
            FROM echo_points
            WHERE artist_id = $1::uuid
            """,
            artist_id,
        ) if artist_id else None
        hist_drops = int(hist["drop_count"]) if hist else 0
        hist_avg = float(hist["avg_purchased"]) if hist else 0.0

        # Genre popularity multiplier
        GENRE_MULTIPLIERS = {
            "pop": 1.5,
            "hip-hop": 1.3,
            "r&b": 1.2,
            "electronic": 1.2,
            "indie": 1.0,
            "rock": 1.0,
            "other": 1.0,
        }
        genre_mult = GENRE_MULTIPLIERS.get(genre, 1.0)

        # Timing factor — Fridays get 1.4x
        from datetime import datetime as _dt
        today_dow = _dt.now().weekday()  # 0=Mon, 4=Fri
        days_to_friday = (4 - today_dow) % 7
        timing_note = "today is Friday" if today_dow == 4 else f"{days_to_friday} day(s) to next Friday"
        timing_mult = 1.4 if today_dow == 4 else 1.0

        # Base demand score from Melodio Score
        base_demand = min(100, melodio_score * 0.7 + 20)

        # Boost from historical data
        if hist_drops > 3:
            base_demand = min(100, base_demand + 10)
        if hist_avg > 5:
            base_demand = min(100, base_demand + 5)

        demand_score = int(min(100, base_demand * genre_mult))

        # Estimated sell-through in 7 days
        sellthrough_pct = round(min(100.0, demand_score * timing_mult), 1)

        # Optimal price suggestion — higher demand → can command premium
        if price_per_point > 0:
            if demand_score >= 75:
                optimal_price = round(price_per_point * 1.15, 2)
            elif demand_score >= 50:
                optimal_price = round(price_per_point * 1.0, 2)
            else:
                optimal_price = round(price_per_point * 0.90, 2)
        else:
            # Suggest based on score (rough USD range)
            optimal_price = round(max(1.0, demand_score * 0.5), 2)

        projected_revenue = round(points_available * (sellthrough_pct / 100) * optimal_price, 2)

        confidence = "high" if hist_drops >= 3 else ("medium" if hist_drops >= 1 else "low")

        recommended_drop_time = (
            f"Drop on Friday — {timing_note}. Best window: 9AM-12PM local time."
            if today_dow == 4
            else f"Wait for Friday ({timing_note}) for 40% higher demand. Best window: 9AM-12PM local time."
        )

        logger.info(f"[Vault] Demand forecast: score={demand_score}, sellthrough={sellthrough_pct}%")
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "release_id": release_id,
                "artist_id": artist_id,
                "demand_score": demand_score,
                "estimated_sellthrough_pct": sellthrough_pct,
                "projected_revenue": projected_revenue,
                "optimal_price": optimal_price,
                "recommended_drop_time": recommended_drop_time,
                "confidence": confidence,
                "hero_skill": "points_demand_engine",
            },
        )

    async def _task_default(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            success=False, task_id=task.task_id, agent_id=self.agent_id,
            error=f"Unknown task type: {task.task_type}",
        )

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    async def _attempt_order_match(
        self, order_id: str, order_type: str, track_id: str,
        price: Decimal, qty: Decimal, user_id: str,
    ) -> bool:
        """Try to immediately match a new order against existing opposing orders."""
        if order_type == "sell":
            match = await self.db_fetchrow(
                """
                SELECT id, user_id, points_qty, price_per_point,
                       points_qty - points_filled as qty_available
                FROM exchange_orders
                WHERE track_id = $1::uuid AND order_type = 'buy' AND status = 'open'
                  AND price_per_point >= $2 AND user_id != $3::uuid
                ORDER BY price_per_point DESC LIMIT 1
                """,
                track_id, float(price), user_id,
            )
            if match:
                fill_qty = min(qty, Decimal(str(match["qty_available"])))
                our_order = await self.db_fetchrow(
                    "SELECT echo_point_id FROM exchange_orders WHERE id = $1::uuid", order_id,
                )
                echo_point_id = str(our_order["echo_point_id"]) if our_order and our_order["echo_point_id"] else None
                await self._execute_trade(
                    sell_order_id=order_id, buy_order_id=str(match["id"]),
                    buyer_id=str(match["user_id"]), seller_id=user_id,
                    echo_point_id=echo_point_id, track_id=track_id,
                    points_qty=fill_qty, price_per_point=Decimal(str(match["price_per_point"])),
                )
                return True
        else:
            match = await self.db_fetchrow(
                """
                SELECT id, user_id, echo_point_id, points_qty, price_per_point,
                       points_qty - points_filled as qty_available
                FROM exchange_orders
                WHERE track_id = $1::uuid AND order_type = 'sell' AND status = 'open'
                  AND price_per_point <= $2 AND user_id != $3::uuid
                ORDER BY price_per_point ASC LIMIT 1
                """,
                track_id, float(price), user_id,
            )
            if match:
                fill_qty = min(qty, Decimal(str(match["qty_available"])))
                await self._execute_trade(
                    sell_order_id=str(match["id"]), buy_order_id=order_id,
                    buyer_id=user_id, seller_id=str(match["user_id"]),
                    echo_point_id=str(match["echo_point_id"]) if match["echo_point_id"] else None,
                    track_id=track_id, points_qty=fill_qty,
                    price_per_point=Decimal(str(match["price_per_point"])),
                )
                return True
        return False

    async def _execute_trade(
        self,
        sell_order_id: Optional[str],
        buy_order_id: Optional[str],
        buyer_id: str,
        seller_id: str,
        echo_point_id: Optional[str],
        track_id: str,
        points_qty: Decimal,
        price_per_point: Decimal,
    ) -> dict:
        """Execute a matched trade: fees, ownership transfer, records."""
        import uuid as _uuid

        gross = (points_qty * price_per_point).quantize(Decimal("0.01"), ROUND_HALF_UP)
        buyer_fee = (gross * FACILITATOR_FEE_EXCHANGE).quantize(Decimal("0.01"), ROUND_HALF_UP)
        seller_fee = (gross * FACILITATOR_FEE_EXCHANGE).quantize(Decimal("0.01"), ROUND_HALF_UP)
        net_to_seller = (gross - seller_fee).quantize(Decimal("0.01"), ROUND_HALF_UP)
        trade_id = str(_uuid.uuid4())

        await self.db_execute(
            """
            INSERT INTO exchange_trades (
                id, track_id, buy_order_id, sell_order_id,
                buyer_id, seller_id, points_qty, price_per_point,
                gross_amount, buyer_fee, seller_fee, net_to_seller
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $6::uuid, $7, $8, $9, $10, $11, $12)
            """,
            trade_id, track_id,
            buy_order_id, sell_order_id,
            buyer_id, seller_id,
            float(points_qty), float(price_per_point),
            float(gross), float(buyer_fee), float(seller_fee), float(net_to_seller),
        )

        # Transfer point ownership
        if echo_point_id:
            await self.db_execute(
                """
                UPDATE echo_points
                SET buyer_user_id = $2::uuid,
                    holding_period_ends = NOW() + INTERVAL '365 days',
                    status = 'active'
                WHERE id = $1::uuid
                """,
                echo_point_id, buyer_id,
            )

        # Record price history
        await self.db_execute(
            "INSERT INTO track_price_history (track_id, price_per_point, volume_traded, source) VALUES ($1::uuid, $2, $3, 'exchange')",
            track_id, float(price_per_point), float(points_qty),
        )

        # Update order fill status
        for oid in filter(None, [sell_order_id, buy_order_id]):
            await self.db_execute(
                """
                UPDATE exchange_orders
                SET points_filled = points_filled + $2,
                    status = CASE WHEN points_filled + $2 >= points_qty THEN 'filled' ELSE 'partial' END,
                    filled_at = CASE WHEN points_filled + $2 >= points_qty THEN NOW() ELSE filled_at END
                WHERE id = $3::uuid
                """,
                float(points_qty), float(points_qty), oid,
            )

        await self.broadcast("exchange.price_update", {
            "track_id": track_id,
            "price_per_point": float(price_per_point),
            "volume": float(points_qty),
            "trade_id": trade_id,
        })

        return {
            "trade_id": trade_id,
            "track_id": track_id,
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "points_qty": float(points_qty),
            "price_per_point": float(price_per_point),
            "gross_amount": float(gross),
            "buyer_fee": float(buyer_fee),
            "seller_fee": float(seller_fee),
            "net_to_seller": float(net_to_seller),
            "status": "executed",
        }

    async def _check_wash_trading(self, user_id: str, track_id: str) -> dict:
        """Check if user has both bought and sold this track in the last 24 hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        row = await self.db_fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE buyer_id = $1::uuid) as buys,
                COUNT(*) FILTER (WHERE seller_id = $1::uuid) as sells
            FROM exchange_trades
            WHERE track_id = $2::uuid AND traded_at >= $3
            """,
            user_id, track_id, cutoff,
        )
        if row and int(row["buys"]) > 0 and int(row["sells"]) > 0:
            return {"flagged": True, "buys": int(row["buys"]), "sells": int(row["sells"])}
        return {"flagged": False}

    # ----------------------------------------------------------------
    # Background loops
    # ----------------------------------------------------------------

    async def _payout_checker_loop(self):
        """Daily check: trigger quarterly payout on Jan/Apr/Jul/Oct 15."""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                payout_day = QUARTERLY_PAYOUT_MONTHS.get(now.month)
                if payout_day and now.day == payout_day:
                    logger.info(f"[Vault] Quarterly payout date triggered: {now.date()}")
                    fake_task = AgentTask(
                        task_id=f"vault_payout_{now.strftime('%Y%m%d')}",
                        task_type="process_quarterly_payout",
                        payload={"triggered_by": "scheduler"},
                    )
                    await self._task_process_quarterly_payout(fake_task)
                    await asyncio.sleep(86400)  # sleep past this day
                else:
                    await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Vault] Payout checker error: {e}")
                await asyncio.sleep(3600)

    async def _exchange_monitor_loop(self):
        """Every 10 minutes: expire stale orders, check for manipulation."""
        while self._running:
            try:
                await asyncio.sleep(600)
                # Expire stale orders
                await self.db_execute(
                    "UPDATE exchange_orders SET status = 'expired' WHERE status = 'open' AND expires_at < NOW()"
                )
                # Check manipulation on recently active tracks
                active_tracks = await self.db_fetch(
                    """
                    SELECT DISTINCT track_id FROM exchange_orders
                    WHERE status = 'open' AND created_at >= NOW() - INTERVAL '24 hours'
                    LIMIT 20
                    """
                )
                for row in active_tracks:
                    check_task = AgentTask(
                        task_id=f"manip_check_{row['track_id']}",
                        task_type="check_manipulation",
                        payload={"track_id": str(row["track_id"])},
                    )
                    await self._task_check_manipulation(check_task)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Vault] Exchange monitor error: {e}")
                await asyncio.sleep(60)

    async def _dynamic_pricing_loop(self):
        """Hourly: refresh AI confidence scores on all active drops."""
        while self._running:
            try:
                await asyncio.sleep(3600)
                active_drops = await self.db_fetch(
                    "SELECT id, artist_id FROM point_drops WHERE status = 'active' LIMIT 50"
                )
                for drop in active_drops:
                    score_task = AgentTask(
                        task_id=f"pricing_{drop['id']}",
                        task_type="ai_confidence_score",
                        payload={"artist_id": str(drop["artist_id"])},
                    )
                    result = await self._task_ai_confidence_score(score_task)
                    if result.success:
                        new_score = result.result.get("ai_confidence_score", 0)
                        await self.db_execute(
                            "UPDATE point_drops SET ai_confidence_score = $2 WHERE id = $1::uuid",
                            str(drop["id"]), new_score,
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Vault] Dynamic pricing loop error: {e}")
                await asyncio.sleep(60)
