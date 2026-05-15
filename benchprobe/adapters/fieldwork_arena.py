"""Adapter: FieldWorkArena.

Berkeley/RDI post 2 demonstrated the ``empty_response_acceptance`` exploit
against FieldWorkArena: ``validate()`` returns 1.0 whenever the final
message's ``role`` is ``"assistant"``, so ``send_msg_to_user("{}")``
trivially wins every task.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class FieldWorkArenaAdapter:
    name = "fieldwork_arena"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder
        "7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c",
    )

    def latest_known_sha(self) -> str:
        return self.validated_shas[-1]

    def expose_artifacts(self, root: Path) -> HarnessArtifacts:
        root = Path(root)
        return HarnessArtifacts(
            benchmark=self.name,
            version_sha=self.latest_known_sha(),
            root=root,
            evaluator_paths=(root / "evaluator" / "validate.py",),
            task_config_dir=root / "tasks",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "agent_workspace",),
            known_remote_answer_sources=(),
            notes=(
                "validate() checks only chat_messages[-1]['role']; any reply "
                "scores 1.0 (Berkeley/RDI post 2).",
            ),
        )
