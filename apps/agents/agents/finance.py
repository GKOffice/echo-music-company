"""
ECHO Finance Agent
Tracks every dollar in and out. Calculates royalties accurately. Keeps the label profitable.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

QUARTERLY_PAYOUT_MONTHS = {1: 15, 4: 15, 7: 15, 10: 15}  # month: day
MIN_PAYOUT_THRESHOLD = Decimal("50.00")


class FinanceAgent(BaseAgent):
    agent_id = "finance"
    agent_name = "Finance Agent"
    subscriptions = ["royalties.new", "expenses.new", "agent.finance", "release.revenue"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        asyncio.create_task(self._payout_scheduler())
        logger.info("[Finance] Online. Tracking every dollar.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "calculate_royalty_split": self._task_calculate_royalty_split,
            "process_quarterly_payout": self._task_process_quarterly_payout,
            "generate_artist_pl": self._task_generate_artist_pl,
            "track_expense": self._task_track_expense,
            "check_cash_position": self._task_check_cash_position,
            "reconcile_distributor_payment": self._task_reconcile_distributor_payment,
            "calculate_point_holder_payouts": self._task_calculate_point_holder_payouts,
            # Legacy handlers
            "process_royalties": self._task_process_royalties,
            "distribute_royalties": self._task_distribute_royalties,
            "recoupment_check": self._task_recoupment_check,
            "financial_report": self._task_financial_report,
            "record_advance": self._task_record_advance,
        }
        handler = handlers.get(task.task_type, self._task_default)
        return await handler(task)

    # ----------------------------------------------------------------
    # Core task handlers
    # ----------------------------------------------------------------

    async def _task_calculate_royalty_split(self, task: AgentTask) -> AgentResult:
        """
        Calculate royalty splits per contract rules.
        Pre-recoup: artist 40%, label 60%
        Post-recoup: artist 60%, label 40%
        Producer points always come off label share.
        Point holder earnings reduce artist share proportionally.
        """
        gross = Decimal(str(task.payload.get("gross_revenue", 0)))
        recouped = task.payload.get("recouped", False)
        producer_points = task.payload.get("producer_points", [])  # [{producer_id, points}]
        track_id = task.payload.get("track_id")

        # Producer points off the top (from label share only)
        total_producer_points = sum(Decimal(str(p["points"])) for p in producer_points)
        producer_pool = (gross * total_producer_points / Decimal("100")).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

        # Artist/label gross split
        if recouped:
            artist_pct = Decimal("0.60")
            label_pct = Decimal("0.40")
        else:
            artist_pct = Decimal("0.40")
            label_pct = Decimal("0.60")

        artist_amount = (gross * artist_pct).quantize(Decimal("0.01"), ROUND_HALF_UP)
        label_gross = (gross * label_pct).quantize(Decimal("0.01"), ROUND_HALF_UP)
        # Producer pool comes entirely from label share
        label_net = (label_gross - producer_pool).quantize(Decimal("0.01"), ROUND_HALF_UP)

        # Per-producer breakdown
        producer_splits = []
        for p in producer_points:
            amt = (gross * Decimal(str(p["points"])) / Decimal("100")).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            producer_splits.append(
                {"producer_id": p["producer_id"], "points": p["points"], "amount": float(amt)}
            )

        # ECHO Points holders pool — each point = 1% of master revenue
        point_holders_pool = Decimal("0")
        point_holder_splits = []
        if track_id:
            rows = await self.db_fetch(
                """
                SELECT buyer_user_id, points_purchased
                FROM echo_points
                WHERE track_id = $1::uuid AND status = 'active'
                """,
                track_id,
            )
            if rows:
                total_pts_sold = sum(Decimal(str(r["points_purchased"])) for r in rows)
                point_holders_pool = (gross * total_pts_sold / Decimal("100")).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
                # Point holder earnings reduce artist share
                artist_amount = (artist_amount - point_holders_pool).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
                # Individual point holder splits
                for r in rows:
                    pts = Decimal(str(r["points_purchased"]))
                    ph_amt = (gross * pts / Decimal("100")).quantize(
                        Decimal("0.01"), ROUND_HALF_UP
                    )
                    point_holder_splits.append(
                        {
                            "buyer_user_id": str(r["buyer_user_id"]),
                            "points": float(pts),
                            "amount": float(ph_amt),
                        }
                    )

        await self.log_audit(
            "calculate_royalty_split",
            "tracks",
            track_id,
            {"gross": float(gross), "recouped": recouped},
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "gross_revenue": float(gross),
                "artist_amount": float(artist_amount),
                "label_gross": float(label_gross),
                "label_net": float(label_net),
                "producer_pool": float(producer_pool),
                "producer_splits": producer_splits,
                "point_holders_pool": float(point_holders_pool),
                "point_holder_splits": point_holder_splits,
                "recouped": recouped,
                "split": "60/40" if recouped else "40/60",
                "breakdown": {
                    "artist_pct": float(artist_pct * 100),
                    "label_pct": float(label_pct * 100),
                    "producer_pts_total": float(total_producer_points),
                },
            },
        )

    async def _task_process_quarterly_payout(self, task: AgentTask) -> AgentResult:
        """
        Calculate and queue all payouts for a quarter.
        Only pays out if balance >= MIN_PAYOUT_THRESHOLD ($50).
        """
        quarter = task.payload.get("quarter")  # e.g. "2026-Q1"
        year = task.payload.get("year", datetime.now(timezone.utc).year)
        quarter_num = task.payload.get("quarter_num", self._current_quarter())

        # Fetch all undistributed royalties
        royalties = await self.db_fetch(
            """
            SELECT r.id, r.artist_id, r.track_id, r.net_amount, r.gross_amount, r.source
            FROM royalties r
            WHERE r.distributed = FALSE
            ORDER BY r.artist_id, r.created_at
            """
        )

        # Aggregate by artist
        artist_totals: dict[str, Decimal] = {}
        royalty_ids: dict[str, list] = {}
        for row in royalties:
            aid = str(row["artist_id"])
            amt = Decimal(str(row["net_amount"]))
            artist_totals[aid] = artist_totals.get(aid, Decimal("0")) + amt
            royalty_ids.setdefault(aid, []).append(str(row["id"]))

        payouts = []
        skipped = []
        total_queued = Decimal("0")

        for artist_id, amount in artist_totals.items():
            if amount < MIN_PAYOUT_THRESHOLD:
                skipped.append({"artist_id": artist_id, "balance": float(amount), "reason": "below_threshold"})
                continue

            # Mark royalties distributed
            for rid in royalty_ids[artist_id]:
                await self.db_execute(
                    "UPDATE royalties SET distributed = TRUE, distributed_at = NOW() WHERE id = $1::uuid",
                    rid,
                )

            # Update artist recoupment balance
            await self.db_execute(
                """
                UPDATE artists
                SET recoupment_balance = GREATEST(0, recoupment_balance - $2),
                    updated_at = NOW()
                WHERE id = $1::uuid
                """,
                artist_id,
                float(amount),
            )

            payouts.append({"artist_id": artist_id, "amount": float(amount), "royalty_count": len(royalty_ids[artist_id])})
            total_queued += amount

        # Notify hub/CEO
        await self.broadcast(
            "finance.payout_queued",
            {
                "quarter": quarter or f"{year}-Q{quarter_num}",
                "payouts_count": len(payouts),
                "total_usd": float(total_queued),
                "skipped_count": len(skipped),
            },
        )

        await self.log_audit(
            "process_quarterly_payout",
            "royalties",
            details={
                "quarter": quarter or f"{year}-Q{quarter_num}",
                "total_usd": float(total_queued),
                "payouts": len(payouts),
            },
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "quarter": quarter or f"{year}-Q{quarter_num}",
                "payouts": payouts,
                "skipped": skipped,
                "total_queued_usd": float(total_queued),
                "payout_date": self._next_payout_date().isoformat(),
            },
        )

    async def _task_generate_artist_pl(self, task: AgentTask) -> AgentResult:
        """
        Full P&L for one artist: revenue - all costs = net profit.
        Recoupable = advance + recording costs ONLY.
        """
        artist_id = task.payload.get("artist_id") or task.artist_id
        if not artist_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="artist_id required",
            )

        artist = await self.db_fetchrow(
            "SELECT name, advance_amount, recoupment_balance FROM artists WHERE id = $1::uuid",
            artist_id,
        )
        if not artist:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="Artist not found",
            )

        # Total revenue
        revenue_row = await self.db_fetchrow(
            """
            SELECT COALESCE(SUM(gross_amount), 0) as total_gross,
                   COALESCE(SUM(net_amount), 0) as total_net
            FROM royalties WHERE artist_id = $1::uuid
            """,
            artist_id,
        )

        # Expenses by category
        expense_rows = await self.db_fetch(
            """
            SELECT category,
                   COALESCE(SUM(amount), 0) as total,
                   COALESCE(SUM(CASE WHEN recoupable THEN amount ELSE 0 END), 0) as recoupable_total
            FROM expenses
            WHERE artist_id = $1::uuid
            GROUP BY category
            """,
            artist_id,
        )

        expenses_by_cat: dict = {}
        total_expenses = Decimal("0")
        total_recoupable = Decimal("0")
        for row in expense_rows:
            cat_total = Decimal(str(row["total"]))
            cat_recoupable = Decimal(str(row["recoupable_total"]))
            expenses_by_cat[row["category"]] = {
                "total": float(cat_total),
                "recoupable": float(cat_recoupable),
            }
            total_expenses += cat_total
            total_recoupable += cat_recoupable

        total_gross = Decimal(str(revenue_row["total_gross"])) if revenue_row else Decimal("0")
        total_net = Decimal(str(revenue_row["total_net"])) if revenue_row else Decimal("0")
        advance = Decimal(str(artist["advance_amount"]))
        recoupment_balance = Decimal(str(artist["recoupment_balance"]))

        net_profit = total_net - total_expenses

        # Recoupment status
        total_recoupable_costs = advance + total_recoupable
        recouped_amount = total_recoupable_costs - recoupment_balance
        fully_recouped = recoupment_balance <= Decimal("0")

        # Points revenue
        points_row = await self.db_fetchrow(
            """
            SELECT COALESCE(SUM(price_paid), 0) as total_points_revenue
            FROM echo_points ep
            JOIN tracks t ON ep.track_id = t.id
            WHERE t.artist_id = $1::uuid AND ep.status = 'active'
            """,
            artist_id,
        )
        points_revenue = Decimal(str(points_row["total_points_revenue"])) if points_row else Decimal("0")

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "artist_id": artist_id,
                "artist_name": artist["name"],
                "revenue": {
                    "gross": float(total_gross),
                    "net": float(total_net),
                    "points_store": float(points_revenue),
                    "total": float(total_net + points_revenue),
                },
                "expenses": {
                    "by_category": expenses_by_cat,
                    "total": float(total_expenses),
                    "recoupable_total": float(total_recoupable),
                },
                "recoupment": {
                    "advance": float(advance),
                    "total_recoupable_costs": float(total_recoupable_costs),
                    "recouped_to_date": float(recouped_amount),
                    "remaining_balance": float(recoupment_balance),
                    "fully_recouped": fully_recouped,
                    "split_status": "60/40 (post-recoup)" if fully_recouped else "40/60 (pre-recoup)",
                },
                "net_profit": float(net_profit),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _task_track_expense(self, task: AgentTask) -> AgentResult:
        """Log an expense to the DB."""
        artist_id = task.payload.get("artist_id") or task.artist_id
        release_id = task.payload.get("release_id") or task.release_id
        category = task.payload.get("category", "other")
        amount = Decimal(str(task.payload.get("amount", 0)))
        description = task.payload.get("description", "")
        vendor = task.payload.get("vendor", "")
        # Marketing, distribution, PR, video = NOT recoupable. Recording + advance = recoupable.
        recoupable_categories = {"recording", "advance"}
        recoupable = task.payload.get("recoupable", category in recoupable_categories)

        expense_id = None
        try:
            row = await self.db_fetchrow(
                """
                INSERT INTO expenses (artist_id, release_id, category, amount, recoupable,
                    description, vendor, created_by)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, 'finance')
                RETURNING id
                """,
                artist_id,
                release_id,
                category,
                float(amount),
                recoupable,
                description,
                vendor,
            )
            expense_id = str(row["id"]) if row else None
        except Exception as e:
            logger.error(f"[Finance] track_expense DB error: {e}")
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id, error=str(e)
            )

        # If recoupable, add to artist's recoupment balance
        if recoupable and artist_id:
            await self.db_execute(
                "UPDATE artists SET recoupment_balance = recoupment_balance + $2, updated_at = NOW() WHERE id = $1::uuid",
                artist_id,
                float(amount),
            )

        await self.log_audit(
            "track_expense",
            "expenses",
            expense_id,
            {"amount": float(amount), "category": category, "recoupable": recoupable},
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "expense_id": expense_id,
                "amount": float(amount),
                "category": category,
                "recoupable": recoupable,
                "artist_id": artist_id,
            },
        )

    async def _task_check_cash_position(self, task: AgentTask) -> AgentResult:
        """
        Return cash status + alerts.
        Warn if cash reserve < 2 months operating expenses.
        """
        # Total undistributed royalties = cash on hand
        royalties_row = await self.db_fetchrow(
            "SELECT COALESCE(SUM(net_amount), 0) as available FROM royalties WHERE distributed = FALSE"
        )
        # Points revenue
        points_row = await self.db_fetchrow(
            "SELECT COALESCE(SUM(price_paid), 0) as total FROM echo_points WHERE status = 'active'"
        )
        # Average monthly expenses (last 3 months)
        monthly_expense_row = await self.db_fetchrow(
            """
            SELECT COALESCE(SUM(amount), 0) / NULLIF(
                EXTRACT(MONTH FROM AGE(NOW(), MIN(paid_at)))::int + 1, 0
            ) as avg_monthly
            FROM expenses
            WHERE paid_at >= NOW() - INTERVAL '3 months'
            """
        )

        cash_available = Decimal(str(royalties_row["available"])) if royalties_row else Decimal("0")
        points_revenue = Decimal(str(points_row["total"])) if points_row else Decimal("0")
        avg_monthly_opex = Decimal(str(monthly_expense_row["avg_monthly"] or 0)) if monthly_expense_row else Decimal("0")
        two_month_reserve = avg_monthly_opex * Decimal("2")

        alerts = []
        if avg_monthly_opex > Decimal("0") and cash_available < two_month_reserve:
            alerts.append({
                "level": "warning",
                "message": f"Cash reserve ${float(cash_available):.2f} is below 2-month operating expense threshold ${float(two_month_reserve):.2f}",
                "threshold": float(two_month_reserve),
                "current": float(cash_available),
            })
        if cash_available < Decimal("0"):
            alerts.append({
                "level": "critical",
                "message": "Negative cash position",
                "current": float(cash_available),
            })

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "cash_available": float(cash_available),
                "points_revenue_total": float(points_revenue),
                "avg_monthly_opex": float(avg_monthly_opex),
                "two_month_reserve_target": float(two_month_reserve),
                "months_of_runway": float(cash_available / avg_monthly_opex) if avg_monthly_opex > 0 else None,
                "alerts": alerts,
                "status": "critical" if any(a["level"] == "critical" for a in alerts)
                    else "warning" if alerts else "healthy",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _task_reconcile_distributor_payment(self, task: AgentTask) -> AgentResult:
        """
        Match an incoming distributor payment to expected royalties.
        Flags discrepancies > 5% as requiring review.
        """
        distributor = task.payload.get("distributor")
        payment_amount = Decimal(str(task.payload.get("payment_amount", 0)))
        period_start = task.payload.get("period_start")
        period_end = task.payload.get("period_end")
        platform = task.payload.get("platform", distributor)

        # Look up expected royalties for this distributor/period
        params = [platform]
        query = "SELECT COALESCE(SUM(gross_amount), 0) as expected FROM royalties WHERE platform = $1"
        if period_start:
            query += " AND period_start >= $2"
            params.append(period_start)
        if period_end:
            query += f" AND period_end <= ${len(params) + 1}"
            params.append(period_end)

        expected_row = await self.db_fetchrow(query, *params)
        expected = Decimal(str(expected_row["expected"])) if expected_row else Decimal("0")

        discrepancy = payment_amount - expected
        discrepancy_pct = abs(discrepancy / expected * 100) if expected > 0 else Decimal("0")
        needs_review = discrepancy_pct > Decimal("5")

        if needs_review:
            await self.broadcast(
                "finance.reconciliation_alert",
                {
                    "distributor": distributor,
                    "expected": float(expected),
                    "received": float(payment_amount),
                    "discrepancy": float(discrepancy),
                    "discrepancy_pct": float(discrepancy_pct),
                    "period": f"{period_start} to {period_end}",
                },
            )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "distributor": distributor,
                "payment_received": float(payment_amount),
                "expected": float(expected),
                "discrepancy": float(discrepancy),
                "discrepancy_pct": float(discrepancy_pct),
                "needs_review": needs_review,
                "status": "flagged_for_review" if needs_review else "reconciled",
                "period": {"start": period_start, "end": period_end},
            },
        )

    async def _task_calculate_point_holder_payouts(self, task: AgentTask) -> AgentResult:
        """
        Distribute royalties to ECHO Points holders proportionally.
        Each point = 1% of master revenue for that track.
        """
        track_id = task.payload.get("track_id")
        gross_revenue = Decimal(str(task.payload.get("gross_revenue", 0)))

        if not track_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="track_id required",
            )

        holders = await self.db_fetch(
            """
            SELECT id, buyer_user_id, points_purchased
            FROM echo_points
            WHERE track_id = $1::uuid AND status = 'active'
            ORDER BY points_purchased DESC
            """,
            track_id,
        )

        if not holders:
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id=self.agent_id,
                result={"track_id": track_id, "payouts": [], "total_distributed": 0.0},
            )

        payouts = []
        total_distributed = Decimal("0")
        for h in holders:
            pts = Decimal(str(h["points_purchased"]))
            payout = (gross_revenue * pts / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
            if payout >= MIN_PAYOUT_THRESHOLD:
                # Update royalties_earned on the echo_points record
                await self.db_execute(
                    "UPDATE echo_points SET royalties_earned = royalties_earned + $2 WHERE id = $1::uuid",
                    str(h["id"]),
                    float(payout),
                )
                payouts.append(
                    {
                        "echo_points_id": str(h["id"]),
                        "buyer_user_id": str(h["buyer_user_id"]),
                        "points": float(pts),
                        "payout": float(payout),
                    }
                )
                total_distributed += payout

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "track_id": track_id,
                "gross_revenue": float(gross_revenue),
                "payouts": payouts,
                "total_distributed": float(total_distributed),
                "holders_paid": len(payouts),
                "holders_below_threshold": len(holders) - len(payouts),
            },
        )

    # ----------------------------------------------------------------
    # Legacy handlers (kept for backward compatibility)
    # ----------------------------------------------------------------

    async def _task_process_royalties(self, task: AgentTask) -> AgentResult:
        royalty_data = task.payload.get("royalties", [])
        processed = 0
        for entry in royalty_data:
            await self.db_execute(
                """
                INSERT INTO royalties (artist_id, track_id, source, platform, gross_amount, net_amount,
                    period_start, period_end, reported_by_agent)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, 'finance')
                """,
                entry.get("artist_id"), entry.get("track_id"), entry.get("source"),
                entry.get("platform"), entry.get("gross"), entry.get("net"),
                entry.get("period_start"), entry.get("period_end"),
            )
            processed += 1
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"processed": processed},
        )

    async def _task_distribute_royalties(self, task: AgentTask) -> AgentResult:
        undistributed = await self.db_fetch(
            "SELECT id, artist_id, net_amount FROM royalties WHERE distributed = FALSE LIMIT 100"
        )
        total = sum(float(r["net_amount"]) for r in undistributed)
        for r in undistributed:
            await self.db_execute(
                "UPDATE royalties SET distributed = TRUE, distributed_at = NOW() WHERE id = $1::uuid",
                r["id"],
            )
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"distributed_count": len(undistributed), "total_usd": total},
        )

    async def _task_recoupment_check(self, task: AgentTask) -> AgentResult:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow(
            "SELECT advance_amount, recoupment_balance FROM artists WHERE id = $1::uuid", artist_id
        )
        if not artist:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="Artist not found",
            )
        advance = float(artist["advance_amount"])
        balance = float(artist["recoupment_balance"])
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "artist_id": artist_id,
                "advance": advance,
                "recoupment_balance": balance,
                "fully_recouped": balance <= 0,
            },
        )

    async def _task_financial_report(self, task: AgentTask) -> AgentResult:
        report = await self.db_fetchrow(
            """
            SELECT COALESCE(SUM(gross_amount), 0) as total_gross,
                   COALESCE(SUM(net_amount), 0) as total_net,
                   COUNT(*) as royalty_records,
                   COUNT(DISTINCT artist_id) as artists_with_royalties
            FROM royalties
            """
        )
        points_revenue = await self.db_fetchrow(
            "SELECT COALESCE(SUM(price_paid), 0) as total FROM echo_points WHERE status = 'active'"
        )
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={
                "royalties": {k: float(v) if v is not None else 0 for k, v in dict(report).items()} if report else {},
                "points_revenue": float(points_revenue["total"]) if points_revenue else 0.0,
            },
        )

    async def _task_record_advance(self, task: AgentTask) -> AgentResult:
        artist_id = task.payload.get("artist_id")
        amount = task.payload.get("amount", 0)
        await self.db_execute(
            "UPDATE artists SET advance_amount = advance_amount + $2, recoupment_balance = recoupment_balance + $2, updated_at = NOW() WHERE id = $1::uuid",
            artist_id, amount,
        )
        await self.log_audit("record_advance", "artists", artist_id, {"amount": amount})
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"artist_id": artist_id, "advance_recorded": amount},
        )

    async def _task_default(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            success=False, task_id=task.task_id, agent_id=self.agent_id,
            error=f"Unknown task type: {task.task_type}",
        )

    # ----------------------------------------------------------------
    # Payout scheduler
    # ----------------------------------------------------------------

    async def _payout_scheduler(self):
        """
        Runs daily. On quarterly payout dates (Jan/Apr/Jul/Oct 15),
        automatically triggers process_quarterly_payout.
        """
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                payout_day = QUARTERLY_PAYOUT_MONTHS.get(now.month)
                if payout_day and now.day == payout_day:
                    logger.info(f"[Finance] Quarterly payout date: {now.date()}. Triggering payouts.")
                    fake_task = AgentTask(
                        task_id=f"scheduler_{now.strftime('%Y%m%d')}",
                        task_type="process_quarterly_payout",
                        payload={
                            "year": now.year,
                            "quarter_num": self._current_quarter(),
                            "triggered_by": "scheduler",
                        },
                    )
                    await self._task_process_quarterly_payout(fake_task)
                    # Sleep until tomorrow to avoid double-firing
                    await asyncio.sleep(86400)
                else:
                    # Check again in 1 hour
                    await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Finance] Payout scheduler error: {e}")
                await asyncio.sleep(3600)

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _current_quarter(self) -> int:
        month = datetime.now(timezone.utc).month
        return (month - 1) // 3 + 1

    def _next_payout_date(self) -> date:
        now = datetime.now(timezone.utc).date()
        for month in sorted(QUARTERLY_PAYOUT_MONTHS.keys()):
            payout = date(now.year, month, QUARTERLY_PAYOUT_MONTHS[month])
            if payout >= now:
                return payout
        # Wrap to next year
        first_month = sorted(QUARTERLY_PAYOUT_MONTHS.keys())[0]
        return date(now.year + 1, first_month, QUARTERLY_PAYOUT_MONTHS[first_month])

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        if topic == "royalties.new":
            logger.info(f"[Finance] New royalty entry: {message.get('payload', {})}")
        elif topic == "release.revenue":
            payload = message.get("payload", {})
            track_id = payload.get("track_id")
            revenue = payload.get("revenue", 0)
            if track_id and revenue:
                logger.info(f"[Finance] Revenue event for track {track_id}: ${revenue}")
