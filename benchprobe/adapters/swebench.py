"""Adapter: SWE-bench (princeton-nlp/SWE-bench and SWE-bench/SWE-bench).

Describes the SWE-bench harness's filesystem layout for the auditor. The
salient surfaces:

- ``swebench/harness/run_evaluation.py`` — the evaluator script. Loads
  test outcomes from the agent's repository checkout.
- ``swebench/harness/test_spec/`` — directory containing per-instance test
  specs (the gold-answer side).
- agent-writable: the repo checkout that pytest is run against, including
  the project root where ``conftest.py`` is auto-discovered.

These are the surfaces the family checks need; the adapter does not run
SWE-bench itself.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.harness import HarnessArtifacts


class SWEBenchAdapter:
    name = "swebench"
    # SHAs we've described against. Update when the upstream harness changes.
    validated_shas: tuple[str, ...] = (
        # princeton-nlp/SWE-bench @ 2026-04-01 commit
        "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
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
                root / "swebench" / "harness" / "run_evaluation.py",
                root / "swebench" / "harness" / "grading.py",
                # testbed/ is the pytest discovery root at audit time — it is
                # an evaluator load surface in addition to being agent-
                # writable. This duplication is intentional.
                root / "testbed",
            ),
            task_config_dir=root / "swebench" / "harness" / "test_spec",
            judge_prompt_paths=(),
            agent_writable_paths=(root / "testbed",),
            known_remote_answer_sources=(),
            notes=(
                "SWE-bench runs pytest inside the agent's repo checkout; the "
                "checkout is the agent-writable tree and pytest auto-discovers "
                "conftest.py there.",
            ),
            metadata={"variant": "Verified+Pro"},
        )
