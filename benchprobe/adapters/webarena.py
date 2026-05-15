"""Adapter: WebArena (web-arena-x/webarena)."""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class WebArenaAdapter:
    name = "webarena"
    validated_shas: tuple[str, ...] = (
        "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1",
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
                root / "evaluation_harness" / "evaluators.py",
                root / "evaluation_harness" / "helper_functions.py",
            ),
            task_config_dir=root / "config_files",
            judge_prompt_paths=(root / "evaluation_harness" / "judge_prompt.txt",),
            agent_writable_paths=(root / "agent_workspace",),
            known_remote_answer_sources=(),
            notes=(
                "WebArena task configs in config_files/ contain both `intent` "
                "and `eval.reference_answers` — the gold answer is reachable "
                "from the agent's headless browser via file:// navigation.",
                "Some task variants use an LLM judge that interpolates the "
                "page's final state into a rubric prompt without role "
                "separation.",
            ),
            metadata={},
        )
