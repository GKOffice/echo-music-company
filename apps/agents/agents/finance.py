"""
Finance Agent
Tracks all revenue, processes royalty distributions, manages
advances and recoupment, and generates financial reports.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class FinanceAgent(BaseAgent):
    agent_id = "finance"
    agent_name = "Finance Agent"
    subscriptions = ["royalties.received", "contract.signed", "points.purchased"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "process_royalties": self._process_royalties,
            "distribute_royalties": self._distribute_royalties,
            "recoupment_check": self._recoupment_check,
            "financial_report": self._financial_report,
            "record_advance": self._record_advance,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _process_royalties(self, task: AgentTask) -> dict:
        royalty_data = task.payload.get("royalties", [])
        processed = 0
        import json
        for entry in royalty_data:
            await self.db_execute(
                """
                INSERT INTO royalties (artist_id, track_id, source, platform, gross_amount, net_amount, period_start, period_end, reported_by_agent)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, 'finance')
                """,
                entry.get("artist_id"), entry.get("track_id"), entry.get("source"),
                entry.get("platform"), entry.get("gross"), entry.get("net"),
                entry.get("period_start"), entry.get("period_end"),
            )
            processed += 1
        return {"processed": processed}

    async def _distribute_royalties(self, task: AgentTask) -> dict:
        undistributed = await self.db_fetch(
            "SELECT id, artist_id, net_amount FROM royalties WHERE distributed = FALSE LIMIT 100"
        )
        total = sum(float(r["net_amount"]) for r in undistributed)
        for r in undistributed:
            await self.db_execute(
                "UPDATE royalties SET distributed = TRUE, distributed_at = NOW() WHERE id = $1",
                r["id"],
            )
        return {"distributed_count": len(undistributed), "total_usd": total}

    async def _recoupment_check(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        artist = await self.db_fetchrow(
            "SELECT advance_amount, recoupment_balance FROM artists WHERE id = $1::uuid", artist_id
        )
        if not artist:
            return {"error": "Artist not found"}
        recouped = float(artist["advance_amount"]) - float(artist.get("recoupment_balance", 0))
        return {
            "artist_id": artist_id,
            "advance": float(artist["advance_amount"]),
            "recoupment_balance": float(artist.get("recoupment_balance", 0)),
            "recouped": recouped,
            "fully_recouped": recouped <= 0,
        }

    async def _financial_report(self, task: AgentTask) -> dict:
        report = await self.db_fetchrow(
            """
            SELECT
              COALESCE(SUM(gross_amount), 0) as total_gross,
              COALESCE(SUM(net_amount), 0) as total_net,
              COUNT(*) as royalty_records,
              COUNT(DISTINCT artist_id) as artists_with_royalties
            FROM royalties
            """
        )
        points_revenue = await self.db_fetchrow(
            "SELECT COALESCE(SUM(price_paid), 0) as total FROM echo_points WHERE status = 'active'"
        )
        return {
            "royalties": dict(report) if report else {},
            "points_revenue": float(points_revenue["total"]) if points_revenue else 0.0,
        }

    async def _record_advance(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id")
        amount = task.payload.get("amount", 0)
        await self.db_execute(
            "UPDATE artists SET advance_amount = advance_amount + $2, recoupment_balance = recoupment_balance + $2, updated_at = NOW() WHERE id = $1::uuid",
            artist_id,
            amount,
        )
        await self.log_audit("record_advance", "artists", artist_id, {"amount": amount})
        return {"artist_id": artist_id, "advance_recorded": amount}
