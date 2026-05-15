from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import VerdictKind
from benchprobe.families.result_pattern_match import family


def test_positive_fixture_detects_substring_and_eval(reference_positive_root: Path) -> None:
    root = reference_positive_root / "result_pattern_match"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        evaluator_paths=(root / "evaluator" / "score.py",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.VULNERABLE


def test_negative_fixture_passes(reference_negative_root: Path) -> None:
    root = reference_negative_root / "result_pattern_match"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        evaluator_paths=(root / "evaluator" / "score.py",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.PASS
