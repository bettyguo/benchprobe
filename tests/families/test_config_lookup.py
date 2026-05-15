from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import VerdictKind
from benchprobe.families.config_lookup import family


def test_positive_fixture_is_vulnerable(reference_positive_root: Path) -> None:
    root = reference_positive_root / "config_lookup"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        task_config_dir=root / "configs",
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.VULNERABLE


def test_negative_fixture_passes(reference_negative_root: Path) -> None:
    root = reference_negative_root / "config_lookup"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        task_config_dir=root / "configs",
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.PASS


def test_known_remote_sources_with_no_filter_flag_vulnerable(tmp_path: Path) -> None:
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=tmp_path,
        known_remote_answer_sources=("https://huggingface.co/datasets/foo",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.VULNERABLE


def test_known_remote_sources_with_filter_pass(tmp_path: Path) -> None:
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=tmp_path,
        known_remote_answer_sources=("https://huggingface.co/datasets/foo",),
        notes=("agent runs offline; egress allowlist excludes huggingface.co",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.PASS
