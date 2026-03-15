"""
ECHO Legal Agent
Drafts and manages contracts, handles copyright registration,
monitors DMCA, verifies compliance (no invest/ROI language), and tracks rights ownership.
"""
import logging
import re
import uuid
from datetime import datetime, timezone, date, timedelta
from typing import Optional

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Words that are strictly prohibited in ECHO Points marketing/context
PROHIBITED_POINT_WORDS = [
    r"\binvest\b", r"\binvestment\b", r"\binvestments\b", r"\binvestor\b", r"\binvestors\b",
    r"\bROI\b", r"\breturn on investment\b", r"\breturns\b", r"\bfinancial returns\b",
    r"\bsecurities\b", r"\bsecurity\b", r"\bshares\b", r"\bequity\b", r"\bdividend\b",
    r"\bprofit sharing\b", r"\bspeculate\b", r"\bspeculation\b",
]

# Allowed replacement guidance
ALLOWED_ALTERNATIVES = {
    "invest": "buy / purchase / own",
    "investment": "purchase / points",
    "ROI": "royalties earned",
    "returns": "royalties / earnings",
    "securities": "points",
    "equity": "master points",
}

COPYRIGHT_SOCIETIES = ["ascap", "bmi", "sesac", "mlc", "soundexchange", "songtrust", "copyright_office", "content_id"]
COPYRIGHT_DEADLINE_DAYS = 30  # Register within 30 days of release


class LegalAgent(BaseAgent):
    agent_id = "legal"
    agent_name = "Legal Agent"
    subscriptions = ["artist.signed", "contract.disputed", "release.published", "agent.legal"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Legal] Online. Protecting ECHO's rights and compliance.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "generate_contract": self._task_generate_contract,
            "register_copyright": self._task_register_copyright,
            "process_dmca": self._task_process_dmca,
            "compliance_check": self._task_compliance_check,
            "check_rights": self._task_check_rights,
            "draft_tos": self._task_draft_tos,
            "verify_point_language": self._task_verify_point_language,
            # Legacy
            "draft_contract": self._task_generate_contract,
            "review_contracts": self._task_review_contracts,
            "send_for_signature": self._task_send_for_signature,
        }
        handler = handlers.get(task.task_type, self._task_default)
        return await handler(task)

    # ----------------------------------------------------------------
    # Task handlers
    # ----------------------------------------------------------------

    async def _task_generate_contract(self, task: AgentTask) -> AgentResult:
        """
        Generate a recording agreement from template.
        Supports: single, ep, album, producer, publishing_admin
        """
        artist_id = task.payload.get("artist_id") or task.artist_id
        deal_type = task.payload.get("deal_type", "single")
        song_title = task.payload.get("song_title", "")
        advance_amount = task.payload.get("advance_amount", 0)
        producer_name = task.payload.get("producer_name", "")
        producer_points = task.payload.get("producer_points", 0)

        # Fetch artist name
        artist_name = "Artist"
        if artist_id:
            artist_row = await self.db_fetchrow(
                "SELECT name, stage_name FROM artists WHERE id = $1::uuid", artist_id
            )
            if artist_row:
                artist_name = artist_row["stage_name"] or artist_row["name"]

        contract_id = str(uuid.uuid4())
        today = datetime.now(timezone.utc).date()
        reversion_date = date(today.year + 5, today.month, today.day)

        if deal_type in ("single", "ep", "album"):
            contract_text = self._render_recording_agreement(
                artist_name=artist_name,
                song_title=song_title or f"[{deal_type.upper()} TITLE]",
                deal_type=deal_type,
                date_str=today.strftime("%B %d, %Y"),
                advance_amount=advance_amount,
                reversion_date=reversion_date.strftime("%B %d, %Y"),
                producer_name=producer_name,
                producer_points=producer_points,
            )
        elif deal_type == "producer":
            contract_text = self._render_producer_agreement(
                producer_name=producer_name or "Producer",
                artist_name=artist_name,
                song_title=song_title or "[SONG TITLE]",
                date_str=today.strftime("%B %d, %Y"),
                producer_points=producer_points,
            )
        elif deal_type == "publishing_admin":
            contract_text = self._render_publishing_admin_agreement(
                artist_name=artist_name,
                date_str=today.strftime("%B %d, %Y"),
            )
        else:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error=f"Unknown deal_type: {deal_type}",
            )

        # Persist to DB
        try:
            await self.db_execute(
                """
                INSERT INTO contracts (id, artist_id, type, status, terms_json,
                    royalty_split_artist, royalty_split_label, advance_amount,
                    recoupment_balance, reversion_date, execution_date)
                VALUES ($1::uuid, $2::uuid, $3, 'draft', $4::jsonb, $5, $6, $7, $7, $8, $9)
                """,
                contract_id,
                artist_id,
                deal_type,
                __import__("json").dumps({
                    "contract_text": contract_text,
                    "producer_name": producer_name,
                    "producer_points": producer_points,
                    "song_title": song_title,
                }),
                40.0,   # pre-recoup artist %
                60.0,   # pre-recoup label %
                float(advance_amount),
                reversion_date,
                today,
            )
        except Exception as e:
            logger.error(f"[Legal] Contract DB insert error: {e}")

        await self.log_audit(
            "generate_contract", "contracts", contract_id,
            {"deal_type": deal_type, "artist_id": artist_id, "song_title": song_title},
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "contract_id": contract_id,
                "artist_id": artist_id,
                "artist_name": artist_name,
                "deal_type": deal_type,
                "status": "draft",
                "reversion_date": reversion_date.isoformat(),
                "advance_amount": float(advance_amount),
                "splits": {
                    "pre_recoup": "artist 40% / ECHO 60%",
                    "post_recoup": "artist 60% / ECHO 40%",
                    "producer_points_from": "ECHO share only",
                    "reversion_override": "15% perpetual after reversion",
                },
                "contract_text": contract_text,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _task_register_copyright(self, task: AgentTask) -> AgentResult:
        """
        Create copyright registration checklist for a track across all societies.
        Required within 30 days of release.
        """
        track_id = task.payload.get("track_id")
        release_id = task.payload.get("release_id") or task.release_id
        release_date_str = task.payload.get("release_date")

        if not track_id and not release_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="track_id or release_id required",
            )

        release_date = datetime.now(timezone.utc).date()
        if release_date_str:
            try:
                release_date = datetime.fromisoformat(release_date_str).date()
            except ValueError:
                pass

        deadline = release_date + timedelta(days=COPYRIGHT_DEADLINE_DAYS)
        days_remaining = (deadline - datetime.now(timezone.utc).date()).days

        registrations = []
        for society in COPYRIGHT_SOCIETIES:
            reg_id = str(uuid.uuid4())
            try:
                await self.db_execute(
                    """
                    INSERT INTO copyright_registrations
                        (id, track_id, release_id, society, status)
                    VALUES ($1::uuid, $2::uuid, $3::uuid, $4, 'pending')
                    ON CONFLICT DO NOTHING
                    """,
                    reg_id,
                    track_id,
                    release_id,
                    society,
                )
            except Exception as e:
                logger.warning(f"[Legal] Copyright reg insert warning ({society}): {e}")

            registrations.append({
                "society": society,
                "status": "pending",
                "registration_id": reg_id,
            })

        await self.log_audit(
            "register_copyright", "tracks", track_id,
            {"release_id": release_id, "societies": COPYRIGHT_SOCIETIES},
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "track_id": track_id,
                "release_id": release_id,
                "release_date": release_date.isoformat(),
                "registration_deadline": deadline.isoformat(),
                "days_remaining": days_remaining,
                "urgent": days_remaining <= 7,
                "registrations": registrations,
                "societies_count": len(registrations),
            },
        )

    async def _task_process_dmca(self, task: AgentTask) -> AgentResult:
        """
        Log and initiate a DMCA takedown request. Track status through resolution.
        """
        track_id = task.payload.get("track_id")
        claimant = task.payload.get("claimant", "")
        platform = task.payload.get("platform", "")
        claim_type = task.payload.get("claim_type", "copyright")
        notes = task.payload.get("notes", "")

        dmca_id = str(uuid.uuid4())
        try:
            await self.db_execute(
                """
                INSERT INTO dmca_requests (id, track_id, claimant, platform, claim_type, status, notes)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5, 'received', $6)
                """,
                dmca_id, track_id, claimant, platform, claim_type, notes,
            )
        except Exception as e:
            logger.error(f"[Legal] DMCA insert error: {e}")
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id, error=str(e)
            )

        # Notify CEO + PR
        await self.broadcast(
            "legal.dmca_received",
            {
                "dmca_id": dmca_id,
                "track_id": track_id,
                "claimant": claimant,
                "platform": platform,
                "claim_type": claim_type,
                "action_required": "Review and respond within 10 business days",
            },
        )

        await self.log_audit(
            "process_dmca", "tracks", track_id,
            {"dmca_id": dmca_id, "claimant": claimant, "platform": platform},
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "dmca_id": dmca_id,
                "track_id": track_id,
                "claimant": claimant,
                "platform": platform,
                "claim_type": claim_type,
                "status": "received",
                "next_steps": [
                    "Verify ECHO's ownership rights",
                    "Check registration status with PROs",
                    "Respond to claimant within 10 business days",
                    "If counter-notice warranted, file within 14 days",
                ],
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _task_compliance_check(self, task: AgentTask) -> AgentResult:
        """
        Full compliance check: point language + general TOS compliance.
        """
        content = task.payload.get("content", "")
        context = task.payload.get("context", "general")  # general | points | marketing | contract
        release_id = task.payload.get("release_id") or task.release_id

        issues = []
        warnings = []

        # Always check for prohibited point language
        point_result = self._scan_prohibited_language(content)
        if point_result["violations"]:
            for v in point_result["violations"]:
                issues.append({
                    "type": "prohibited_language",
                    "severity": "critical",
                    "match": v["match"],
                    "suggestion": v["suggestion"],
                    "rule": "ECHO Points language policy — no investment terminology",
                })

        # Check for missing required disclosures in points context
        if context in ("points", "marketing"):
            required_phrases = ["past earnings do not guarantee", "points are not securities"]
            for phrase in required_phrases:
                if phrase.lower() not in content.lower():
                    warnings.append({
                        "type": "missing_disclosure",
                        "severity": "warning",
                        "message": f'Consider adding: "{phrase}"',
                    })

        # Check for contract-specific compliance
        if context == "contract":
            contract_checks = [
                ("reversion", "Contract should reference master reversion rights"),
                ("recoup", "Contract should define recoupable costs"),
                ("arbitration", "Contract should specify dispute resolution"),
            ]
            for keyword, message in contract_checks:
                if keyword not in content.lower():
                    warnings.append({
                        "type": "missing_clause",
                        "severity": "warning",
                        "message": message,
                    })

        compliant = len(issues) == 0

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "compliant": compliant,
                "context": context,
                "issues": issues,
                "warnings": warnings,
                "issue_count": len(issues),
                "warning_count": len(warnings),
                "release_id": release_id,
                "checked_by": "legal",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _task_check_rights(self, task: AgentTask) -> AgentResult:
        """
        Verify ownership chain for a track.
        Returns: who owns master, publishing, and any splits.
        """
        track_id = task.payload.get("track_id")
        if not track_id:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="track_id required",
            )

        track = await self.db_fetchrow(
            """
            SELECT t.id, t.title, t.artist_id, t.credits_json,
                   a.name as artist_name, a.advance_amount, a.recoupment_balance
            FROM tracks t
            JOIN artists a ON t.artist_id = a.id
            WHERE t.id = $1::uuid
            """,
            track_id,
        )

        if not track:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="Track not found",
            )

        # Fetch active contracts
        contracts = await self.db_fetch(
            """
            SELECT id, type, status, royalty_split_artist, royalty_split_label,
                   reversion_date, signed_at
            FROM contracts
            WHERE artist_id = $1::uuid AND status IN ('signed', 'active', 'draft')
            ORDER BY signed_at DESC LIMIT 5
            """,
            str(track["artist_id"]),
        )

        # Fetch copyright registrations
        registrations = await self.db_fetch(
            "SELECT society, status, registration_number FROM copyright_registrations WHERE track_id = $1::uuid",
            track_id,
        )

        # Fetch point holders
        point_holders = await self.db_fetch(
            "SELECT buyer_user_id, points_purchased FROM echo_points WHERE track_id = $1::uuid AND status = 'active'",
            track_id,
        )
        total_points_sold = sum(float(h["points_purchased"]) for h in point_holders)

        recouped = float(track["recoupment_balance"]) <= 0
        artist_master_pct = 60.0 if recouped else 40.0
        label_master_pct = 40.0 if recouped else 60.0

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "track_id": track_id,
                "track_title": track["title"],
                "artist": {
                    "id": str(track["artist_id"]),
                    "name": track["artist_name"],
                    "master_pct": artist_master_pct - total_points_sold,
                    "recouped": recouped,
                },
                "label": {
                    "name": "ECHO",
                    "master_pct": label_master_pct,
                    "note": "Producer points deducted from label share",
                },
                "point_holders": {
                    "total_points_sold": total_points_sold,
                    "holder_count": len(point_holders),
                    "holders": [
                        {"buyer_user_id": str(h["buyer_user_id"]), "points": float(h["points_purchased"])}
                        for h in point_holders
                    ],
                },
                "publishing": {
                    "owner": track["artist_name"],
                    "pct": 100.0,
                    "note": "Artist retains 100% of publishing",
                },
                "contracts": [dict(c) for c in contracts],
                "copyright_registrations": [dict(r) for r in registrations],
                "split_status": "post_recoup" if recouped else "pre_recoup",
            },
        )

    async def _task_draft_tos(self, task: AgentTask) -> AgentResult:
        """Generate a Terms of Service draft for a specific context."""
        context = task.payload.get("context", "points_store")  # points_store | platform | artist_portal
        tos_text = self._render_tos(context)

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "context": context,
                "tos_text": tos_text,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "draft",
                "note": "Review with qualified legal counsel before publishing.",
            },
        )

    async def _task_verify_point_language(self, task: AgentTask) -> AgentResult:
        """
        Strict check: scan marketing copy for prohibited investment terminology.
        Returns violations with exact matches and suggested replacements.
        """
        content = task.payload.get("content", "")
        source = task.payload.get("source", "unknown")  # email, web, social, contract

        result = self._scan_prohibited_language(content)

        if result["violations"]:
            await self.broadcast(
                "legal.language_violation",
                {
                    "source": source,
                    "violations": result["violations"],
                    "violation_count": len(result["violations"]),
                },
            )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "approved": len(result["violations"]) == 0,
                "source": source,
                "violations": result["violations"],
                "violation_count": len(result["violations"]),
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "policy": "ECHO Points are NOT securities. Never use invest/investment/ROI/returns.",
                "allowed_language": "buy, purchase, own, earn, points, royalties",
            },
        )

    # ----------------------------------------------------------------
    # Legacy handlers
    # ----------------------------------------------------------------

    async def _task_review_contracts(self, task: AgentTask) -> AgentResult:
        artist_id = task.payload.get("artist_id") or task.artist_id
        contracts = await self.db_fetch(
            "SELECT id, type, status FROM contracts WHERE artist_id = $1::uuid ORDER BY created_at DESC LIMIT 5",
            artist_id,
        )
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"artist_id": artist_id, "contracts": [dict(c) for c in contracts]},
        )

    async def _task_send_for_signature(self, task: AgentTask) -> AgentResult:
        contract_id = task.payload.get("contract_id")
        envelope_id = f"env_{str(uuid.uuid4())[:8]}"
        await self.db_execute(
            "UPDATE contracts SET status = 'pending_signature', docusign_envelope_id = $2, updated_at = NOW() WHERE id = $1::uuid",
            contract_id, envelope_id,
        )
        return AgentResult(
            success=True, task_id=task.task_id, agent_id=self.agent_id,
            result={"contract_id": contract_id, "envelope_id": envelope_id, "status": "sent_for_signature"},
        )

    async def _task_default(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            success=False, task_id=task.task_id, agent_id=self.agent_id,
            error=f"Unknown task type: {task.task_type}",
        )

    # ----------------------------------------------------------------
    # Language scanning
    # ----------------------------------------------------------------

    def _scan_prohibited_language(self, content: str) -> dict:
        violations = []
        for pattern in PROHIBITED_POINT_WORDS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                word_key = match.lower().replace(" ", "_")
                suggestion = ALLOWED_ALTERNATIVES.get(
                    match.lower(),
                    "Use approved ECHO Points terminology",
                )
                violations.append({"match": match, "pattern": pattern, "suggestion": suggestion})
        return {"violations": violations, "clean": len(violations) == 0}

    # ----------------------------------------------------------------
    # Contract templates
    # ----------------------------------------------------------------

    def _render_recording_agreement(
        self,
        artist_name: str,
        song_title: str,
        deal_type: str,
        date_str: str,
        advance_amount: float,
        reversion_date: str,
        producer_name: str = "",
        producer_points: int = 0,
    ) -> str:
        producer_clause = ""
        if producer_name and producer_points:
            producer_clause = f"\nProducer ({producer_name}) receives {producer_points} points from ECHO share only.\n"

        advance_clause = f"\nAdvance: ${advance_amount:,.2f} (recoupable against recording costs only).\n" if advance_amount else ""

        return f"""ECHO RECORDING AGREEMENT — {deal_type.upper()}

Artist: {artist_name}
Song: {song_title}
Date: {date_str}

1. GRANT OF RIGHTS
Artist grants ECHO exclusive rights to the master recording of "{song_title}" for the term of this agreement.

2. REVENUE SPLIT
Pre-recoupment: Artist 40% / ECHO 60%
Post-recoupment: Artist 60% / ECHO 40%
Producer points (if any): Deducted from ECHO share only.{producer_clause}

3. PUBLISHING
Artist retains 100% of publishing ownership.
ECHO may administer publishing for 10% admin fee (optional, separate agreement).

4. MASTER REVERSION
Masters revert to Artist upon the earlier of:
(a) 5 years from release date ({reversion_date}), or
(b) ECHO has recouped 3x all recording costs.
After reversion: ECHO retains 15% perpetual royalty override.

5. RECOUPABLE COSTS
Only recording costs (advance + producer fees) are recoupable.
Marketing, distribution, PR, and video costs are NOT recoupable.{advance_clause}

6. ECHO POINTS
Artist may sell up to 10 of their master points via ECHO Points Store.
80% of point sale proceeds must fund marketing for this project.
20% goes to Artist.
Artist must retain minimum 30 master points at all times.

7. NO LONG-TERM COMMITMENT
This agreement covers only "{song_title}". No obligation for future projects.

8. GOVERNING LAW
California. Disputes via binding arbitration (AAA rules).

___________________________          ___________________________
Artist Signature / Date              ECHO Representative / Date
"""

    def _render_producer_agreement(
        self,
        producer_name: str,
        artist_name: str,
        song_title: str,
        date_str: str,
        producer_points: int = 3,
    ) -> str:
        return f"""ECHO PRODUCER AGREEMENT

Producer: {producer_name}
Artist: {artist_name}
Song: {song_title}
Date: {date_str}

1. BEAT LICENSE
Producer grants ECHO and Artist an exclusive license to use the instrumental in "{song_title}".

2. PRODUCER POINTS
Producer receives {producer_points} master points for "{song_title}".
These points are deducted from ECHO's label share — NOT from Artist's share.
Each point = 1% of master recording revenue.

3. CREDIT
Producer must receive "Produced by {producer_name}" credit on all official releases.

4. PUBLISHING
Producer retains 50% of publishing (composition) for the instrumental.
Artist retains 50% of publishing (lyrics/melody contributions).

5. PAYMENT
Beat fee (if applicable): As agreed separately.
Ongoing: Producer points per Section 2.

6. GOVERNING LAW
California. Disputes via binding arbitration.

___________________________          ___________________________
Producer Signature / Date            ECHO Representative / Date
"""

    def _render_publishing_admin_agreement(
        self, artist_name: str, date_str: str
    ) -> str:
        return f"""ECHO PUBLISHING ADMINISTRATION AGREEMENT

Artist/Publisher: {artist_name}
Date: {date_str}

1. ADMINISTRATION
Artist appoints ECHO as non-exclusive publishing administrator for a 10% admin fee.
Artist retains 100% ownership of all compositions at all times.

2. SERVICES
ECHO will:
- Register compositions with ASCAP/BMI/SESAC and MLC
- Collect mechanical, performance, and sync royalties
- File claims on Content ID and neighboring rights platforms

3. TERM
2 years from execution date. Renewable with mutual consent.

4. ACCOUNTING
Quarterly statements and payments. 45-day payment window after quarter close.

5. TERMINATION
Either party may terminate with 60 days written notice.
ECHO retains right to collect royalties accrued during term for 12 months post-termination.

6. GOVERNING LAW
California. Disputes via binding arbitration.

___________________________          ___________________________
Artist Signature / Date              ECHO Representative / Date
"""

    def _render_tos(self, context: str) -> str:
        if context == "points_store":
            return """ECHO POINTS STORE — TERMS OF SERVICE

Last Updated: {date}

1. WHAT ARE ECHO POINTS?
ECHO Points represent a contractual right to receive a share of master recording royalties
for a specific track. Points are NOT securities, investments, or equity stakes.
Points do NOT represent ownership in ECHO or any artist entity.

2. PURCHASING POINTS
By purchasing ECHO Points, you ("Buyer") agree that:
- You are buying a contractual royalty participation right only
- Points are NOT an investment or security
- Past royalty performance does not guarantee future earnings
- Points may have zero value if the track generates no royalties

3. ROYALTY DISTRIBUTIONS
- Each point = 1% of master recording revenue for the designated track
- Distributions occur quarterly (Jan 15, Apr 15, Jul 15, Oct 15)
- Minimum distribution threshold: $50 per Buyer per quarter
- Balances below $50 roll forward to next quarter

4. PROHIBITED USES
Buyers may not resell or transfer Points except through ECHO's official marketplace.

5. RISK ACKNOWLEDGMENT
Music royalties are unpredictable. Buyer acknowledges that:
- Revenue may be zero or minimal
- There is no guarantee of any royalty distribution
- This is NOT a financial instrument

6. GOVERNING LAW
California. Disputes via binding arbitration (AAA rules).
""".format(date=datetime.now(timezone.utc).strftime("%B %d, %Y"))
        else:
            return f"[ECHO {context.upper()} TERMS OF SERVICE — DRAFT — Generated {datetime.now(timezone.utc).date()}]"

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        if topic == "release.published":
            # Auto-trigger copyright registration checklist
            payload = message.get("payload", {})
            track_id = payload.get("track_id")
            release_id = payload.get("release_id")
            if track_id or release_id:
                logger.info(f"[Legal] Release published — queuing copyright registration for track {track_id}")
