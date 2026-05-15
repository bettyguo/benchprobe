"""Adapter: LiveBench.

LiveBench rotates questions monthly and gates answer release, so the
``config_lookup`` family is partly mitigated by design. The concerns
that remain reachable: the coding subset uses test-based grading
(``assertion_rewrite`` adjacent) and the math subset uses
substring-match grading (``result_pattern_match``).
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class LiveBenchAdapter:
    name = "livebench"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder
        "0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d",
    )

    def latest_known_sha(self) -> str:
        return self.validated_shas[-1]

    def expose_artifacts(self, root: Path) -> HarnessArtifacts:
        root = Path(root)
        return HarnessArtifacts(
            benchmark=self.name,
            version_sha=self.latest_known_sha(),
            root=root,
            evaluator_paths=(
                root / "livebench" / "process_results.py",
                root / "livebench" / "coding" / "checker.py",
            ),
            task_config_dir=root / "livebench" / "data",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "submissions",),
            known_remote_answer_sources=(),
            notes=(
                "Monthly question rotation gates config_lookup. Coding tests "
                "and substring math grading remain in scope.",
            ),
        )
