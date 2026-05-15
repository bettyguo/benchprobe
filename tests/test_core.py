"""Core-abstraction tests: Verdict, Family registry, LeaderboardStore."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from benchprobe.core.families import Family, FamilyRegistry
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.leaderboard import LeaderboardStore, entry_from_verdicts
from benchprobe.core.verdict import Evidence, Severity, Verdict, VerdictKind


def _stub_artifacts() -> HarnessArtifacts:
    return HarnessArtifacts(benchmark="x", version_sha="sha", root=Path("."))


def test_verdict_is_failing_only_on_vulnerable() -> None:
    common = dict(
        family="f",
        benchmark="b",
        severity=Severity.LOW,
        reason="r",
        remediation_hint="h",
        audited_at=datetime.now(UTC),
    )
    assert Verdict(**common, kind=VerdictKind.VULNERABLE).is_failing()
    assert not Verdict(**common, kind=VerdictKind.PASS).is_failing()
    assert not Verdict(**common, kind=VerdictKind.INCONCLUSIVE).is_failing()


def test_evidence_is_frozen() -> None:
    from pydantic import ValidationError

    e = Evidence(path="x", snippet="y")
    with pytest.raises(ValidationError):
        e.path = "z"  # type: ignore[misc]


def test_family_registry_rejects_duplicates() -> None:
    reg = FamilyRegistry()
    fam = Family(
        name="foo",
        formal_definition="d",
        mitigation_class="m",
        severity_default=Severity.LOW,
        detect=lambda a: Verdict(
            family="foo",
            benchmark=a.benchmark,
            kind=VerdictKind.PASS,
            severity=Severity.LOW,
            reason="ok",
            remediation_hint="",
        ),
        citation="src",
    )
    reg.register(fam)
    with pytest.raises(ValueError):
        reg.register(fam)


def test_every_shipped_family_has_a_citation() -> None:
    import benchprobe.families  # noqa: F401  - side-effect registration
    from benchprobe.core.families import family_registry

    for fam in family_registry.all():
        assert fam.citation, f"{fam.name} ships without a citation"
        assert fam.formal_definition, f"{fam.name} has no formal definition"
        assert fam.mitigation_class, f"{fam.name} has no mitigation class"


def test_leaderboard_upsert_detects_change(tmp_path: Path) -> None:
    store = LeaderboardStore()
    v_pass = Verdict(
        family="f",
        benchmark="b",
        kind=VerdictKind.PASS,
        severity=Severity.LOW,
        reason="ok",
        remediation_hint="",
    )
    v_vuln = Verdict(
        family="f",
        benchmark="b",
        kind=VerdictKind.VULNERABLE,
        severity=Severity.HIGH,
        reason="bad",
        remediation_hint="fix",
    )
    entry1 = entry_from_verdicts("b", "sha1", [v_pass])
    assert store.upsert(entry1) is True
    entry2 = entry_from_verdicts("b", "sha1", [v_pass])
    assert store.upsert(entry2) is False
    entry3 = entry_from_verdicts("b", "sha1", [v_vuln])
    assert store.upsert(entry3) is True
    path = tmp_path / "out.json"
    store.save(path)
    loaded = LeaderboardStore.load(path)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].family_verdicts["f"] is VerdictKind.VULNERABLE
