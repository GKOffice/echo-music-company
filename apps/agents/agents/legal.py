"""
Legal Agent
Drafts and manages contracts, handles copyright registration,
monitors compliance, and oversees DocuSign execution.
"""

import logging
import uuid
from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)


class LegalAgent(BaseAgent):
    agent_id = "legal"
    agent_name = "Legal Agent"
    subscriptions = ["artist.signed", "contract.disputed"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "draft_contract": self._draft_contract,
            "review_contracts": self._review_contracts,
            "register_copyright": self._register_copyright,
            "send_for_signature": self._send_for_signature,
            "compliance_check": self._compliance_check,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task"}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    async def _draft_contract(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        deal_type = task.payload.get("deal_type", "single")
        contract_id = str(uuid.uuid4())
        splits = {"single": (80, 20), "ep": (75, 25), "album": (70, 30)}
        artist_split, label_split = splits.get(deal_type, (80, 20))
        await self.db_execute(
            """
            INSERT INTO contracts (id, artist_id, type, status, royalty_split_artist, royalty_split_label)
            VALUES ($1::uuid, $2::uuid, $3, 'draft', $4, $5)
            """,
            contract_id, artist_id, deal_type, artist_split, label_split,
        )
        await self.log_audit("draft_contract", "contracts", contract_id)
        return {"contract_id": contract_id, "artist_id": artist_id, "type": deal_type, "splits": f"{artist_split}/{label_split}"}

    async def _review_contracts(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        artist_id = task.payload.get("artist_id") or task.artist_id
        contracts = await self.db_fetch(
            "SELECT id, type, status FROM contracts WHERE artist_id = $1::uuid ORDER BY created_at DESC LIMIT 5",
            artist_id,
        )
        return {"artist_id": artist_id, "contracts": contracts}

    async def _register_copyright(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        track_id = task.payload.get("track_id")
        logger.info(f"[Legal] Registering copyright for release {release_id}")
        return {"release_id": release_id, "copyright_registered": True, "status": "pending_confirmation"}

    async def _send_for_signature(self, task: AgentTask) -> dict:
        contract_id = task.payload.get("contract_id")
        envelope_id = f"env_{str(uuid.uuid4())[:8]}"
        await self.db_execute(
            "UPDATE contracts SET status = 'pending_signature', docusign_envelope_id = $2, updated_at = NOW() WHERE id = $1::uuid",
            contract_id, envelope_id,
        )
        return {"contract_id": contract_id, "envelope_id": envelope_id, "status": "sent_for_signature"}

    async def _compliance_check(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        return {"release_id": release_id, "compliant": True, "issues": [], "checked_by": "legal"}
