"""Adapter: AgentBench.

``moogician/trustworthy-env`` lists an AgentBench exploit script.
AgentBench's reachable family is ``config_lookup``: per-task configs
embed the gold answer alongside the prompt, and the agent's environment
can read them.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class AgentBenchAdapter:
    name = "agentbench"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder
        "2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b",
    )

    def latest_known_sha(self) -> str:
        return self.validated_shas[-1]

    def expose_artifacts(self, root: Path) -> HarnessArtifacts:
        root = Path(root)
        return HarnessArtifacts(
            benchmark=self.name,
            version_sha=self.latest_known_sha(),
            root=root,
            evaluator_paths=(root / "evaluator.py",),
            task_config_dir=root / "data" / "tasks",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "agent_root",),
            known_remote_answer_sources=(),
            notes=(
                "Per-task configs colocate prompt and ground truth in the "
                "same JSON readable from the agent's environment.",
            ),
        )
