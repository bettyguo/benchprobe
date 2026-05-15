from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import VerdictKind
from benchprobe.families.assertion_rewrite import family


def test_positive_fixture_detects_hookimpl(reference_positive_root: Path) -> None:
    root = reference_positive_root / "assertion_rewrite"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        evaluator_paths=(root / "evaluator" / "run_tests.py",),
        agent_writable_paths=(root / "agent_tree",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.VULNERABLE
    assert any("conftest" in e.snippet or "hookimpl" in e.snippet.lower() for e in verdict.evidence)


def test_negative_fixture_with_confcutdir_passes(reference_negative_root: Path) -> None:
    root = reference_negative_root / "assertion_rewrite"
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=root,
        evaluator_paths=(root / "evaluator" / "run_tests.py",),
        agent_writable_paths=(root / "agent_sandbox",),
        notes=("evaluator runs pytest with --no-conftest and confcutdir=evaluator",),
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.PASS


def test_inconclusive_when_no_paths(tmp_path: Path) -> None:
    artifacts = HarnessArtifacts(
        benchmark="synthetic",
        version_sha="x",
        root=tmp_path,
    )
    verdict = family.detect(artifacts)
    assert verdict.kind is VerdictKind.INCONCLUSIVE
