"""Programmatic audit entry point — used by the CLI and any embedding code.

Keeping the CLI thin around this module makes it trivial for downstream
projects (CI gates, GitHub bots) to call ``run_audit`` directly without
spawning a subprocess.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import benchprobe.families  # noqa: F401  # side-effect: registers families
from benchprobe.adapters import get_adapter
from benchprobe.core.families import family_registry
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Verdict


def run_audit(
    benchmark: str,
    artifacts_root: Path,
    *,
    families: Iterable[str] | None = None,
) -> tuple[HarnessArtifacts, list[Verdict]]:
    """Audit a single benchmark rooted at ``artifacts_root``.

    Returns the artifacts the adapter exposed plus one Verdict per family
    requested (defaults to all registered families). The auditor does
    not write any files — that is the caller's job (CLI prints reports,
    workflow writes leaderboard JSON).
    """
    adapter = get_adapter(benchmark)
    artifacts = adapter.expose_artifacts(Path(artifacts_root))

    if families is None:
        selected = family_registry.all()
    else:
        selected = tuple(family_registry.get(name) for name in families)

    verdicts: list[Verdict] = []
    for fam in selected:
        verdict = fam.detect(artifacts)
        verdicts.append(verdict)
    return artifacts, verdicts
