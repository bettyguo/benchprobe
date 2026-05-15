from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import VerdictKind
from benchprobe.families.judge_prompt_injection import family


def test_positive_fixture_is_vulnerable(reference_positive_root: Path) -> None:
    root = reference_positive_root / "judge_prompt_injection"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        judge_prompt_paths=(root / "prompts" / "judge_prompt.txt",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.VULNERABLE


def test_negative_fixture_passes(reference_negative_root: Path) -> None:
    root = reference_negative_root / "judge_prompt_injection"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        judge_prompt_paths=(root / "prompts" / "judge_prompt.txt",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.PASS


def test_inconclusive_when_no_judge_prompt() -> None:
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=Path("."),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.INCONCLUSIVE
