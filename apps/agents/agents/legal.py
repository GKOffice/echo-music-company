"""
ECHO Legal Agent — Worldwide Compliance Edition
Drafts and manages contracts, handles copyright registration,
monitors DMCA/global takedowns, verifies compliance (no invest/ROI language),
tracks rights ownership, and enforces GDPR, FATF, Berne Convention standards.

TEMPLATE ONLY — Not legal advice. Review with qualified counsel in each jurisdiction.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timezone, date, timedelta
from typing import Optional

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# Prohibited language — global securities law
# ----------------------------------------------------------------
PROHIBITED_POINT_WORDS = [
    r"\binvest\b", r"\binvestment\b", r"\binvestments\b", r"\binvestor\b", r"\binvestors\b",
    r"\bROI\b", r"\breturn on investment\b", r"\breturns\b", r"\bfinancial returns\b",
    r"\bsecurities\b", r"\bsecurity\b", r"\bshares\b", r"\bequity\b", r"\bdividend\b",
    r"\bprofit sharing\b", r"\bspeculate\b", r"\bspeculation\b",
    # EU / international securities terms
    r"\bWertpapier\b", r"\bValeurs mobilières\b",
    # Crypto / token investment context
    r"\btoken\b", r"\bcrypto\b",
    # Additional high-risk financial terms
    r"\bguaranteed returns\b", r"\bcapital gain\b", r"\bappreciation\b",
]

ALLOWED_ALTERNATIVES = {
    "invest": "buy / purchase / own",
    "investment": "purchase / points",
    "ROI": "royalties earned",
    "returns": "royalties / earnings",
    "securities": "points",
    "equity": "master points",
    "wertpapier": "Punkte (points)",
    "valeurs mobilières": "points de redevance",
    "token": "points / credits",
    "crypto": "digital points",
    "guaranteed returns": "potential royalty earnings",
    "capital gain": "royalty earnings",
    "appreciation": "royalty growth",
}

# ----------------------------------------------------------------
# Copyright Societies — 60+ global PROs
# ----------------------------------------------------------------
COPYRIGHT_SOCIETIES = [
    # United States
    "ascap", "bmi", "sesac", "mlc", "soundexchange", "songtrust",
    "copyright_office", "content_id",
    # United Kingdom
    "prs_for_music", "ppl_uk",
    # Germany
    "gema", "gvl",
    # France
    "sacem", "scpp", "sppf",
    # Italy
    "siae",
    # Spain
    "sgae",
    # Netherlands
    "buma_stemra",
    # Scandinavia
    "stim", "koda", "tono", "teosto",
    # Australia / New Zealand
    "apra_amcos",
    # Japan
    "jasrac",
    # Canada
    "socan", "re_sound",
    # Brazil
    "ecad",
    # Mexico
    "sacm",
    # South Africa
    "samro",
    # International umbrella
    "cisac", "wipo",
]

COPYRIGHT_DEADLINE_DAYS = 30  # Register within 30 days of release

# ----------------------------------------------------------------
# GDPR
# ----------------------------------------------------------------
GDPR_REQUIRED_FIELDS = [
    "data_controller", "lawful_basis", "retention_period", "data_subject_rights",
]

PERSONAL_DATA_CATEGORIES = [
    "name", "email", "address", "payment", "credit card", "bank",
    "biometric", "photo", "location", "ip address", "device id",
    "date of birth", "phone", "national id", "passport",
]

# ----------------------------------------------------------------
# KYC / AML — FATF high-risk countries (ISO 3166-1 alpha-2)
# ----------------------------------------------------------------
FATF_HIGH_RISK_COUNTRIES = [
    "IR", "KP", "MM", "SY", "YE", "IQ", "LY", "SD", "SO",
    "AF", "VU", "PK", "HT",
]

# ----------------------------------------------------------------
# Governing law clauses
# ----------------------------------------------------------------
GOVERNING_LAW_CLAUSES = {
    "california_us": (
        "This Agreement is governed by the laws of the State of California, USA. "
        "All disputes shall be resolved by binding arbitration under AAA Commercial Rules, "
        "seated in Los Angeles, California."
    ),
    "england_wales": (
        "This Agreement is governed by the laws of England and Wales. "
        "Disputes shall be resolved by arbitration under LCIA Rules, seated in London."
    ),
    "germany": (
        "This Agreement is governed by the laws of Germany. "
        "Disputes shall be resolved by arbitration under DIS Rules, seated in Frankfurt."
    ),
    "france": (
        "This Agreement is governed by the laws of France. "
        "Disputes shall be resolved by arbitration under ICC Rules, seated in Paris."
    ),
    "australia": (
        "This Agreement is governed by the laws of New South Wales, Australia. "
        "Disputes shall be resolved by arbitration under ACICA Rules, seated in Sydney."
    ),
    "international_icc": (
        "This Agreement is governed by the UNIDROIT Principles of International Commercial Contracts. "
        "Disputes shall be resolved by arbitration under ICC International Court of Arbitration Rules, "
        "seated in Geneva. The language of arbitration shall be English."
    ),
}

SUPPORTED_JURISDICTIONS = [
    {"id": "california_us", "name": "California, USA", "body": "AAA Commercial Arbitration"},
    {"id": "england_wales", "name": "England and Wales", "body": "LCIA Arbitration, London"},
    {"id": "germany", "name": "Germany", "body": "DIS Arbitration, Frankfurt"},
    {"id": "france", "name": "France", "body": "ICC Arbitration, Paris"},
    {"id": "australia", "name": "New South Wales, Australia", "body": "ACICA Arbitration, Sydney"},
    {"id": "international_icc", "name": "International (ICC)", "body": "ICC International Court of Arbitration, Geneva"},
]

# ----------------------------------------------------------------
# Global takedown regimes
# ----------------------------------------------------------------
TAKEDOWN_REGIMES = {
    "dmca_us": {
        "name": "DMCA (US)",
        "law": "Digital Millennium Copyright Act 17 U.S.C. § 512",
        "response_window": "10 business days",
        "response_days": 10,
    },
    "dsa_eu": {
        "name": "DSA (EU)",
        "law": "Digital Services Act (EU) 2022/2065, Article 16",
        "response_window": "24–72 hours for illegal content; 7 days general",
        "response_days": 1,
    },
    "osa_uk": {
        "name": "Online Safety Act (UK)",
        "law": "Online Safety Act 2023 (UK)",
        "response_window": "7 days",
        "response_days": 7,
    },
    "osa_au": {
        "name": "Online Safety Act (Australia)",
        "law": "Online Safety Act 2021 (Cth)",
        "response_window": "48 hours for class 1 material; 7 days general",
        "response_days": 2,
    },
    "nnr_ca": {
        "name": "Notice-and-Notice (Canada)",
        "law": "Copyright Act (Canada) R.S.C. 1985, c. C-42, s. 41.25",
        "response_window": "Forward notice within a reasonable time",
        "response_days": 5,
    },
    "plla_jp": {
        "name": "Provider Liability Limitation Act (Japan)",
        "law": "Provider Liability Limitation Act (Japan) Act No. 137 of 2001",
        "response_window": "7 days",
        "response_days": 7,
    },
}


class LegalAgent(BaseAgent):
    agent_id = "legal"
    agent_name = "Legal Agent"
    subscriptions = ["artist.signed", "contract.disputed", "release.published", "agent.legal"]

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Legal] Online. Worldwide compliance active: GDPR, Berne, ICC, FATF, DSA, 60+ PROs.")

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "generate_contract": self._task_generate_contract,
            "register_copyright": self._task_register_copyright,
            "process_dmca": self._task_process_dmca,
            "compliance_check": self._task_compliance_check,
            "check_rights": self._task_check_rights,
            "draft_tos": self._task_draft_tos,
            "verify_point_language": self._task_verify_point_language,
            "gdpr_check": self._task_gdpr_check,
            "kyc_check": self._task_kyc_check,
            "contract_shield": self._task_contract_shield,
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
        territory = task.payload.get("territory", "worldwide")
        governing_law = task.payload.get("governing_law", "california_us")

        if governing_law not in GOVERNING_LAW_CLAUSES:
            governing_law = "california_us"

        territory_lower = territory.lower()
        needs_gdpr = any(t in territory_lower for t in ["eu", "eea", "uk", "europe", "worldwide"])

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
                territory=territory,
                governing_law=governing_law,
            )
        elif deal_type == "producer":
            contract_text = self._render_producer_agreement(
                producer_name=producer_name or "Producer",
                artist_name=artist_name,
                song_title=song_title or "[SONG TITLE]",
                date_str=today.strftime("%B %d, %Y"),
                producer_points=producer_points,
                territory=territory,
                governing_law=governing_law,
            )
        elif deal_type == "publishing_admin":
            contract_text = self._render_publishing_admin_agreement(
                artist_name=artist_name,
                date_str=today.strftime("%B %d, %Y"),
                territory=territory,
                governing_law=governing_law,
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
                    "territory": territory,
                    "governing_law": governing_law,
                    "gdpr_addendum": needs_gdpr,
                    "kyc_verified": False,
                }),
                40.0,
                60.0,
                float(advance_amount),
                reversion_date,
                today,
            )
        except Exception as e:
            logger.error(f"[Legal] Contract DB insert error: {e}")

        await self.log_audit(
            "generate_contract", "contracts", contract_id,
            {
                "deal_type": deal_type, "artist_id": artist_id, "song_title": song_title,
                "territory": territory, "governing_law": governing_law,
            },
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
                "territory": territory,
                "governing_law": governing_law,
                "gdpr_addendum": needs_gdpr,
                "kyc_verified": False,
                "splits": {
                    "pre_recoup": "artist 40% / ECHO 60%",
                    "post_recoup": "artist 60% / ECHO 40%",
                    "producer_points_from": "ECHO share only",
                    "reversion_override": "15% perpetual after reversion",
                },
                "contract_text": contract_text,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "disclaimer": "TEMPLATE ONLY — Not legal advice. Review with qualified counsel in each jurisdiction.",
            },
        )

    async def _task_register_copyright(self, task: AgentTask) -> AgentResult:
        """
        Create copyright registration checklist for a track across all 30+ societies.
        Required within 30 days of release. Covers Berne Convention signatory nations.
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
                "berne_convention": (
                    "Copyright protections granted under Berne Convention (1886, as amended) "
                    "across all 181 signatory nations."
                ),
            },
        )

    async def _task_process_dmca(self, task: AgentTask) -> AgentResult:
        """
        Log and initiate a takedown request under the specified regime.
        Supports: DMCA (US), DSA (EU), OSA (UK/AU), NNR (CA), PLLA (JP).
        """
        track_id = task.payload.get("track_id")
        claimant = task.payload.get("claimant", "")
        platform = task.payload.get("platform", "")
        claim_type = task.payload.get("claim_type", "copyright")
        notes = task.payload.get("notes", "")
        takedown_regime = task.payload.get("takedown_regime", "dmca_us")

        if takedown_regime not in TAKEDOWN_REGIMES:
            takedown_regime = "dmca_us"

        regime_info = TAKEDOWN_REGIMES[takedown_regime]
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

        await self.broadcast(
            "legal.dmca_received",
            {
                "dmca_id": dmca_id,
                "track_id": track_id,
                "claimant": claimant,
                "platform": platform,
                "claim_type": claim_type,
                "takedown_regime": takedown_regime,
                "regime_name": regime_info["name"],
                "action_required": f"Review and respond within {regime_info['response_window']}",
            },
        )

        await self.log_audit(
            "process_dmca", "tracks", track_id,
            {
                "dmca_id": dmca_id, "claimant": claimant,
                "platform": platform, "takedown_regime": takedown_regime,
            },
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
                "takedown_regime": takedown_regime,
                "regime": regime_info,
                "next_steps": [
                    "Verify ECHO's ownership rights",
                    "Check registration status with PROs",
                    f"Respond to claimant within {regime_info['response_window']}",
                    "If counter-notice warranted, file within 14 days",
                ],
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _task_compliance_check(self, task: AgentTask) -> AgentResult:
        """
        Full compliance check: point language + GDPR + DSA + MiFID II/FCA/ASIC.
        """
        content = task.payload.get("content", "")
        context = task.payload.get("context", "general")
        territory = task.payload.get("territory", "")
        release_id = task.payload.get("release_id") or task.release_id

        issues = []
        warnings = []

        # Always check for prohibited point/investment language
        point_result = self._scan_prohibited_language(content)
        if point_result["violations"]:
            for v in point_result["violations"]:
                issues.append({
                    "type": "prohibited_language",
                    "severity": "critical",
                    "match": v["match"],
                    "suggestion": v["suggestion"],
                    "rule": "ECHO Points language policy — no investment terminology (global)",
                })

        # Points / marketing disclosures
        if context in ("points", "marketing"):
            for phrase in ["past earnings do not guarantee", "points are not securities"]:
                if phrase.lower() not in content.lower():
                    warnings.append({
                        "type": "missing_disclosure",
                        "severity": "warning",
                        "message": f'Consider adding: "{phrase}"',
                    })

        # Contract checks
        if context == "contract":
            for keyword, message in [
                ("reversion", "Contract should reference master reversion rights"),
                ("recoup", "Contract should define recoupable costs"),
                ("arbitration", "Contract should specify dispute resolution"),
                ("berne", "Contract should reference Berne Convention for international protection"),
            ]:
                if keyword not in content.lower():
                    warnings.append({
                        "type": "missing_clause",
                        "severity": "warning",
                        "message": message,
                    })

        # GDPR checks — EU/EEA/UK territory
        territory_lower = territory.lower()
        is_eu = any(t in territory_lower for t in ["eu", "eea", "uk", "europe", "worldwide"])
        if is_eu or context in ("contract", "platform", "artist_portal"):
            for field in GDPR_REQUIRED_FIELDS:
                if field.replace("_", " ") not in content.lower():
                    warnings.append({
                        "type": "gdpr_missing_field",
                        "severity": "warning",
                        "message": (
                            f"GDPR: Consider disclosing '{field.replace('_', ' ')}' "
                            f"per GDPR Art. 13/14"
                        ),
                    })

        # DSA checks — platform / marketing
        if context in ("platform", "marketing"):
            for keyword, message in [
                ("transparency", "DSA Art. 26: Advertising transparency disclosure required"),
                ("recommender", "DSA Art. 27: Algorithmic recommendation system disclosure"),
                ("contact", "DSA Art. 12: Accessible contact point for authorities required"),
            ]:
                if keyword not in content.lower():
                    warnings.append({
                        "type": "dsa_missing",
                        "severity": "warning",
                        "message": message,
                    })

        # Financial context — MiFID II / FCA / ASIC
        if context == "financial":
            for phrase, message in [
                ("risk warning", "FCA/ASIC/MiFID II: Prominent risk warning required"),
                ("not financial advice", "Disclaimer: 'Not financial advice' required"),
                ("past performance", "Required: past performance disclaimer"),
            ]:
                if phrase not in content.lower():
                    warnings.append({
                        "type": "financial_warning_missing",
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
                "territory": territory,
                "eu_territory": is_eu,
                "issues": issues,
                "warnings": warnings,
                "issue_count": len(issues),
                "warning_count": len(warnings),
                "release_id": release_id,
                "checked_by": "legal",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _task_gdpr_check(self, task: AgentTask) -> AgentResult:
        """
        GDPR compliance review for content or document.
        Checks for personal data, lawful basis, retention period, and data subject rights.
        """
        content = task.payload.get("content", "")
        context = task.payload.get("context", "general")

        issues = []
        recommendations = []
        content_lower = content.lower()

        # Detect personal data categories
        detected_personal_data = [cat for cat in PERSONAL_DATA_CATEGORIES if cat in content_lower]

        # Check required GDPR disclosure fields
        article_map = {
            "data_controller": "GDPR Art. 13(1)(a)",
            "lawful_basis": "GDPR Art. 13(1)(c)",
            "retention_period": "GDPR Art. 13(2)(a)",
            "data_subject_rights": "GDPR Art. 13(2)(b)",
        }
        missing_fields = []
        for field in GDPR_REQUIRED_FIELDS:
            if field.replace("_", " ") not in content_lower:
                missing_fields.append(field)
                issues.append({
                    "field": field,
                    "message": f"Missing required GDPR disclosure: {field.replace('_', ' ')}",
                    "article": article_map.get(field, "GDPR Art. 13/14"),
                })

        # Check processing purpose
        if "purpose" not in content_lower and detected_personal_data:
            issues.append({
                "field": "processing_purpose",
                "message": "Data processing purpose not stated (GDPR Art. 5(1)(b) — purpose limitation)",
                "article": "GDPR Art. 5(1)(b)",
            })

        # Check lawful basis
        lawful_bases = [
            "consent", "contract", "legitimate interest",
            "legal obligation", "vital interests", "public task",
        ]
        has_lawful_basis = any(basis in content_lower for basis in lawful_bases)
        if not has_lawful_basis and detected_personal_data:
            issues.append({
                "field": "lawful_basis",
                "message": (
                    "No valid GDPR lawful basis identified (Art. 6). "
                    "Must state: consent / contract / legitimate interest / legal obligation."
                ),
                "article": "GDPR Art. 6",
            })

        # Recommendations
        if detected_personal_data:
            recommendations.append(
                f"Personal data detected: {', '.join(detected_personal_data)}. "
                "Ensure Article 30 processing record is maintained."
            )
        if "transfer" in content_lower or "third party" in content_lower:
            recommendations.append(
                "International data transfers: Ensure SCCs / adequacy decision in place (GDPR Art. 46)."
            )
        recommendations.append(
            "Appoint a Data Protection Officer if processing large-scale special category data (GDPR Art. 37)."
        )
        recommendations.append(
            "Conduct DPIA for high-risk processing activities (GDPR Art. 35)."
        )

        gdpr_compliant = len(issues) == 0

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "gdpr_compliant": gdpr_compliant,
                "context": context,
                "detected_personal_data": detected_personal_data,
                "missing_fields": missing_fields,
                "issues": issues,
                "recommendations": recommendations,
                "issue_count": len(issues),
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "disclaimer": "TEMPLATE ONLY — Not legal advice. Review with qualified GDPR counsel.",
            },
        )

    async def _task_kyc_check(self, task: AgentTask) -> AgentResult:
        """
        KYC/AML tier determination per FATF recommendations.
        Returns required verification tier, tax form requirements, and sanctions flags.
        """
        user_id = task.payload.get("user_id", "")
        country_code = task.payload.get("country_code", "US").upper()
        purchase_amount = float(task.payload.get("purchase_amount", 0))
        annual_royalties = float(task.payload.get("annual_royalties", 0))
        is_us_person = task.payload.get("is_us_person", False)

        # Sanctions / FATF check (always required)
        sanctions_flagged = country_code in FATF_HIGH_RISK_COUNTRIES
        fatf_high_risk = country_code in FATF_HIGH_RISK_COUNTRIES

        # KYC tier
        if purchase_amount < 500:
            kyc_tier = 1
            verification_required = ["email", "phone"]
            tier_description = "Tier 1: Email + phone verification"
        elif purchase_amount <= 5000:
            kyc_tier = 2
            verification_required = ["email", "phone", "government_id"]
            tier_description = "Tier 2: Government ID required (Persona API)"
        else:
            kyc_tier = 3
            verification_required = [
                "email", "phone", "government_id",
                "source_of_funds", "enhanced_due_diligence",
            ]
            tier_description = "Tier 3: Enhanced due diligence + source of funds"

        # Tax form requirements
        tax_form_required = None
        if is_us_person and annual_royalties > 600:
            tax_form_required = "W-9"
        elif not is_us_person and annual_royalties > 0:
            tax_form_required = "W-8BEN"

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "user_id": user_id,
                "country_code": country_code,
                "purchase_amount": purchase_amount,
                "kyc_tier": kyc_tier,
                "tier_description": tier_description,
                "verification_required": verification_required,
                "tax_form_required": tax_form_required,
                "sanctions_flagged": sanctions_flagged,
                "fatf_high_risk": fatf_high_risk,
                "ofac_check_required": True,
                "aml_note": (
                    "ECHO applies AML/KYC per FATF recommendations. "
                    "Identity verification required for point purchases > $500."
                ),
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

        registrations = await self.db_fetch(
            "SELECT society, status, registration_number FROM copyright_registrations WHERE track_id = $1::uuid",
            track_id,
        )

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
                "berne_convention": "Protected under Berne Convention (1886) across 181 signatory nations.",
            },
        )

    async def _task_draft_tos(self, task: AgentTask) -> AgentResult:
        """Generate a Terms of Service draft for a specific context."""
        context = task.payload.get("context", "points_store")
        territory = task.payload.get("territory", "worldwide")
        tos_text = self._render_tos(context, territory)

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "context": context,
                "territory": territory,
                "tos_text": tos_text,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "draft",
                "note": "TEMPLATE ONLY — Not legal advice. Review with qualified counsel before publishing.",
            },
        )

    async def _task_verify_point_language(self, task: AgentTask) -> AgentResult:
        """
        Strict check: scan marketing copy for prohibited investment terminology (global).
        Returns violations with exact matches and suggested replacements.
        """
        content = task.payload.get("content", "")
        source = task.payload.get("source", "unknown")

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
                "policy": "ECHO Points are NOT securities. Never use invest/investment/ROI/returns/token/crypto.",
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

    # ----------------------------------------------------------------
    # Hero skill: Contract Shield
    # ----------------------------------------------------------------

    # Predatory clause patterns for keyword-based fallback scan
    _PREDATORY_PATTERNS = {
        "rights_grab": {
            "keywords": ["perpetual", "worldwide", "irrevocable", "all rights", "in perpetuity"],
            "reversion_keywords": ["reversion", "revert", "reversion clause"],
            "description": "Perpetual/worldwide rights without reversion clause",
            "severity": "critical",
        },
        "360_deal": {
            "keywords": ["360", "live performance", "merchandise", "endorsement", "sponsorship",
                         "touring", "brand deal"],
            "label_cut_keywords": ["percentage", "percent", "%", "share", "portion"],
            "description": "Label taking percentage of non-recording revenue (360 deal)",
            "severity": "high",
        },
        "unconscionable_term": {
            "keywords": ["years", "albums", "lp", "album option", "option period"],
            "description": "Unreasonable contract length (>7 years or >5 album commitment)",
            "severity": "high",
        },
        "low_royalty_rate": {
            "keywords": ["royalty", "royalties", "net receipts", "net sales"],
            "description": "Royalty rate below market standard (<15% recording / <75% publishing net)",
            "severity": "high",
        },
        "no_audit_rights": {
            "keywords": ["audit", "accounting", "inspection", "examine"],
            "description": "Missing audit rights clause",
            "severity": "medium",
        },
        "unilateral_changes": {
            "keywords": ["sole discretion", "without consent", "unilaterally", "may modify",
                         "reserves the right to change"],
            "description": "Label can change terms without artist consent",
            "severity": "high",
        },
        "no_exit_clause": {
            "keywords": ["termination", "terminate", "exit", "release from"],
            "description": "No exit clause if label fails to perform",
            "severity": "medium",
        },
    }

    _CONTRACT_GRADE_THRESHOLDS = {
        "A": (0, 1),   # 0-1 flags
        "B": (2, 2),   # 2 flags
        "C": (3, 3),   # 3 flags
        "D": (4, 99),  # 4+ flags
    }

    def _keyword_scan_contract(self, contract_text: str, contract_type: str) -> list[dict]:
        """Keyword-based contract scan used as fallback when no Claude key is available."""
        text_lower = contract_text.lower()
        flags = []

        # Rights grab: look for perpetual/worldwide without reversion
        p = self._PREDATORY_PATTERNS["rights_grab"]
        has_perpetual = any(k in text_lower for k in p["keywords"])
        has_reversion = any(k in text_lower for k in p["reversion_keywords"])
        if has_perpetual and not has_reversion:
            flags.append({"flag": "rights_grab", "description": p["description"], "severity": p["severity"]})

        # 360 deal
        p = self._PREDATORY_PATTERNS["360_deal"]
        has_360_scope = any(k in text_lower for k in p["keywords"])
        has_cut = any(k in text_lower for k in p["label_cut_keywords"])
        if has_360_scope and has_cut:
            flags.append({"flag": "360_deal", "description": p["description"], "severity": p["severity"]})

        # Term length — look for numbers > 7 near "year" or > 5 near "album"
        year_matches = re.findall(r'(\d+)\s*(?:-\s*)?year', text_lower)
        album_matches = re.findall(r'(\d+)\s*(?:-\s*)?album', text_lower)
        if any(int(y) > 7 for y in year_matches) or any(int(a) > 5 for a in album_matches):
            p = self._PREDATORY_PATTERNS["unconscionable_term"]
            flags.append({"flag": "unconscionable_term", "description": p["description"], "severity": p["severity"]})

        # Low royalty rate
        royalty_pct_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', text_lower)
        if royalty_pct_matches:
            rates = [float(r) for r in royalty_pct_matches]
            if contract_type in ("recording", "distribution") and any(r < 15 for r in rates):
                p = self._PREDATORY_PATTERNS["low_royalty_rate"]
                flags.append({"flag": "low_royalty_rate",
                               "description": f"{p['description']} — found rates: {rates[:5]}",
                               "severity": p["severity"]})
            elif contract_type == "publishing" and any(r < 75 for r in rates):
                p = self._PREDATORY_PATTERNS["low_royalty_rate"]
                flags.append({"flag": "low_royalty_rate",
                               "description": f"{p['description']} — found rates: {rates[:5]}",
                               "severity": p["severity"]})

        # No audit rights
        p = self._PREDATORY_PATTERNS["no_audit_rights"]
        if not any(k in text_lower for k in p["keywords"]):
            flags.append({"flag": "no_audit_rights", "description": p["description"], "severity": p["severity"]})

        # Unilateral changes
        p = self._PREDATORY_PATTERNS["unilateral_changes"]
        if any(k in text_lower for k in p["keywords"]):
            flags.append({"flag": "unilateral_changes", "description": p["description"], "severity": p["severity"]})

        # No exit clause
        p = self._PREDATORY_PATTERNS["no_exit_clause"]
        if not any(k in text_lower for k in p["keywords"]):
            flags.append({"flag": "no_exit_clause", "description": p["description"], "severity": p["severity"]})

        return flags

    def _grade_contract(self, flags: list[dict]) -> str:
        # Automatic F if rights grab is present
        if any(f["flag"] == "rights_grab" for f in flags):
            return "F"
        n = len(flags)
        if n <= 1:
            return "A"
        if n == 2:
            return "B"
        if n == 3:
            return "C"
        return "D"

    async def _task_contract_shield(self, task: AgentTask) -> AgentResult:
        """
        Contract Shield hero skill.
        Scans contract text for predatory clauses and grades the contract.
        Uses Claude AI when available; falls back to keyword analysis.
        """
        contract_text = task.payload.get("contract_text", "")
        contract_type = task.payload.get("contract_type", "recording")

        if not contract_text:
            return AgentResult(
                success=False, task_id=task.task_id, agent_id=self.agent_id,
                error="contract_text required",
            )

        flags: list[dict] = []
        analysis_method = "keyword"

        # Try Claude first
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            try:
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=api_key)

                system_prompt = (
                    "You are a music industry contract lawyer. Analyze the provided contract text "
                    "for predatory clauses. Return a JSON object with a 'flags' array. "
                    "Each flag must have: flag (string key), description (plain English), severity (critical/high/medium/low). "
                    "Check for: rights_grab (perpetual/worldwide without reversion), 360_deal (label takes % of live/merch/endorsements), "
                    "unconscionable_term (>7 years or >5 album commitment), low_royalty_rate (<15% recording or <75% publishing net), "
                    "no_audit_rights (missing audit clause), unilateral_changes (label can change terms unilaterally), "
                    "no_exit_clause (no exit if label fails to perform). "
                    "Respond ONLY with valid JSON, no markdown."
                )

                response = await client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                f"Contract type: {contract_type}\n\n"
                                f"CONTRACT TEXT:\n{contract_text[:12000]}\n\n"
                                "Return JSON: {\"flags\": [{\"flag\": ..., \"description\": ..., \"severity\": ...}]}"
                            ),
                        }
                    ],
                    system=system_prompt,
                )

                import json as _json
                raw = response.content[0].text.strip()
                parsed = _json.loads(raw)
                flags = parsed.get("flags", [])
                analysis_method = "claude"
            except Exception as e:
                logger.warning(f"[Legal] Contract Shield Claude analysis failed: {e}. Falling back to keyword scan.")
                flags = self._keyword_scan_contract(contract_text, contract_type)
        else:
            flags = self._keyword_scan_contract(contract_text, contract_type)

        grade = self._grade_contract(flags)
        flag_count = len(flags)

        grade_summaries = {
            "A": "Contract looks fair — minimal red flags. Review with counsel before signing.",
            "B": "Contract has some concerning clauses — negotiate before signing.",
            "C": "Contract has multiple problematic clauses — significant negotiation required.",
            "D": "Contract is highly predatory — do not sign without major revisions and legal counsel.",
            "F": "Contract contains a rights grab — this is an unacceptable rights transfer. Do not sign.",
        }

        recommendations = {
            "A": "Proceed with standard legal review. Minor cleanup may be needed.",
            "B": "Request amendments on flagged clauses before proceeding.",
            "C": "Require substantial redrafting. Consult a music industry attorney.",
            "D": "This contract is artist-hostile. Engage an entertainment lawyer immediately.",
            "F": "Walk away or fully redraft. A perpetual rights grab without reversion is non-negotiable.",
        }

        await self.log_audit(
            "contract_shield", "contracts", None,
            {"contract_type": contract_type, "grade": grade, "flags": flag_count,
             "method": analysis_method},
        )

        return AgentResult(
            success=True,
            task_id=task.task_id,
            agent_id=self.agent_id,
            result={
                "grade": grade,
                "flags": flags,
                "flag_count": flag_count,
                "summary": grade_summaries[grade],
                "recommendation": recommendations[grade],
                "contract_type": contract_type,
                "analysis_method": analysis_method,
                "hero_skill": "contract_shield",
            },
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
        territory: str = "worldwide",
        governing_law: str = "california_us",
    ) -> str:
        producer_clause = ""
        if producer_name and producer_points:
            producer_clause = f"\nProducer ({producer_name}) receives {producer_points} points from ECHO share only.\n"

        advance_clause = (
            f"\nAdvance: ${advance_amount:,.2f} (recoupable against recording costs only).\n"
            if advance_amount else ""
        )

        governing_clause = GOVERNING_LAW_CLAUSES.get(governing_law, GOVERNING_LAW_CLAUSES["california_us"])

        territory_lower = territory.lower()
        needs_gdpr = any(t in territory_lower for t in ["eu", "eea", "uk", "europe", "worldwide"])

        gdpr_section = ""
        if needs_gdpr:
            gdpr_section = """
9. GDPR DATA PROCESSING ADDENDUM
The parties agree to comply with GDPR (EU) 2016/679 and UK GDPR where applicable.
ECHO acts as data controller for artist account data.
Artist consents to processing for contract administration purposes.
EU/EEA consumers have a 14-day right of withdrawal for digital services under
EU Consumer Rights Directive (2011/83/EU), waived upon commencement of service delivery.
"""

        return f"""ECHO RECORDING AGREEMENT — {deal_type.upper()}
TEMPLATE ONLY — Not legal advice. Review with qualified counsel in each jurisdiction.

Artist: {artist_name}
Song: {song_title}
Date: {date_str}
Territory: {territory}
Governing Law: {governing_law.replace('_', ' ').title()}

1. GRANT OF RIGHTS
Artist grants ECHO exclusive rights to the master recording of "{song_title}"
for the term of this agreement in the territory of: {territory}.
Copyright protections apply under the Berne Convention (1886, as amended) across all 181 signatory nations.

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
20% goes to Artist. Artist must retain minimum 30 master points at all times.
ECHO Points are NOT securities — they represent contractual royalty participation rights only.

7. NO LONG-TERM COMMITMENT
This agreement covers only "{song_title}". No obligation for future projects.

8. GOVERNING LAW AND DISPUTE RESOLUTION
{governing_clause}
{gdpr_section}
10. SANCTIONS COMPLIANCE
Both parties warrant they are not subject to OFAC, EU, UK, or UN sanctions programs.

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
        territory: str = "worldwide",
        governing_law: str = "california_us",
    ) -> str:
        governing_clause = GOVERNING_LAW_CLAUSES.get(governing_law, GOVERNING_LAW_CLAUSES["california_us"])

        return f"""ECHO PRODUCER AGREEMENT
TEMPLATE ONLY — Not legal advice. Review with qualified counsel in each jurisdiction.

Producer: {producer_name}
Artist: {artist_name}
Song: {song_title}
Date: {date_str}
Territory: {territory}

1. BEAT LICENSE
Producer grants ECHO and Artist an exclusive license to use the instrumental in "{song_title}".
Territory: {territory}. Protected under Berne Convention (1886, as amended).

2. PRODUCER POINTS
Producer receives {producer_points} master points for "{song_title}".
These points are deducted from ECHO's label share — NOT from Artist's share.
Each point = 1% of master recording revenue. Points are NOT securities.

3. CREDIT
Producer must receive "Produced by {producer_name}" credit on all official releases.

4. PUBLISHING
Producer retains 50% of publishing (composition) for the instrumental.
Artist retains 50% of publishing (lyrics/melody contributions).

5. PAYMENT
Beat fee (if applicable): As agreed separately.
Ongoing: Producer points per Section 2.

6. GOVERNING LAW AND DISPUTE RESOLUTION
{governing_clause}

___________________________          ___________________________
Producer Signature / Date            ECHO Representative / Date
"""

    def _render_publishing_admin_agreement(
        self,
        artist_name: str,
        date_str: str,
        territory: str = "worldwide",
        governing_law: str = "california_us",
    ) -> str:
        governing_clause = GOVERNING_LAW_CLAUSES.get(governing_law, GOVERNING_LAW_CLAUSES["california_us"])

        return f"""ECHO PUBLISHING ADMINISTRATION AGREEMENT
TEMPLATE ONLY — Not legal advice. Review with qualified counsel in each jurisdiction.

Artist/Publisher: {artist_name}
Date: {date_str}
Territory: {territory}

1. ADMINISTRATION
Artist appoints ECHO as non-exclusive publishing administrator for a 10% admin fee.
Artist retains 100% ownership of all compositions at all times.

2. SERVICES
ECHO will:
- Register compositions with ASCAP, BMI, SESAC, MLC, PRS for Music, GEMA, SACEM,
  JASRAC, SOCAN, APRA AMCOS, and all applicable societies in: {territory}
- Collect mechanical, performance, and sync royalties worldwide
- File claims on Content ID and neighboring rights platforms
- Register with CISAC/WIPO where applicable

3. TERM
2 years from execution date. Renewable with mutual consent.

4. ACCOUNTING
Quarterly statements and payments. 45-day payment window after quarter close.

5. TERMINATION
Either party may terminate with 60 days written notice.
ECHO retains right to collect royalties accrued during term for 12 months post-termination.

6. GOVERNING LAW AND DISPUTE RESOLUTION
{governing_clause}

7. BERNE CONVENTION
Copyright protections under Berne Convention (1886, as amended) apply across all 181 signatory nations.

___________________________          ___________________________
Artist Signature / Date              ECHO Representative / Date
"""

    def _render_tos(self, context: str, territory: str = "worldwide") -> str:
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        territory_lower = territory.lower()
        is_eu = any(t in territory_lower for t in ["eu", "eea", "uk", "europe", "worldwide"])

        if context == "points_store":
            eu_section = ""
            if is_eu:
                eu_section = f"""
10. EU/UK CONSUMER RIGHTS
Right of Withdrawal: EU/EEA consumers have a 14-day right of withdrawal for digital services
under EU Consumer Rights Directive (2011/83/EU), waived upon service commencement.
GDPR Data Rights: EU/UK users have the right to access, portability, and erasure of personal data.
To exercise rights, contact: privacy@melodio.io
EU consumer protection laws apply regardless of the governing law clause.

11. VAT / GST
Digital services subject to VAT/GST per local regulations:
- EU: ~20% (standard rate; varies by member state)
- UK: 20%
- Australia: 10% (GST)
Prices shown ex-tax where required by local law. Tax calculated at checkout.

12. SANCTIONS SCREENING
ECHO complies with OFAC, EU, UK, and UN sanctions programs.
Access is restricted to users in sanctioned jurisdictions.
"""
            return f"""ECHO POINTS STORE — TERMS OF SERVICE (WORLDWIDE)
TEMPLATE ONLY — Not legal advice. Review with qualified counsel before publishing.

Last Updated: {date_str}

1. WHAT ARE ECHO POINTS?
ECHO Points represent a contractual right to receive a share of master recording royalties
for a specific track. Points are NOT securities, investments, or equity stakes.
Points do NOT represent ownership in ECHO or any artist entity.
All content protected under Berne Convention (1886, as amended) across 181 signatory nations.

2. PURCHASING POINTS
By purchasing ECHO Points, you ("Buyer") agree that:
- You are buying a contractual royalty participation right only
- Points are NOT an investment or security (under US, EU, and international law)
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

6. AGE VERIFICATION
Users must be 18 years of age or older globally.
EU/UK users under 18 require verifiable parental consent per GDPR Art. 8
and the UK Age Appropriate Design Code.

7. AML / KYC
ECHO applies AML/KYC procedures per FATF recommendations.
Identity verification is required for point purchases exceeding $500 USD or equivalent.
ECHO complies with OFAC, EU, UK, and UN sanctions programs.
Access restricted in sanctioned jurisdictions.

8. INTELLECTUAL PROPERTY
All content on the ECHO platform is protected under copyright law.
Copyright protections apply under the Berne Convention (1886, as amended)
across all 181 signatory nations.

9. GOVERNING LAW
California law governs this agreement. Disputes via binding arbitration (AAA rules).
EU/EEA consumers retain rights under mandatory local consumer protection laws
regardless of the governing law clause.
{eu_section}"""

        elif context == "artist_portal":
            return f"""ECHO ARTIST PORTAL — TERMS OF SERVICE (WORLDWIDE)
TEMPLATE ONLY — Not legal advice. Review with qualified counsel before publishing.

Last Updated: {date_str}

1. ARTIST ACCOUNT
By creating an ECHO artist account, you agree to these worldwide terms.
These terms are governed by California law, with local mandatory consumer protections preserved.

2. CONTENT OWNERSHIP
Artists retain full ownership of their music and compositions at all times.
ECHO receives limited administrative rights only as specified in individual agreements.
All content protected under Berne Convention (1886) across 181 signatory nations.

3. COPYRIGHT REGISTRATION
ECHO will assist with registration across all applicable PROs including:
ASCAP, BMI, SESAC, PRS for Music, GEMA, SACEM, JASRAC, SOCAN, APRA AMCOS, and others.
Registration with CISAC umbrella organisation covers cross-border collections.

4. GDPR / DATA PROTECTION
Data Controller: ECHO (Melodio Inc.)
Lawful Basis: Contract performance and legitimate interests.
Retention Period: Duration of artist relationship + 7 years for financial records.
Data Subject Rights: Access, portability, erasure — contact privacy@melodio.io
Transfers: Data may be transferred to US servers under Standard Contractual Clauses.

5. SANCTIONS COMPLIANCE
ECHO complies with OFAC, EU, UK, and UN sanctions programs.
Artists in sanctioned jurisdictions may not access the platform.

6. AML / KYC
Identity verification required for royalty payments.
W-9 required for US persons receiving royalties exceeding $600/year.
W-8BEN required for non-US persons receiving US-source royalties.

7. GOVERNING LAW
California. Disputes via binding arbitration (AAA rules).
EU/EEA artists retain rights under mandatory local consumer protection laws."""

        elif context == "platform":
            return f"""ECHO PLATFORM — TERMS OF SERVICE (WORLDWIDE)
TEMPLATE ONLY — Not legal advice. Review with qualified counsel before publishing.

Last Updated: {date_str}

1. PLATFORM SERVICES
ECHO provides an AI-powered music industry platform including distribution,
royalty management, and rights administration services.

2. DSA TRANSPARENCY (EU)
In compliance with EU Digital Services Act (DSA) 2022/2065:
- Advertising: All paid content is clearly labelled as advertising (DSA Art. 26).
- Recommender Systems: Content recommendations are based on streaming performance
  and user engagement (DSA Art. 27).
- Authority Contact: legal@melodio.io (DSA Art. 12 contact point).

3. COPYRIGHT & TAKEDOWNS
ECHO respects intellectual property rights under:
- US DMCA (17 U.S.C. § 512)
- EU DSA Art. 16 notice-and-action
- UK Online Safety Act 2023
- Australia Online Safety Act 2021
- Berne Convention (181 nations)
Report infringement: dmca@melodio.io

4. DATA PROTECTION (GDPR)
Data Controller: Melodio Inc.
Lawful Basis: Contract / legitimate interests / consent where required.
Retention: Account data retained for duration of service + 7 years.
Rights: Access, portability, erasure — contact privacy@melodio.io
International Transfers: SCCs in place for EU-US transfers.

5. SANCTIONS & COMPLIANCE
ECHO complies with OFAC, EU, UK, and UN sanctions programs.
AML/KYC applies per FATF recommendations.

6. CONSUMER RIGHTS (EU/UK)
EU/EEA consumers retain rights under mandatory local consumer protection laws.
VAT/GST applied per local regulations.

7. GOVERNING LAW
California. Disputes via binding arbitration (AAA rules)."""

        elif context == "eu_consumer":
            return f"""ECHO — EU CONSUMER TERMS (SUPPLEMENT)
TEMPLATE ONLY — Not legal advice. Review with qualified EU consumer law counsel.

Last Updated: {date_str}

These EU Consumer Terms supplement the ECHO Platform Terms and apply to consumers
in the EU, EEA, and UK.

1. RIGHT OF WITHDRAWAL
Under EU Consumer Rights Directive (2011/83/EU), you have 14 days to withdraw from
digital service contracts without giving a reason.
This right is waived once digital service delivery commences with your explicit consent.

2. GDPR DATA RIGHTS
You have the following rights under GDPR (EU) 2016/679 and UK GDPR:
- Right of Access (Art. 15)
- Right to Rectification (Art. 16)
- Right to Erasure / 'Right to be Forgotten' (Art. 17)
- Right to Data Portability (Art. 20)
- Right to Object (Art. 21)
Contact: privacy@melodio.io | Response within 30 days.

3. VAT
Digital services are subject to VAT at applicable local rates.
EU: Standard rate (approx. 20% in most member states; rates vary).
UK: 20%. All rates subject to change per local legislation.

4. AGE
EU/UK users under 18 require verifiable parental/guardian consent
(GDPR Art. 8, UK Age Appropriate Design Code).

5. MANDATORY LOCAL CONSUMER LAW
Regardless of the governing law clause, you retain all rights under mandatory
consumer protection laws in your country of residence.

6. DISPUTE RESOLUTION (EU)
EU consumers may access the European Online Dispute Resolution platform:
https://ec.europa.eu/consumers/odr/
"""

        else:
            return (
                f"[ECHO {context.upper()} TERMS OF SERVICE — WORLDWIDE DRAFT — Generated {date_str}]\n"
                "TEMPLATE ONLY — Not legal advice."
            )

    async def on_message(self, message: dict):
        topic = message.get("topic", "")
        if topic == "release.published":
            payload = message.get("payload", {})
            track_id = payload.get("track_id")
            release_id = payload.get("release_id")
            if track_id or release_id:
                logger.info(f"[Legal] Release published — queuing copyright registration for track {track_id}")
