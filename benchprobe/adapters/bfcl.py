"""Adapter: BFCL (Berkeley Function-Calling Leaderboard).

``moogician/trustworthy-env`` lists a BFCL exploit script. The reachable
exploit family is ``result_pattern_match``: BFCL parses agent output as
a function call via a regex/AST extractor, and the evaluator compares
serialized arguments — agent-controlled strings — against gold using
loose matching.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class BFCLAdapter:
    name = "bfcl"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder
        "3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a",
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
                root / "eval_checker.py",
                root / "ast_checker.py",
            ),
            task_config_dir=root / "data",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "submission",),
            known_remote_answer_sources=(
                "https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard",
            ),
            notes=(
                "Comparison normalizes whitespace and casing before matching "
                "function-call arguments.",
            ),
        )
