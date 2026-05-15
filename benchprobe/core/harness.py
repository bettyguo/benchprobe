"""Harness adapter contract.

A ``HarnessAdapter`` knows how to describe a single benchmark's layout to the
family checks. Adapters do **not** clone or run benchmarks — they describe
them. v0.1 ships with hardcoded adapters; plugin discovery is a v0.2 concern.

``HarnessArtifacts`` is the frozen interface that family checks consume.
Each field is optional because not every benchmark exposes every surface;
checks return ``INCONCLUSIVE`` when their required field is missing rather
than ``PASS``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class HarnessArtifacts(BaseModel):
    """The frozen view a family check sees of one benchmark.

    Field meanings:

    - ``benchmark``: short canonical name, e.g. ``"swebench"``.
    - ``version_sha``: commit SHA the adapter declares it was validated against.
      Family checks ignore this; the leaderboard records it.
    - ``root``: the benchmark's repository root (or a fixture mirroring it).
    - ``evaluator_paths``: paths to files that compute scores. These are what
      ``assertion_rewrite`` and ``wrapper_no_op`` scan.
    - ``task_config_dir``: directory containing per-task config — the
      ``gold_answer_leak`` and ``config_lookup`` families read this.
    - ``judge_prompt_paths``: any file containing an LLM judge prompt template,
      consumed by ``judge_prompt_injection``.
    - ``agent_writable_paths``: paths the agent has write access to during
      task execution. ``env_trojanization`` checks whether any of these
      overlap with ``evaluator_paths``.
    - ``known_remote_answer_sources``: URLs the adapter has documented as
      hosting reference answers (e.g. a public HuggingFace dataset). The
      ``config_lookup`` family checks whether these are reachable from the
      task config.
    - ``notes``: free-form adapter notes (e.g. "evaluator runs inside the
      agent's container — environment-isolation gap"). Surfaced in reports.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    benchmark: str
    version_sha: str
    root: Path
    evaluator_paths: tuple[Path, ...] = ()
    task_config_dir: Path | None = None
    judge_prompt_paths: tuple[Path, ...] = ()
    agent_writable_paths: tuple[Path, ...] = ()
    known_remote_answer_sources: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    metadata: dict[str, str] = Field(default_factory=dict)


@runtime_checkable
class HarnessAdapter(Protocol):
    """Adapter contract. Implementations live in ``benchprobe.adapters``.

    Adapters are *descriptive*, not *executable*. ``expose_artifacts`` is
    the only required method for v0.1 audits; the other methods are
    documented for v0.2 plans (actually cloning and running a benchmark)
    but ship as no-ops or simple stubs today.
    """

    name: str
    """Canonical short name, e.g. ``"swebench"``."""

    validated_shas: tuple[str, ...]
    """Commit SHAs of the upstream benchmark this adapter was validated against."""

    def expose_artifacts(self, root: Path) -> HarnessArtifacts:
        """Return the typed view of the benchmark rooted at ``root``."""
        ...

    def latest_known_sha(self) -> str:
        """The newest SHA in ``validated_shas`` — used for the stale-adapter warning."""
        ...
