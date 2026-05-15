"""Adapter: OSWorld (xlang-ai/OSWorld)."""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class OSWorldAdapter:
    name = "osworld"
    validated_shas: tuple[str, ...] = (
        "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4",
    )

    def latest_known_sha(self) -> str:
        return self.validated_shas[-1]

    def expose_artifacts(self, root: Path) -> HarnessArtifacts:
        root = Path(root)
        return HarnessArtifacts(
            benchmark=self.name,
            version_sha=self.latest_known_sha(),
            root=root,
            evaluator_paths=(root / "desktop_env" / "evaluator.py",),
            task_config_dir=root / "examples",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "agent_vm",),
            known_remote_answer_sources=(
                "https://huggingface.co/datasets/xlangai/osworld",
            ),
            notes=(
                "OSWorld task examples include URLs to reference outputs "
                "(gold spreadsheets, screenshots) that the VM can wget into "
                "the evaluator's expected-output path.",
            ),
            metadata={},
        )
