"""Verdict types.

A ``Verdict`` is the result of running one exploit-family check against one
benchmark's exposed artifacts. Three outcomes are possible:

- ``PASS`` — the check ran and found no evidence of the exploit being possible.
- ``VULNERABLE`` — the check ran and found concrete evidence of the exploit.
- ``INCONCLUSIVE`` — the check could not run (artifact missing, adapter
  out-of-date, evaluator code unavailable). Treated as a soft "ask again later"
  rather than a pass.

Every verdict carries enough provenance for the leaderboard renderer to link
back to the exact evidence — see ``evidence`` and ``remediation_hint``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class VerdictKind(StrEnum):
    """The three possible outcomes of running a single family check."""

    PASS = "pass"
    VULNERABLE = "vulnerable"
    INCONCLUSIVE = "inconclusive"


class Severity(StrEnum):
    """How damaging the exploit is, given it is reachable.

    ``CRITICAL`` is reserved for exploits that yield a perfect score with
    near-zero work (e.g. SWE-bench conftest hookimpl). ``HIGH`` for exploits
    that yield a perfect score with modest setup. ``MEDIUM`` for exploits
    that bias scores but do not trivially saturate them. ``LOW`` for
    detection-only signals where exploitation is theoretical.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Evidence(BaseModel):
    """A pointer back to the specific artifact that triggered the verdict.

    ``path`` is the relative path inside the benchmark's exposed artifacts —
    e.g. ``"evaluators/judge_prompt.txt"`` or ``"config_files/12.json"``.
    ``snippet`` is a short excerpt; we cap it at ~400 chars to keep reports
    legible. ``line`` is optional; set it when the evidence is one specific
    line of a file.
    """

    model_config = {"frozen": True}

    path: str
    snippet: str = Field(default="", max_length=400)
    line: int | None = None


class Verdict(BaseModel):
    """Result of a single family check against a single benchmark."""

    model_config = {"frozen": True}

    family: str
    benchmark: str
    kind: VerdictKind
    severity: Severity
    reason: str
    remediation_hint: str
    evidence: tuple[Evidence, ...] = ()
    audited_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    auditor_version: str = "0.1.0"

    def is_failing(self) -> bool:
        """A verdict is failing iff the benchmark is provably vulnerable."""
        return self.kind is VerdictKind.VULNERABLE
