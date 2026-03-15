"""
CEO Agent
Orchestrates all other agents, sets company strategy, monitors KPIs,
and makes high-level decisions across the ECHO operation.
"""

import logging
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class CEOAgent(BaseAgent):
    agent_id = "ceo"
    agent_name = "CEO Agent"
    subscriptions = [
        "agent.status",
        "release.completed",
        "artist.signed",
        "revenue.report",
        "alert.critical",
    ]

    async def on_start(self):
        logger.info("[CEO] Online — monitoring all 21 agents")
        await self.broadcast_status()

    async def broadcast_status(self):
        agents = await self.db_fetch(
            "SELECT agent_id, status FROM agent_tasks GROUP BY agent_id, status"
        )
        logger.info(f"[CEO] Current agent task summary: {len(agents)} records")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "orchestrate_release": self._orchestrate_release,
            "company_report": self._generate_report,
            "set_priority": self._set_priority,
            "delegate": self._delegate_task,
        }

        handler = handlers.get(task.task_type)
        if handler:
            result = await handler(task)
        else:
            logger.warning(f"[CEO] Unknown task type: {task.task_type}")
            result = {"status": "unknown_task", "task_type": task.task_type}

        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _orchestrate_release(self, task: AgentTask) -> dict:
        """Kick off a full release pipeline for a release_id."""
        release_id = task.payload.get("release_id") or task.release_id
        if not release_id:
            return {"error": "release_id required"}

        release = await self.db_fetchrow(
            "SELECT * FROM releases WHERE id = $1::uuid", release_id
        )
        if not release:
            return {"error": f"Release {release_id} not found"}

        pipeline = [
            ("qc", "quality_check", {"release_id": release_id}),
            ("legal", "review_contracts", {"release_id": release_id}),
            ("creative", "artwork_review", {"release_id": release_id}),
            ("distribution", "prepare_distribution", {"release_id": release_id}),
            ("marketing", "plan_campaign", {"release_id": release_id}),
        ]

        for agent_id, task_type, payload in pipeline:
            await self.send_message(agent_id, task_type, payload)
            logger.info(f"[CEO] Delegated {task_type} to {agent_id} for release {release_id}")

        await self.db_execute(
            "UPDATE releases SET status = 'in_pipeline', updated_at = NOW() WHERE id = $1::uuid",
            release_id,
        )

        await self.log_audit("orchestrate_release", "releases", release_id)

        return {
            "release_id": release_id,
            "pipeline_stages": len(pipeline),
            "status": "pipeline_initiated",
        }

    async def _generate_report(self, task: AgentTask) -> dict:
        """Compile company-wide KPI report."""
        stats = await self.db_fetchrow(
            """
            SELECT
              (SELECT COUNT(*) FROM artists WHERE status = 'signed') as signed_artists,
              (SELECT COUNT(*) FROM releases WHERE status != 'draft') as active_releases,
              (SELECT COALESCE(SUM(net_amount), 0) FROM royalties) as total_royalties,
              (SELECT COUNT(*) FROM agent_tasks WHERE status = 'completed') as tasks_completed,
              (SELECT COUNT(*) FROM agent_tasks WHERE status = 'failed') as tasks_failed
            """
        )
        return dict(stats) if stats else {}

    async def _set_priority(self, task: AgentTask) -> dict:
        """Update priority for a release or artist."""
        release_id = task.payload.get("release_id")
        priority = task.payload.get("priority", "standard")
        if release_id:
            await self.db_execute(
                "UPDATE releases SET priority = $2, updated_at = NOW() WHERE id = $1::uuid",
                release_id,
                priority,
            )
        return {"priority_set": priority, "release_id": release_id}

    async def _delegate_task(self, task: AgentTask) -> dict:
        """Delegate a task to a specific agent."""
        to_agent = task.payload.get("to_agent")
        delegated_task_type = task.payload.get("task_type")
        payload = task.payload.get("payload", {})

        if not to_agent or not delegated_task_type:
            return {"error": "to_agent and task_type required"}

        await self.send_message(to_agent, delegated_task_type, payload)
        return {"delegated_to": to_agent, "task_type": delegated_task_type}

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        payload = message.get("payload", {})

        if topic == "alert.critical":
            logger.critical(f"[CEO] CRITICAL ALERT: {payload}")
        elif topic == "release.completed":
            release_id = payload.get("release_id")
            logger.info(f"[CEO] Release completed: {release_id}")
            await self.send_message("analytics", "track_release", {"release_id": release_id})
            await self.send_message("pr", "announce_release", {"release_id": release_id})
        elif topic == "artist.signed":
            artist_id = payload.get("artist_id")
            logger.info(f"[CEO] Artist signed: {artist_id}")
