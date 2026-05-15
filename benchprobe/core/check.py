"""Helpers for writing family ``detect`` callables.

The base class is deliberately thin — ``Family.detect`` is just
``HarnessArtifacts -> Verdict`` and most families use module-level functions.
``Check`` exists for the cases where a detector needs to carry tuning state
(e.g. ``EnvTrojanCheck(extra_evaluator_paths=...)``) without leaking a
closure into the registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Evidence, Severity, Verdict, VerdictKind


class Check(ABC):
    """Callable adapter — instances of ``Check`` can be passed as ``detect``."""

    name: str
    severity_default: Severity

    @abstractmethod
    def __call__(self, artifacts: HarnessArtifacts) -> Verdict:  # pragma: no cover - interface
        raise NotImplementedError

    # --- shared helpers ----------------------------------------------------

    def inconclusive(
        self,
        artifacts: HarnessArtifacts,
        reason: str,
        remediation_hint: str = "",
    ) -> Verdict:
        return Verdict(
            family=self.name,
            benchmark=artifacts.benchmark,
            kind=VerdictKind.INCONCLUSIVE,
            severity=Severity.LOW,
            reason=reason,
            remediation_hint=remediation_hint
            or "Provide the missing artifact in the benchmark adapter.",
        )

    def passing(
        self,
        artifacts: HarnessArtifacts,
        reason: str,
        remediation_hint: str = "",
    ) -> Verdict:
        return Verdict(
            family=self.name,
            benchmark=artifacts.benchmark,
            kind=VerdictKind.PASS,
            severity=Severity.LOW,
            reason=reason,
            remediation_hint=remediation_hint
            or "No remediation required — this family is not reachable here.",
        )

    def vulnerable(
        self,
        artifacts: HarnessArtifacts,
        reason: str,
        remediation_hint: str,
        evidence: tuple[Evidence, ...] = (),
        severity: Severity | None = None,
    ) -> Verdict:
        return Verdict(
            family=self.name,
            benchmark=artifacts.benchmark,
            kind=VerdictKind.VULNERABLE,
            severity=severity or self.severity_default,
            reason=reason,
            remediation_hint=remediation_hint,
            evidence=evidence,
        )


def read_text_safely(path: Path, max_bytes: int = 200_000) -> str | None:
    """Read up to ``max_bytes`` of UTF-8 text. Return ``None`` if unreadable.

    We never raise on read errors during an audit — a missing file is
    semantically ``INCONCLUSIVE``, not a crash. ``max_bytes`` caps memory
    so an adapter that points at a 5 GB SQLite file doesn't OOM the audit.
    """
    try:
        with path.open("rb") as fh:
            raw = fh.read(max_bytes)
    except OSError:
        return None
    try:
        return raw.decode("utf-8", errors="replace")
    except UnicodeDecodeError:  # pragma: no cover - errors="replace" suppresses this
        return None


def snippet_around(text: str, idx: int, width: int = 120) -> str:
    """Extract a short snippet around character index ``idx`` for evidence."""
    start = max(0, idx - width // 2)
    end = min(len(text), idx + width // 2)
    return text[start:end].replace("\n", " ⏎ ").strip()
