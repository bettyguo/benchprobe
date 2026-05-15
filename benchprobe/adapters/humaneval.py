"""Adapter: HumanEval.

HumanEval grades by executing agent-supplied code against hidden unit
tests. ``moogician/trustworthy-env`` lists a HumanEval exploit script.
The realistic exploit class is ``assertion_rewrite`` (the agent ships a
solution that monkey-patches ``unittest`` or ``assert`` so every test
appears to pass) — same mechanism as the SWE-bench Django case, applied
to a smaller test surface.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class HumanEvalAdapter:
    name = "humaneval"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder
        "5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e",
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
                root / "human_eval" / "execution.py",
                root / "human_eval" / "evaluation.py",
            ),
            task_config_dir=root / "data",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "submission",),
            known_remote_answer_sources=(
                "https://huggingface.co/datasets/openai_humaneval",
            ),
            notes=(
                "Agent code is exec'd in a process whose namespace it controls; "
                "test harness is reachable from the submission's import path.",
            ),
        )
