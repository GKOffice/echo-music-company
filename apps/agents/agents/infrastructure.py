"""
ECHO Infrastructure Agent
Monitors system health, manages deployments, and handles infrastructure ops.
"""
from base_agent import BaseAgent, AgentTask, AgentResult


class InfrastructureAgent(BaseAgent):
    agent_id = "infrastructure"
    agent_name = "Infrastructure Agent"
    subscriptions = ["system.health", "agent.infrastructure"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handler = getattr(self, f"_task_{task.task_type}", self._task_default)
        return await handler(task)

    async def _task_default(self, task: AgentTask) -> AgentResult:
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result={"status": "received", "task_type": task.task_type})

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
