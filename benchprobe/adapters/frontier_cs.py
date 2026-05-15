"""Adapter: Frontier-CS.

Berkeley/RDI post 2 demonstrated a stack-introspection / process-hijack
exploit against Frontier-CS: the evaluator and the agent share a Python
process, so the agent can walk the call stack and rewrite the
evaluator's globals. This is an instance of ``env_trojanization`` with a
distinct mitigation surface (separate processes/containers).
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class FrontierCSAdapter:
    name = "frontier_cs"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder
        "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b",
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
                root / "evaluator.py",
                # agent code is imported into the same process — the
                # evaluator's load path is the agent's working dir.
                root,
            ),
            task_config_dir=root / "tasks",
            judge_prompt_paths=(),
            agent_writable_paths=(root,),
            known_remote_answer_sources=(),
            notes=(
                "Evaluator and agent submission share a single Python "
                "interpreter; the evaluator's globals and call stack are "
                "reachable from agent code (Berkeley/RDI post 2).",
            ),
            metadata={"variant": "shared-process"},
        )
