from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import VerdictKind
from benchprobe.families.gold_answer_leak import family


def _artifacts(root: Path, *, config_subdir: str) -> HarnessArtifacts:
    return HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        task_config_dir=root / config_subdir,
    )


def test_positive_fixture_detects_co_located_gold(reference_positive_root: Path) -> None:
    root = reference_positive_root / "gold_answer_leak"
    verdict = family.detect(_artifacts(root, config_subdir="configs"))
    assert verdict.kind is VerdictKind.VULNERABLE
    assert verdict.evidence


def test_negative_fixture_passes(reference_negative_root: Path) -> None:
    root = reference_negative_root / "gold_answer_leak"
    verdict = family.detect(_artifacts(root, config_subdir="configs"))
    assert verdict.kind is VerdictKind.PASS


def test_inconclusive_when_config_dir_missing(tmp_path: Path) -> None:
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=tmp_path,
        task_config_dir=tmp_path / "does_not_exist",
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.INCONCLUSIVE
