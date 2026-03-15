"""
ECHO PR Agent
Handles press releases, media outreach, and public relations.
"""
from base_agent import BaseAgent, AgentTask, AgentResult


class PRAgent(BaseAgent):
    agent_id = "pr"
    agent_name = "PR Agent"
    subscriptions = ["releases.new", "agent.pr"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handler = getattr(self, f"_task_{task.task_type}", self._task_default)
        return await handler(task)

    async def _task_default(self, task: AgentTask) -> AgentResult:
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result={"status": "received", "task_type": task.task_type})

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
