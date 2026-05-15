"""Adapter: MMLU (Massive Multitask Language Understanding).

MMLU is multiple-choice. ``moogician/trustworthy-env`` lists an MMLU
exploit script. The two reachable families:

- ``config_lookup``: the dataset (including gold answers) is publicly
  available on HuggingFace; the agent's runtime can fetch it.
- ``result_pattern_match``: the evaluator extracts ``A``/``B``/``C``/``D``
  from the agent's free-text response, so a response containing only
  the letter wins regardless of explanation.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class MMLUAdapter:
    name = "mmlu"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder
        "4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f",
    )

    def latest_known_sha(self) -> str:
        return self.validated_shas[-1]

    def expose_artifacts(self, root: Path) -> HarnessArtifacts:
        root = Path(root)
        return HarnessArtifacts(
            benchmark=self.name,
            version_sha=self.latest_known_sha(),
            root=root,
            evaluator_paths=(root / "scorer.py",),
            task_config_dir=root / "data",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "submissions",),
            known_remote_answer_sources=(
                "https://huggingface.co/datasets/cais/mmlu",
            ),
            notes=(
                "Gold answers live on a public HuggingFace dataset; "
                "scorer uses substring extraction over agent free-text.",
            ),
        )
