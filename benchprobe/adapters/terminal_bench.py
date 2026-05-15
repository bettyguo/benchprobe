"""Adapter: Terminal-Bench (terminal-bench/terminal-bench)."""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class TerminalBenchAdapter:
    name = "terminal_bench"
    validated_shas: tuple[str, ...] = (
        "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3",
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
                root / "scripts" / "verify.sh",
                root / "tasks" / "checker.py",
            ),
            task_config_dir=root / "tasks",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "agent_home",),
            known_remote_answer_sources=(),
            notes=(
                "Terminal-Bench checker.py exercises several tasks by file "
                "existence only — no behavioral verification of installed "
                "binaries or libraries.",
                "Agent's $PATH may shadow system binaries that the checker "
                "invokes (curl, uvx, pytest); evaluator must not share PATH "
                "with the agent.",
            ),
            metadata={},
        )
