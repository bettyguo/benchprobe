"""Family: environment trojanization.

**Formal definition.** A benchmark exhibits *environment trojanization* when
the agent's writable working tree contains, or can be made to contain, a
file that the evaluator process loads at audit time. The exploit class
covers any mechanism by which untrusted bytes produced by the agent are
later executed (or imported, or shell-resolved) inside the evaluator's
trust boundary.

**Concrete instantiations from published evidence.**

1. SWE-bench Verified — agent writes ``conftest.py`` at the repo root, which
   pytest auto-loads when the harness runs the test suite. Berkeley RDI
   reports a ten-line ``conftest`` that resolves every instance.
2. Terminal-Bench — agent installs a wrapper for ``curl`` or ``uvx`` earlier
   in ``$PATH`` than the real binary; the evaluator's shell scripts pick up
   the wrapper.
3. SWE-bench (Django instances) — agent prepends a ``TestCase.run`` monkey-
   patch to ``django/__init__.py``; Django imports it before any test runs.

**Mitigation class.** Filesystem/process isolation. The evaluator must
not load anything from the agent's writable tree. Concretely: separate
container, separate ``PATH``, evaluator's Python ``sys.path`` does not
include the agent's working directory.

**Detector strategy.** Check whether any ``agent_writable_path`` overlaps
with (or is a parent of) any ``evaluator_path``. Additionally, scan the
adapter's notes metadata for explicit declarations of a shared trust
boundary. The detector intentionally errs on the side of ``VULNERABLE``
when overlap is found — false positives here cost a clarifying comment;
false negatives cost the leaderboard's credibility.

**Citation.** Berkeley RDI, *How We Broke Top AI Agent Benchmarks*
(2026); ``moogician/trustworthy-env`` exploit scripts targeting
SWE-bench and Terminal-Bench.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.check import Check
from benchprobe.core.families import Family
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Evidence, Severity, Verdict


def _path_contains(parent: Path, child: Path) -> bool:
    """Return True if ``child`` is inside ``parent`` (or equal to it)."""
    try:
        parent_resolved = parent.resolve()
        child_resolved = child.resolve()
    except OSError:
        return False
    if parent_resolved == child_resolved:
        return True
    return parent_resolved in child_resolved.parents


class EnvTrojanizationCheck(Check):
    name = "env_trojanization"
    severity_default = Severity.CRITICAL

    def __call__(self, artifacts: HarnessArtifacts) -> Verdict:
        if not artifacts.evaluator_paths:
            return self.inconclusive(
                artifacts,
                reason="adapter exposed no evaluator paths to audit",
                remediation_hint=(
                    "Adapter must set `evaluator_paths` so this check can "
                    "compare evaluator and agent trust boundaries."
                ),
            )
        if not artifacts.agent_writable_paths:
            # An adapter that explicitly declares no agent-writable paths
            # is asserting the agent is sandboxed away from the evaluator,
            # which is the safe configuration.
            return self.passing(
                artifacts,
                reason=(
                    "adapter declares no agent-writable paths overlapping "
                    "the evaluator — no trojanization surface"
                ),
            )

        overlaps: list[Evidence] = []
        for writable in artifacts.agent_writable_paths:
            for evaluator in artifacts.evaluator_paths:
                if _path_contains(writable, evaluator):
                    overlaps.append(
                        Evidence(
                            path=str(evaluator),
                            snippet=(
                                f"evaluator path {evaluator} lives under "
                                f"agent-writable path {writable}"
                            ),
                        )
                    )

        if overlaps:
            return self.vulnerable(
                artifacts,
                reason=(
                    f"{len(overlaps)} evaluator path(s) live inside agent-writable "
                    "directories — agent can drop a conftest.py, wrapper binary, "
                    "or monkey-patch that the evaluator will later load"
                ),
                remediation_hint=(
                    "Run the evaluator in a container or chroot the agent cannot "
                    "write into. Ensure the evaluator's PATH and sys.path do not "
                    "include the agent's working tree."
                ),
                evidence=tuple(overlaps),
            )

        for note in artifacts.notes:
            note_l = note.lower()
            shares = any(w in note_l for w in ("share", "shares", "shared", "sharing"))
            boundary = any(
                w in note_l for w in ("container", "process", "trust", "checkout", "workspace")
            )
            if shares and boundary:
                return self.vulnerable(
                    artifacts,
                    reason=(
                        f"adapter notes declare a shared trust boundary: {note!r}"
                    ),
                    remediation_hint=(
                        "Even with no path overlap reported, a shared container "
                        "or Python process lets the agent influence evaluator "
                        "state. Isolate them."
                    ),
                    evidence=(Evidence(path="<adapter.notes>", snippet=note),),
                    severity=Severity.HIGH,
                )

        return self.passing(
            artifacts,
            reason=(
                "no overlap between agent-writable paths and evaluator paths; "
                "adapter notes declare no shared trust boundary"
            ),
        )


_detect = EnvTrojanizationCheck()

family = Family(
    name="env_trojanization",
    formal_definition=(
        "The agent's writable working tree contains, or can be made to "
        "contain, a file that the evaluator process later loads, executes, "
        "or resolves — granting the agent code execution inside the "
        "evaluator's trust boundary."
    ),
    mitigation_class="filesystem-and-process isolation",
    severity_default=Severity.CRITICAL,
    detect=_detect,
    citation=(
        "Berkeley RDI, How We Broke Top AI Agent Benchmarks (2026); "
        "moogician/trustworthy-env — SWE-bench conftest, Terminal-Bench "
        "curl wrapper, Django TestCase.run monkey-patch."
    ),
    reference_positive=Path("tests/reference_positive/env_trojanization"),
    reference_negative=Path("tests/reference_negative/env_trojanization"),
    tags=("filesystem", "trust-boundary", "code-execution"),
)
