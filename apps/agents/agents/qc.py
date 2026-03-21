"""
QC Agent
Sits at every agent handoff — verifies deliverables meet standards
across audio, artwork, metadata, marketing, contracts, and financials.
Also acts as the system-wide guardrail enforcement layer — any agent can
submit its output for QC verification and receive a correction broadcast.
"""

import logging
import re
from datetime import datetime, timezone

from base_agent import BaseAgent, AgentTask, AgentResult
from guardrails import ConfidenceGate, GuardrailStatus
from memory_store import ErrorType

logger = logging.getLogger(__name__)

# Audio specs (Blueprint v18)
REQUIRED_LOUDNESS_LUFS = -14.0
MAX_TRUE_PEAK_DBTP = -1.0
REQUIRED_SAMPLE_RATE = 44100
REQUIRED_BIT_DEPTH = 24
MIN_ARTWORK_PX = 3000

# Budget auto-approve threshold (must match CEO policy)
BUDGET_AUTO_APPROVE_MAX = 200.0

# Prohibited investment language (securities compliance)
PROHIBITED_PATTERNS = [
    r"\binvest\b", r"\binvestment\b", r"\broi\b", r"\breturns\b",
    r"\bprofit sharing\b", r"\bequity\b", r"\bshares\b", r"\bdividend\b",
    r"\bsecurity\b", r"\bsecurities\b",
]

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_NOTE = "NOTE"

REQUIRED_CONTRACT_CLAUSES = [
    "reversion_clause", "split_percentages", "artist_name", "song_title",
]

LABEL_GENRES = {"r&b", "hip-hop", "pop", "electronic", "indie"}


def _issue(severity: str, message: str) -> dict:
    return {"severity": severity, "message": message}


class QCAgent(BaseAgent):
    agent_id = "qc"
    agent_name = "Quality Control Agent"
    subscriptions = ["release.mastered", "release.ready"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "check_audio": self._check_audio,
            "check_artwork": self._check_artwork,
            "check_metadata": self._check_metadata,
            "check_marketing": self._check_marketing,
            "check_contract": self._check_contract,
            "check_financial": self._check_financial,
            "check_point_language": self._check_point_language,
            "run_pre_release_gate": self._run_pre_release_gate,
            "verify_agent_output": self._verify_agent_output_task,
            # Legacy task types (keep for backwards compat)
            "quality_check": self._legacy_quality_check,
            "approve_release": self._legacy_approve_release,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    # ----------------------------------------------------------------
    # check_audio
    # ----------------------------------------------------------------

    async def _check_audio(self, task: AgentTask) -> dict:
        p = task.payload
        issues = []

        lufs = p.get("loudness_lufs")
        if lufs is None:
            issues.append(_issue(SEVERITY_WARNING, "LUFS measurement not provided"))
        elif lufs > REQUIRED_LOUDNESS_LUFS + 1.0:
            issues.append(_issue(SEVERITY_WARNING, f"LUFS too loud: {lufs} (target {REQUIRED_LOUDNESS_LUFS})"))
        elif lufs < REQUIRED_LOUDNESS_LUFS - 3.0:
            issues.append(_issue(SEVERITY_NOTE, f"LUFS below target: {lufs} (target {REQUIRED_LOUDNESS_LUFS})"))

        true_peak = p.get("true_peak_dbtp")
        if true_peak is not None and true_peak > MAX_TRUE_PEAK_DBTP:
            issues.append(_issue(SEVERITY_CRITICAL, f"True peak exceeds limit: {true_peak} dBTP (max {MAX_TRUE_PEAK_DBTP})"))

        if p.get("clipping", False):
            issues.append(_issue(SEVERITY_CRITICAL, "Clipping detected — master rejected"))

        sample_rate = p.get("sample_rate")
        if sample_rate and sample_rate != REQUIRED_SAMPLE_RATE:
            issues.append(_issue(SEVERITY_WARNING, f"Sample rate {sample_rate}Hz (required {REQUIRED_SAMPLE_RATE}Hz)"))

        bit_depth = p.get("bit_depth")
        if bit_depth and bit_depth < REQUIRED_BIT_DEPTH:
            issues.append(_issue(SEVERITY_WARNING, f"Bit depth {bit_depth}-bit (required {REQUIRED_BIT_DEPTH}-bit)"))

        fmt = (p.get("format") or "").upper()
        if fmt and fmt not in ("WAV", "AIFF", "FLAC"):
            issues.append(_issue(SEVERITY_WARNING, f"Non-standard format: {fmt} (expected WAV/AIFF/FLAC)"))

        criticals = [i for i in issues if i["severity"] == SEVERITY_CRITICAL]
        passed = len(criticals) == 0

        if criticals:
            await self.send_message("ceo", "qc_critical_alert", {
                "check": "audio",
                "track_id": p.get("track_id"),
                "issues": criticals,
            })

        return {
            "check": "audio",
            "track_id": p.get("track_id"),
            "passed": passed,
            "issues": issues,
            "specs": {
                "loudness_lufs": lufs,
                "true_peak_dbtp": true_peak,
                "sample_rate": sample_rate,
                "bit_depth": bit_depth,
                "format": fmt,
            },
        }

    # ----------------------------------------------------------------
    # check_artwork
    # ----------------------------------------------------------------

    async def _check_artwork(self, task: AgentTask) -> dict:
        p = task.payload
        issues = []

        width = p.get("width_px", 0)
        height = p.get("height_px", 0)
        if width < MIN_ARTWORK_PX or height < MIN_ARTWORK_PX:
            issues.append(_issue(SEVERITY_CRITICAL, f"Artwork too small: {width}x{height}px (min {MIN_ARTWORK_PX}x{MIN_ARTWORK_PX})"))

        if width != height:
            issues.append(_issue(SEVERITY_WARNING, f"Artwork not square: {width}x{height}px"))

        fmt = (p.get("format") or "").upper()
        if fmt and fmt not in ("JPEG", "JPG", "PNG"):
            issues.append(_issue(SEVERITY_WARNING, f"Non-standard artwork format: {fmt} (expected JPEG/PNG)"))

        # Check for prohibited content in artwork text
        artwork_text = p.get("text_content", "")
        prohibited_art = [r"https?://", r"@\w+", r"\$\d+", r"\d+%\s*off"]
        for pattern in prohibited_art:
            if re.search(pattern, artwork_text, re.IGNORECASE):
                issues.append(_issue(SEVERITY_CRITICAL, f"Prohibited content in artwork: matches '{pattern}'"))

        # Text readability at 300px
        if p.get("text_too_small_at_300px", False):
            issues.append(_issue(SEVERITY_WARNING, "Text not readable at 300px thumbnail size"))

        criticals = [i for i in issues if i["severity"] == SEVERITY_CRITICAL]
        passed = len(criticals) == 0

        return {
            "check": "artwork",
            "artwork_url": p.get("artwork_url"),
            "passed": passed,
            "issues": issues,
        }

    # ----------------------------------------------------------------
    # check_metadata
    # ----------------------------------------------------------------

    async def _check_metadata(self, task: AgentTask) -> dict:
        p = task.payload
        issues = []

        release_id = p.get("release_id") or task.release_id
        if release_id:
            release = await self.db_fetchrow("SELECT * FROM releases WHERE id = $1::uuid", release_id)
            if not release:
                return {"check": "metadata", "passed": False, "issues": [_issue(SEVERITY_CRITICAL, "Release not found")]}

            if not release.get("title"):
                issues.append(_issue(SEVERITY_CRITICAL, "Release title missing"))
            if not release.get("artist_id"):
                issues.append(_issue(SEVERITY_CRITICAL, "Artist not linked to release"))
            if not release.get("genre"):
                issues.append(_issue(SEVERITY_WARNING, "Genre not specified"))

            tracks = await self.db_fetch(
                "SELECT id, title, isrc FROM tracks WHERE release_id = $1::uuid", release_id
            )
            if not tracks:
                issues.append(_issue(SEVERITY_CRITICAL, "No tracks linked to release"))
            for t in tracks:
                if not t.get("isrc"):
                    issues.append(_issue(SEVERITY_CRITICAL, f"Track '{t.get('title', t['id'])}' missing ISRC code"))
                if not t.get("title"):
                    issues.append(_issue(SEVERITY_CRITICAL, f"Track {t['id']} has no title"))
        else:
            # Validate inline payload metadata
            if not p.get("title"):
                issues.append(_issue(SEVERITY_CRITICAL, "Title missing"))
            if not p.get("artist_name"):
                issues.append(_issue(SEVERITY_CRITICAL, "Artist name missing"))
            if not p.get("isrc"):
                issues.append(_issue(SEVERITY_CRITICAL, "ISRC code missing"))
            if not p.get("genre"):
                issues.append(_issue(SEVERITY_WARNING, "Genre not specified"))
            if not p.get("writer_credits"):
                issues.append(_issue(SEVERITY_WARNING, "No writer credits listed"))
            if not p.get("release_date"):
                issues.append(_issue(SEVERITY_NOTE, "Release date not set"))

        criticals = [i for i in issues if i["severity"] == SEVERITY_CRITICAL]
        passed = len(criticals) == 0

        return {
            "check": "metadata",
            "release_id": release_id,
            "passed": passed,
            "issues": issues,
        }

    # ----------------------------------------------------------------
    # check_marketing
    # ----------------------------------------------------------------

    async def _check_marketing(self, task: AgentTask) -> dict:
        p = task.payload
        issues = []

        budget = float(p.get("budget", 0))
        if budget > BUDGET_AUTO_APPROVE_MAX and not p.get("ceo_approved", False):
            issues.append(_issue(SEVERITY_CRITICAL, f"Budget ${budget:.2f} exceeds auto-approve limit (${BUDGET_AUTO_APPROVE_MAX}) — requires CEO approval"))

        copy_text = p.get("copy_text", "")
        prohibited_lang = self._scan_prohibited_language(copy_text)
        for match in prohibited_lang:
            issues.append(_issue(SEVERITY_CRITICAL, f"Prohibited language in copy: '{match}'"))

        links = p.get("links", [])
        broken_links = p.get("broken_links", [])
        if broken_links:
            for link in broken_links:
                issues.append(_issue(SEVERITY_CRITICAL, f"Broken link detected: {link}"))

        if not p.get("target_audience"):
            issues.append(_issue(SEVERITY_NOTE, "Target audience not specified"))

        criticals = [i for i in issues if i["severity"] == SEVERITY_CRITICAL]
        passed = len(criticals) == 0

        return {
            "check": "marketing",
            "campaign_id": p.get("campaign_id"),
            "passed": passed,
            "issues": issues,
            "budget": budget,
            "links_checked": len(links),
        }

    # ----------------------------------------------------------------
    # check_contract
    # ----------------------------------------------------------------

    async def _check_contract(self, task: AgentTask) -> dict:
        p = task.payload
        issues = []

        contract_id = p.get("contract_id")
        clauses_present = p.get("clauses_present", [])
        content = p.get("content", "")

        for clause in REQUIRED_CONTRACT_CLAUSES:
            if clause not in clauses_present and clause not in content.lower():
                severity = SEVERITY_CRITICAL if clause in ("reversion_clause", "split_percentages") else SEVERITY_WARNING
                issues.append(_issue(severity, f"Required clause missing: {clause.replace('_', ' ')}"))

        if not p.get("artist_name") and "artist_name" not in (p.get("clauses_present") or []):
            issues.append(_issue(SEVERITY_CRITICAL, "Artist name not found in contract"))

        if not p.get("song_title") and "song_title" not in (p.get("clauses_present") or []):
            issues.append(_issue(SEVERITY_CRITICAL, "Song title not found in contract"))

        # Check for prohibited investment language in contracts too
        prohibited_lang = self._scan_prohibited_language(content)
        for match in prohibited_lang:
            issues.append(_issue(SEVERITY_CRITICAL, f"Prohibited investment language in contract: '{match}'"))

        criticals = [i for i in issues if i["severity"] == SEVERITY_CRITICAL]
        passed = len(criticals) == 0

        if criticals:
            await self.send_message("ceo", "qc_critical_alert", {
                "check": "contract",
                "contract_id": contract_id,
                "issues": criticals,
            })

        return {
            "check": "contract",
            "contract_id": contract_id,
            "passed": passed,
            "issues": issues,
        }

    # ----------------------------------------------------------------
    # check_financial
    # ----------------------------------------------------------------

    async def _check_financial(self, task: AgentTask) -> dict:
        p = task.payload
        issues = []

        # Verify royalty calculation matches to the penny
        stated_total = p.get("stated_total")
        line_items = p.get("line_items", [])

        if stated_total is not None and line_items:
            calculated_total = sum(float(item.get("amount", 0)) for item in line_items)
            diff = abs(round(float(stated_total), 2) - round(calculated_total, 2))
            if diff > 0.00:
                issues.append(_issue(SEVERITY_CRITICAL, f"Royalty calculation mismatch: stated ${stated_total:.2f} vs calculated ${calculated_total:.2f} (diff ${diff:.2f})"))

        split_pcts = p.get("split_percentages", {})
        if split_pcts:
            total_pct = sum(float(v) for v in split_pcts.values())
            if abs(total_pct - 100.0) > 0.01:
                issues.append(_issue(SEVERITY_CRITICAL, f"Split percentages don't sum to 100%: {total_pct:.2f}%"))

        if p.get("negative_amounts", False):
            issues.append(_issue(SEVERITY_CRITICAL, "Negative payment amounts detected"))

        criticals = [i for i in issues if i["severity"] == SEVERITY_CRITICAL]
        passed = len(criticals) == 0

        return {
            "check": "financial",
            "royalty_id": p.get("royalty_id"),
            "passed": passed,
            "issues": issues,
            "stated_total": stated_total,
            "line_items_count": len(line_items),
        }

    # ----------------------------------------------------------------
    # check_point_language
    # ----------------------------------------------------------------

    async def _check_point_language(self, task: AgentTask) -> dict:
        text = task.payload.get("text", "")
        context = task.payload.get("context", "unknown")

        matches = self._scan_prohibited_language(text)
        passed = len(matches) == 0

        issues = [_issue(SEVERITY_CRITICAL, f"Prohibited term '{m}' in {context}") for m in matches]

        if not passed:
            await self.send_message("ceo", "qc_critical_alert", {
                "check": "point_language",
                "context": context,
                "matches": matches,
            })
            logger.warning(f"[QC] Prohibited investment language found in {context}: {matches}")

        return {
            "check": "point_language",
            "context": context,
            "passed": passed,
            "prohibited_matches": matches,
            "issues": issues,
        }

    # ----------------------------------------------------------------
    # run_pre_release_gate
    # ----------------------------------------------------------------

    async def _run_pre_release_gate(self, task: AgentTask) -> dict:
        p = task.payload
        release_id = p.get("release_id") or task.release_id

        gates = {}
        blockers = []
        warnings = []

        # --- Audio gate ---
        audio_result = await self._check_audio(AgentTask(
            task_id=f"{task.task_id}_audio",
            task_type="check_audio",
            payload=p.get("audio", {}),
        ))
        gates["audio"] = {
            "passed": audio_result["passed"],
            "issues": [i["message"] for i in audio_result["issues"]],
        }

        # --- Artwork gate ---
        artwork_result = await self._check_artwork(AgentTask(
            task_id=f"{task.task_id}_artwork",
            task_type="check_artwork",
            payload=p.get("artwork", {}),
        ))
        gates["artwork"] = {
            "passed": artwork_result["passed"],
            "issues": [i["message"] for i in artwork_result["issues"]],
        }

        # --- Metadata gate ---
        metadata_result = await self._check_metadata(AgentTask(
            task_id=f"{task.task_id}_metadata",
            task_type="check_metadata",
            payload={**p.get("metadata", {}), "release_id": release_id},
            release_id=release_id,
        ))
        gates["metadata"] = {
            "passed": metadata_result["passed"],
            "issues": [i["message"] for i in metadata_result["issues"]],
        }

        # --- Marketing gate (if campaign provided) ---
        if p.get("marketing"):
            marketing_result = await self._check_marketing(AgentTask(
                task_id=f"{task.task_id}_marketing",
                task_type="check_marketing",
                payload=p.get("marketing", {}),
            ))
            gates["marketing"] = {
                "passed": marketing_result["passed"],
                "issues": [i["message"] for i in marketing_result["issues"]],
            }
        else:
            gates["marketing"] = {"passed": True, "issues": [], "skipped": True}

        # Aggregate blockers and warnings across all gates
        for gate_name, gate in gates.items():
            if not gate.get("skipped"):
                # Re-check severity from source results
                pass

        # Gather all critical issues as blockers
        for result in [audio_result, artwork_result, metadata_result]:
            for issue in result["issues"]:
                if issue["severity"] == SEVERITY_CRITICAL:
                    blockers.append(issue["message"])
                elif issue["severity"] == SEVERITY_WARNING:
                    warnings.append(issue["message"])

        if p.get("marketing"):
            for issue in marketing_result["issues"]:
                if issue["severity"] == SEVERITY_CRITICAL:
                    blockers.append(issue["message"])
                elif issue["severity"] == SEVERITY_WARNING:
                    warnings.append(issue["message"])

        all_gates_passed = all(g["passed"] for g in gates.values())
        ready_to_release = all_gates_passed and len(blockers) == 0

        # Update release status in DB if we have a release_id
        if release_id:
            new_status = "qc_approved" if ready_to_release else "qc_failed"
            await self.db_execute(
                "UPDATE releases SET status = $2, updated_at = NOW() WHERE id = $1::uuid",
                release_id, new_status,
            )
            await self.log_audit("pre_release_gate", "releases", release_id, {
                "passed": ready_to_release,
                "blockers": blockers,
            })

        if ready_to_release:
            if release_id:
                await self.send_message("distribution", "submit_to_dsps", {"release_id": release_id})
            logger.info(f"[QC] Pre-release gate PASSED for release {release_id}")
        else:
            logger.warning(f"[QC] Pre-release gate FAILED: {blockers}")
            if blockers and release_id:
                await self.send_message("ceo", "qc_gate_failed", {
                    "release_id": release_id,
                    "blockers": blockers,
                })

        return {
            "passed": all_gates_passed,
            "gates": gates,
            "blockers": blockers,
            "warnings": warnings,
            "ready_to_release": ready_to_release,
            "release_id": release_id,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _scan_prohibited_language(self, text: str) -> list[str]:
        """Return list of prohibited terms found in text."""
        found = []
        for pattern in PROHIBITED_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found.append(match.group(0).lower())
        return list(set(found))

    # ----------------------------------------------------------------
    # Legacy task handlers (backwards compat)
    # ----------------------------------------------------------------

    async def _legacy_quality_check(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        return await self._run_pre_release_gate(AgentTask(
            task_id=task.task_id,
            task_type="run_pre_release_gate",
            payload={"release_id": release_id},
            release_id=release_id,
        ))

    async def _legacy_approve_release(self, task: AgentTask) -> dict:
        release_id = task.payload.get("release_id") or task.release_id
        await self.db_execute(
            "UPDATE releases SET status = 'qc_approved', updated_at = NOW() WHERE id = $1::uuid",
            release_id,
        )
        await self.send_message("distribution", "submit_to_dsps", {"release_id": release_id})
        await self.log_audit("approve_release", "releases", release_id)
        return {"release_id": release_id, "status": "qc_approved"}

    # ----------------------------------------------------------------
    # Cross-agent output verification
    # ----------------------------------------------------------------

    async def verify_agent_output(
        self, agent_id: str, task_type: str, output: dict
    ) -> dict:
        """
        Run ConfidenceGate on any agent's output.

        - Logs failures to memory store with HALLUCINATION or SCHEMA_MISMATCH.
        - Broadcasts a correction back to the originating agent via bus.
        - Returns a dict with {passed, confidence, reason, correction}.
        """
        gate = ConfidenceGate()
        gate_result = gate.check(output, agent_id, task_type)

        if gate_result.passed:
            return {
                "passed": True,
                "agent_id": agent_id,
                "task_type": task_type,
                "confidence": gate_result.confidence,
                "reason": gate_result.reason,
            }

        # Classify the error type
        if gate_result.confidence == 0.0:
            error_type = ErrorType.SCHEMA_MISMATCH
        else:
            error_type = ErrorType.HALLUCINATION

        correction = (
            f"QC rejected {agent_id}/{task_type} output: {gate_result.reason}. "
            f"Confidence was {gate_result.confidence:.2f}. "
            f"Do not emit low-confidence results — return not-found instead."
        )

        logger.warning(
            f"[QC] verify_agent_output FAILED — {agent_id}/{task_type}: {gate_result.reason}"
        )

        if self._memory_store:
            await self._memory_store.log_failure(
                agent_id=agent_id,
                task_type=task_type,
                input_data={},
                bad_output=output,
                error_type=error_type,
                correction=correction,
                confidence_score=gate_result.confidence,
            )

        # Broadcast correction back to the originating agent
        await self.broadcast(
            f"agent.{agent_id}",
            {
                "topic": "qc.correction",
                "from_agent": self.agent_id,
                "to_agent": agent_id,
                "task_type": task_type,
                "error_type": error_type.value,
                "correction": correction,
                "safe_response": gate_result.safe_response,
            },
        )

        return {
            "passed": False,
            "agent_id": agent_id,
            "task_type": task_type,
            "confidence": gate_result.confidence,
            "reason": gate_result.reason,
            "error_type": error_type.value,
            "correction": correction,
        }

    async def _verify_agent_output_task(self, task: AgentTask) -> dict:
        """Task handler wrapper for verify_agent_output."""
        p = task.payload
        source_agent = p.get("agent_id", "unknown")
        source_task_type = p.get("task_type", "unknown")
        output = p.get("output", {})
        return await self.verify_agent_output(source_agent, source_task_type, output)

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[QC] Online — guarding all release gates")
