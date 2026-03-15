"""
Vault Agent
Manages ECHO Points issuance, royalty distribution to point holders,
holding periods, and the secondary market.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class VaultAgent(BaseAgent):
    agent_id = "vault"
    agent_name = "Vault Agent"
    subscriptions = ["royalties.distributed", "points.purchased"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "distribute_to_holders": self._distribute_to_holders,
            "issue_points": self._issue_points,
            "holding_period_check": self._holding_period_check,
            "points_report": self._points_report,
            "calculate_yield": self._calculate_yield,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _distribute_to_holders(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        royalty_amount = task.payload.get("royalty_amount", 0.0)
        if not track_id or royalty_amount <= 0:
            return {"error": "track_id and positive royalty_amount required"}

        holders = await self.db_fetch(
            "SELECT id, buyer_user_id, points_purchased FROM echo_points WHERE track_id = $1::uuid AND status = 'active'",
            track_id,
        )
        if not holders:
            return {"track_id": track_id, "distributed_to": 0, "total": royalty_amount}

        total_points = sum(float(h["points_purchased"]) for h in holders)
        distributions = []
        for holder in holders:
            share = (float(holder["points_purchased"]) / total_points) * royalty_amount
            await self.db_execute(
                "UPDATE echo_points SET royalties_earned = royalties_earned + $2 WHERE id = $1",
                holder["id"], share,
            )
            distributions.append({"user_id": str(holder["buyer_user_id"]), "amount": share})

        await self.log_audit("distribute_royalties", "tracks", track_id, {"total": royalty_amount, "holders": len(holders)})
        return {"track_id": track_id, "distributed_to": len(holders), "total": royalty_amount, "distributions": distributions}

    async def _issue_points(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        release_id = task.payload.get("release_id")
        max_points = task.payload.get("max_points", 10000.0)
        price_per_point = task.payload.get("price_per_point", 1.0)
        logger.info(f"[Vault] Issuing {max_points} points for track {track_id}")
        return {
            "track_id": track_id,
            "release_id": release_id,
            "max_points": max_points,
            "price_per_point": price_per_point,
            "status": "points_available",
        }

    async def _holding_period_check(self, task: AgentTask) -> dict:
        from datetime import datetime, timezone
        expired = await self.db_fetch(
            "SELECT id, buyer_user_id, track_id FROM echo_points WHERE holding_period_ends < NOW() AND status = 'active' LIMIT 50"
        )
        for point in expired:
            await self.db_execute(
                "UPDATE echo_points SET status = 'tradeable' WHERE id = $1", point["id"]
            )
        return {"holding_periods_expired": len(expired), "now_tradeable": len(expired)}

    async def _points_report(self, task: AgentTask) -> dict:
        stats = await self.db_fetchrow(
            """
            SELECT
              COUNT(*) as total_purchases,
              COUNT(DISTINCT buyer_user_id) as unique_holders,
              COALESCE(SUM(price_paid), 0) as total_invested,
              COALESCE(SUM(royalties_earned), 0) as total_royalties_paid,
              COALESCE(SUM(points_purchased), 0) as total_points_issued
            FROM echo_points WHERE status IN ('active', 'tradeable')
            """
        )
        return dict(stats) if stats else {}

    async def _calculate_yield(self, task: AgentTask) -> dict:
        track_id = task.payload.get("track_id")
        royalties = await self.db_fetchrow(
            "SELECT COALESCE(SUM(net_amount), 0) as total FROM royalties WHERE track_id = $1::uuid",
            track_id,
        )
        invested = await self.db_fetchrow(
            "SELECT COALESCE(SUM(price_paid), 0) as total FROM echo_points WHERE track_id = $1::uuid AND status IN ('active','tradeable')",
            track_id,
        )
        total_royalties = float(royalties["total"]) if royalties else 0.0
        total_invested = float(invested["total"]) if invested else 0.0
        yield_pct = (total_royalties / total_invested * 100) if total_invested > 0 else 0.0
        return {"track_id": track_id, "total_royalties": total_royalties, "total_invested": total_invested, "yield_pct": round(yield_pct, 2)}

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
