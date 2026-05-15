from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import VerdictKind
from benchprobe.families.wrapper_no_op import family


def test_positive_fixture_is_vulnerable(reference_positive_root: Path) -> None:
    root = reference_positive_root / "wrapper_no_op"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        evaluator_paths=(root / "evaluator" / "check.py",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.VULNERABLE


def test_negative_fixture_passes(reference_negative_root: Path) -> None:
    root = reference_negative_root / "wrapper_no_op"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        evaluator_paths=(root / "evaluator" / "check.py",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.PASS
