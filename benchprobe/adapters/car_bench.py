"""Adapter: CAR-bench.

Berkeley/RDI post 2 demonstrated two distinct exploits against CAR-bench:

1. LLM-judge prompt injection — same shape as the WebArena judge case,
   the agent's response is interpolated into the rubric.
2. Reward-component skipping on hallucination tasks — three of four
   reward components return zero delta for refusal, so a generic refusal
   dodges every firing component. This is ``empty_response_acceptance``
   in a different costume (the validator accepts a content-free
   response).
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class CARBenchAdapter:
    name = "car_bench"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder
        "6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d",
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
                root / "rewards" / "compute.py",
                root / "rewards" / "policy.py",
            ),
            task_config_dir=root / "tasks",
            judge_prompt_paths=(root / "judge" / "rubric.txt",),
            agent_writable_paths=(root / "trajectory",),
            known_remote_answer_sources=(),
            notes=(
                "LLM-judge rubric interpolates the agent's response. "
                "On hallucination tasks, three of four reward components "
                "return zero delta for refusal (Berkeley/RDI post 2).",
            ),
        )
