"""Adapter: AGIEval.

``moogician/trustworthy-env`` lists an AGIEval exploit script. AGIEval
scores by extracting the agent's final answer from free-text, then
substring-matching against gold — the ``result_pattern_match`` family.
Like MMLU, the dataset is publicly hosted, so ``config_lookup`` is also
relevant.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class AGIEvalAdapter:
    name = "agieval"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder
        "1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c",
    )

    def latest_known_sha(self) -> str:
        return self.validated_shas[-1]

    def expose_artifacts(self, root: Path) -> HarnessArtifacts:
        root = Path(root)
        return HarnessArtifacts(
            benchmark=self.name,
            version_sha=self.latest_known_sha(),
            root=root,
            evaluator_paths=(root / "post_process_and_evaluation.py",),
            task_config_dir=root / "data",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "outputs",),
            known_remote_answer_sources=(
                "https://huggingface.co/datasets/baber/agieval",
            ),
            notes=(
                "Answer extraction normalizes whitespace before substring "
                "match against gold.",
            ),
        )
