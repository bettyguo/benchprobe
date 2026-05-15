from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import VerdictKind
from benchprobe.families.empty_response_acceptance import family


def test_positive_fixture_is_vulnerable(reference_positive_root: Path) -> None:
    root = reference_positive_root / "empty_response_acceptance"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        evaluator_paths=(root / "evaluator" / "validate.py",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.VULNERABLE


def test_negative_fixture_passes(reference_negative_root: Path) -> None:
    root = reference_negative_root / "empty_response_acceptance"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        evaluator_paths=(root / "evaluator" / "validate.py",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.PASS


def test_inconclusive_when_no_evaluator(tmp_path: Path) -> None:
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=tmp_path,
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.INCONCLUSIVE
