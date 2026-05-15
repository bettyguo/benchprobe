from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Severity, VerdictKind
from benchprobe.families.env_trojanization import family


def _artifacts_positive(root: Path) -> HarnessArtifacts:
    return HarnessArtifacts(
        benchmark="synthetic",
        version_sha="positive",
        root=root,
        evaluator_paths=(root / "evaluator" / "run_evaluation.py",),
        agent_writable_paths=(root / "evaluator",),
    )


def _artifacts_negative(root: Path) -> HarnessArtifacts:
    return HarnessArtifacts(
        benchmark="synthetic",
        version_sha="negative",
        root=root,
        evaluator_paths=(root / "evaluator" / "run_evaluation.py",),
        agent_writable_paths=(root / "agent_sandbox",),
    )


def test_family_metadata() -> None:
    assert family.name == "env_trojanization"
    assert family.severity_default is Severity.CRITICAL
    assert family.citation, "every family must carry a citation"
    assert family.formal_definition, "every family must have a formal definition"


def test_positive_fixture_is_vulnerable(reference_positive_root: Path) -> None:
    root = reference_positive_root / "env_trojanization"
    verdict = family.detect(_artifacts_positive(root))
    assert verdict.kind is VerdictKind.VULNERABLE
    assert verdict.severity is Severity.CRITICAL
    assert verdict.evidence, "vulnerable verdicts must surface evidence"
    assert verdict.remediation_hint


def test_negative_fixture_passes(reference_negative_root: Path) -> None:
    root = reference_negative_root / "env_trojanization"
    verdict = family.detect(_artifacts_negative(root))
    assert verdict.kind is VerdictKind.PASS


def test_inconclusive_when_no_evaluator_paths() -> None:
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=Path("."),
        evaluator_paths=(),
        agent_writable_paths=(Path("."),),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.INCONCLUSIVE


def test_shared_trust_boundary_note_flags_vulnerable() -> None:
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=Path("."),
        evaluator_paths=(Path("evaluator/run.py"),),
        agent_writable_paths=(Path("agent/"),),
        notes=("evaluator and agent share the same container and process",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.VULNERABLE
    assert verdict.severity is Severity.HIGH
