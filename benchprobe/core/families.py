"""Exploit family abstraction and registry.

A ``Family`` is the static description of one exploit class: name, formal
definition, mitigation, default severity, and (most importantly) the
``detect`` callable that consumes ``HarnessArtifacts`` and returns a
``Verdict``.

The taxonomy is *closed for additions* within a single release — every
family must trace to a published source (see ``notes/research.md``). New
families enter via PR, never via runtime registration in audit code.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Severity, Verdict

Detector = Callable[[HarnessArtifacts], Verdict]


@dataclass(frozen=True)
class Family:
    """Static metadata for one exploit family.

    Fields:

    - ``name``: stable ID used in the leaderboard JSON. Never rename without
      a migration.
    - ``formal_definition``: one-paragraph definition. Surfaced in reports.
    - ``mitigation_class``: short label for how to fix it.
    - ``severity_default``: severity returned when the detector finds
      conclusive evidence and doesn't override.
    - ``detect``: the check itself.
    - ``reference_positive`` / ``reference_negative``: paths to checked-in
      fixtures that ``pytest`` exercises. Documented here so the audit
      report can link to "what a vulnerable benchmark looks like for this
      family" without external lookup.
    - ``citation``: published source. Required — no family ships without
      a citation.
    """

    name: str
    formal_definition: str
    mitigation_class: str
    severity_default: Severity
    detect: Detector
    citation: str
    reference_positive: Path | None = None
    reference_negative: Path | None = None
    experimental: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)


class FamilyRegistry:
    """Hardcoded registry for the v0.1 families.

    No runtime discovery, no entry points — adding a family means editing
    ``benchprobe.families`` and importing it here. This is intentional for
    a security-adjacent tool.
    """

    def __init__(self) -> None:
        self._families: dict[str, Family] = {}

    def register(self, family: Family) -> None:
        if family.name in self._families:
            raise ValueError(f"family already registered: {family.name}")
        self._families[family.name] = family

    def get(self, name: str) -> Family:
        return self._families[name]

    def all(self) -> tuple[Family, ...]:
        return tuple(self._families.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._families.keys())

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._families

    def __len__(self) -> int:
        return len(self._families)


family_registry = FamilyRegistry()
"""Module-level singleton — populated by ``benchprobe.families`` on import."""
