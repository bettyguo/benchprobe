"""Adapter: GAIA (general AI assistants benchmark)."""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class GaiaAdapter:
    name = "gaia"
    validated_shas: tuple[str, ...] = (
        "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2",
    )

    def latest_known_sha(self) -> str:
        return self.validated_shas[-1]

    def expose_artifacts(self, root: Path) -> HarnessArtifacts:
        root = Path(root)
        return HarnessArtifacts(
            benchmark=self.name,
            version_sha=self.latest_known_sha(),
            root=root,
            evaluator_paths=(root / "scorer.py", root / "normalize.py"),
            task_config_dir=root / "data",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "submissions",),
            known_remote_answer_sources=(
                "https://huggingface.co/datasets/gaia-benchmark/GAIA",
            ),
            notes=(
                "GAIA's validation answers are hosted on a public HuggingFace "
                "dataset. The agent's environment must not have egress to "
                "huggingface.co during task execution, or it can fetch the "
                "answer set and look up the expected reply before submitting.",
                "normalize_str() in the scorer strips whitespace and "
                "punctuation, enabling loose-collision attacks on short "
                "answers.",
            ),
            metadata={},
        )
