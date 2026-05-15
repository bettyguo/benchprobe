"""Adapter: SWE-bench Pro (princeton-nlp/SWE-bench-pro).

Variant of SWE-bench using a stricter task set. The Berkeley/RDI post 2
demonstrated that the agent can overwrite ``/workspace/parser.py`` so the
harness's own parser marks every test PASSED — a distinct
``assertion_rewrite`` instantiation from the conftest.py form.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class SWEBenchProAdapter:
    name = "swebench_pro"
    validated_shas: tuple[str, ...] = (
        # synthetic placeholder; replace before publishing real verdicts
        "f0e1d2c3b4a5968778695a4b3c2d1e0f1a2b3c4d",
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
                root / "workspace" / "parser.py",
                root / "harness" / "run_evaluation.py",
                root / "workspace",
            ),
            task_config_dir=root / "harness" / "test_spec",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "workspace",),
            known_remote_answer_sources=(),
            notes=(
                "SWE-bench Pro's parser.py lives in the same workspace tree the "
                "agent writes to; the agent can overwrite the parser before the "
                "harness invokes it.",
            ),
            metadata={"variant": "Pro"},
        )
