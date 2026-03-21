"""
Agent Guardrails

Provides confidence gates, hallucination detection, and scope guards
for all ECHO agents. Prevents fabricated data from leaving any agent.
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

CONFIDENCE_THRESHOLD = float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", "0.7"))

# Real external ID fields that prove an artist record is genuine
REAL_ID_FIELDS = [
    "spotify_id", "musicbrainz_id", "chartmetric_id",
    "apple_music_id", "isrc", "discogs_id",
]

# Terms that indicate a non-music entity when found in an AR payload
NON_MUSIC_DOMAINS = [
    "politician", "athlete", "actor", "actress", "filmmaker", "chef",
    "ceo", "executive", "scientist", "author", "writer", "journalist",
    "investor", "banker", "doctor", "lawyer", "architect", "engineer",
]

# Suspicious placeholder patterns that signal an invented value
_SUSPICIOUS_PATTERNS = [
    re.compile(r"^(unknown|n/a|not\s+found|none|null|tbd|placeholder|undefined)$", re.I),
    re.compile(r"example\.com", re.I),
    re.compile(r"lorem\s+ipsum", re.I),
    re.compile(r"fake_?id_?\d+", re.I),
    re.compile(r"test_?artist", re.I),
    re.compile(r"artist_\d+", re.I),
]


class GuardrailStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class GuardrailResult:
    status: GuardrailStatus
    confidence: float
    reason: str
    safe_response: Optional[dict] = field(default=None)

    @property
    def passed(self) -> bool:
        return self.status == GuardrailStatus.PASS


class HallucinationDetector:
    """
    Checks whether key fields in an output appear invented.
    Returns a confidence score 0.0–1.0.

    1.0 = definitely real  |  0.0 = definitely hallucinated
    """

    def check(self, output: dict, task_type: str) -> float:
        if not output:
            return 0.0

        # Agent already self-reported "not found" — that's honest, not hallucinated
        if output.get("found") is False:
            return 1.0

        score = 0.5  # neutral starting point

        # AR / search tasks: a real external ID is strong evidence of reality
        if task_type in ("ar_search", "artist_search", "review_artist", "score_submission"):
            has_real_id = any(output.get(f) for f in REAL_ID_FIELDS)
            if has_real_id:
                score += 0.4
            else:
                score -= 0.2  # suspicious but not conclusive

        # Scan all string values for placeholder patterns
        text_to_scan = " ".join(
            str(v) for v in output.values() if isinstance(v, (str, int, float))
        )
        for pattern in _SUSPICIOUS_PATTERNS:
            if pattern.search(text_to_scan):
                score -= 0.3
                break

        # Real artist: name + at least one external URL
        if output.get("name") and any(
            output.get(k)
            for k in ("spotify_url", "spotify_id", "website", "instagram_url", "soundcloud_url")
        ):
            score += 0.1

        # Structured numeric data (streaming counts, scores) suggests real data
        numeric_fields = sum(
            1 for v in output.values() if isinstance(v, (int, float)) and v > 0
        )
        if numeric_fields >= 2:
            score += 0.1

        return max(0.0, min(1.0, round(score, 3)))


class ScopeGuard:
    """
    Prevents agents from processing out-of-scope requests.
    Currently enforces that AR agent only processes music-related entities.
    """

    # Agents that have scope restrictions
    _SCOPED_AGENTS = {"ar"}

    def check(self, agent_id: str, task_type: str, payload: dict) -> GuardrailResult:
        if agent_id not in self._SCOPED_AGENTS:
            return GuardrailResult(
                status=GuardrailStatus.PASS,
                confidence=1.0,
                reason="No scope restriction for this agent",
            )

        # Flatten all string values from the payload for scanning
        text = " ".join(
            str(v) for v in payload.values() if isinstance(v, str)
        ).lower()

        for term in NON_MUSIC_DOMAINS:
            if re.search(rf"\b{re.escape(term)}\b", text):
                return GuardrailResult(
                    status=GuardrailStatus.FAIL,
                    confidence=1.0,
                    reason=(
                        f"Out of scope: entity appears to be a '{term}', not a music artist"
                    ),
                    safe_response={
                        "found": False,
                        "reason": (
                            f"This request is out of scope for the {agent_id.upper()} agent. "
                            f"'{term}' is not a music industry entity."
                        ),
                        "scope": "music_entities_only",
                        "searched": [],
                    },
                )

        return GuardrailResult(
            status=GuardrailStatus.PASS,
            confidence=1.0,
            reason="Payload is in scope for this agent",
        )


class ConfidenceGate:
    """
    Validates any agent output before it leaves the agent.

    Runs required-field checks and hallucination detection.
    Returns a GuardrailResult with pass/fail and confidence score.
    """

    # Required fields per task type — ALL must be present and non-empty
    _REQUIRED_FIELDS: dict[str, list[str]] = {
        "score_submission": ["submission_id", "score"],
        "sign_artist": ["artist_id", "status"],
    }

    def __init__(self, threshold: float = CONFIDENCE_THRESHOLD):
        self.threshold = threshold
        self._detector = HallucinationDetector()

    def check(self, output: dict, agent_id: str, task_type: str) -> GuardrailResult:
        """
        Full guardrail check on an output dict.

        Returns GuardrailResult — always prefer not-found over fabrication.
        """
        # 1. Required fields
        missing = self._check_required_fields(output, task_type)
        if missing:
            return GuardrailResult(
                status=GuardrailStatus.FAIL,
                confidence=0.0,
                reason=f"Required fields missing for '{task_type}': {missing}",
                safe_response=self._not_found_response(
                    task_type, f"Missing required fields: {missing}"
                ),
            )

        # 2. Hallucination detection
        confidence = self._detector.check(output, task_type)
        if confidence < self.threshold:
            return GuardrailResult(
                status=GuardrailStatus.FAIL,
                confidence=confidence,
                reason=(
                    f"Confidence {confidence:.2f} is below threshold {self.threshold} "
                    f"for task '{task_type}' — refusing to emit low-confidence result"
                ),
                safe_response=self._not_found_response(
                    task_type, f"Low confidence result ({confidence:.2f})"
                ),
            )

        return GuardrailResult(
            status=GuardrailStatus.PASS,
            confidence=confidence,
            reason="Output passed all guardrail checks",
        )

    def _check_required_fields(self, output: dict, task_type: str) -> list[str]:
        required = self._REQUIRED_FIELDS.get(task_type, [])
        return [f for f in required if not output.get(f)]

    @staticmethod
    def _not_found_response(task_type: str, reason: str) -> dict:
        return {
            "found": False,
            "reason": reason,
            "task_type": task_type,
            "searched": [],
        }
