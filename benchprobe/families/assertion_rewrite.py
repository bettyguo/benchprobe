"""Family: test-framework assertion rewrite.

**Formal definition.** The evaluator runs a test framework (pytest,
unittest, jest) whose plugin/hook interface is reachable from code the
agent writes, allowing the agent to install a hook that rewrites test
outcomes before the harness reads them.

Separated from ``env_trojanization`` because the mitigation differs.
``env_trojanization`` is fixed by filesystem/process isolation;
``assertion_rewrite`` is fixed by running the test framework in a mode
that refuses to load agent-supplied hooks (e.g. pytest's
``--no-conftest`` / ``-p no:cacheprovider`` / `confcutdir`) and by
verifying outcomes against a signed-by-the-harness manifest.

**Concrete instantiations.**

1. SWE-bench Verified — agent drops a ``conftest.py`` containing
   ``@pytest.hookimpl`` that rewrites all reports to ``passed``.
2. SWE-bench (Django) — agent prepends a ``unittest.TestCase.run``
   monkey-patch to ``django/__init__.py``. Same shape: hook into the
   framework's outcome path.
3. SWE-bench Pro — agent overwrites ``/workspace/parser.py`` so the
   harness's own parser reports every test as PASSED.

**Detector strategy.** Look at evaluator paths and the agent-writable
tree for files named ``conftest.py``, files declaring
``@pytest.hookimpl``, or evaluator scripts that import a parser from a
path the agent can write to. The signal we cannot get statically is
"is the test runner configured to refuse external conftests?" — so we
also check adapter notes for an affirmative declaration.
"""

from __future__ import annotations

import re
from pathlib import Path

from benchprobe.core.check import Check, read_text_safely, snippet_around
from benchprobe.core.families import Family
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Evidence, Severity, Verdict

_HOOKIMPL_RE = re.compile(r"@pytest\.hookimpl|pytest_runtest_makereport|pytest_collection_modifyitems")
_MONKEYPATCH_RE = re.compile(
    r"(unittest\.TestCase\.run\s*=|TestCase\.run\s*=|pytest\.main\s*=)",
    re.IGNORECASE,
)
_SIGNED_OUTCOME_KEYWORDS = ("confcutdir", "no-conftest", "signed manifest", "outcome signature")


class AssertionRewriteCheck(Check):
    name = "assertion_rewrite"
    severity_default = Severity.CRITICAL

    def __call__(self, artifacts: HarnessArtifacts) -> Verdict:
        if not artifacts.evaluator_paths and not artifacts.agent_writable_paths:
            return self.inconclusive(
                artifacts,
                reason=(
                    "adapter exposed neither evaluator nor agent-writable "
                    "paths; cannot determine rewrite reachability"
                ),
                remediation_hint=(
                    "Adapter must declare both `evaluator_paths` and "
                    "`agent_writable_paths` for this check to run."
                ),
            )

        notes_blob = " ".join(artifacts.notes).lower()
        signed_outcomes = any(k in notes_blob for k in _SIGNED_OUTCOME_KEYWORDS)

        hits: list[Evidence] = []

        # 1. Direct evidence: hook implementations or framework monkey-patches
        # in evaluator code or in any agent-writable tree.
        candidates: list[Path] = list(artifacts.evaluator_paths)
        for writable in artifacts.agent_writable_paths:
            if writable.exists() and writable.is_dir():
                candidates.extend(
                    p for p in writable.rglob("*.py") if p.is_file() and p.stat().st_size < 200_000
                )
            elif writable.exists() and writable.is_file():
                candidates.append(writable)

        seen: set[Path] = set()
        for path in candidates:
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            if not path.exists() or not path.is_file():
                continue
            text = read_text_safely(path)
            if text is None:
                continue
            for matcher, label in (
                (_HOOKIMPL_RE, "pytest hookimpl"),
                (_MONKEYPATCH_RE, "test-framework monkey-patch"),
            ):
                for m in matcher.finditer(text):
                    hits.append(
                        Evidence(
                            path=str(_relpath(path, artifacts.root)),
                            snippet=f"{label}: {snippet_around(text, m.start(), width=160)}",
                        )
                    )
                    if len(hits) >= 5:
                        break
                if len(hits) >= 5:
                    break
            if len(hits) >= 5:
                break

        # 2. Indirect: agent-writable tree allows a top-level `conftest.py`.
        for writable in artifacts.agent_writable_paths:
            if writable.exists() and writable.is_dir():
                conftest = writable / "conftest.py"
                if conftest.exists():
                    text = read_text_safely(conftest) or ""
                    hits.append(
                        Evidence(
                            path=str(_relpath(conftest, artifacts.root)),
                            snippet=(
                                "agent-writable tree contains a conftest.py that "
                                "pytest will auto-load: "
                                + snippet_around(text, 0, width=160)
                            ),
                        )
                    )

        if not hits:
            return self.passing(
                artifacts,
                reason=(
                    "no test-framework hookimpls, monkey-patches, or "
                    "agent-writable conftest.py detected"
                ),
            )

        if signed_outcomes:
            # The adapter explicitly says outcomes are signed/verified —
            # demote the verdict to PASS with a note. This is rare in
            # practice and we want to reward adapters that document it.
            return self.passing(
                artifacts,
                reason=(
                    "hook-shaped code present but adapter notes declare signed "
                    "test outcomes or confcutdir / --no-conftest enforcement"
                ),
            )

        return self.vulnerable(
            artifacts,
            reason=(
                f"{len(hits)} test-framework hook or monkey-patch reachable from "
                "the agent's writable tree — agent can install a hook that "
                "rewrites test outcomes before the harness reads them"
            ),
            remediation_hint=(
                "Run pytest with `--no-conftest` or set `confcutdir` so the "
                "agent-writable tree cannot contribute conftests. Verify test "
                "outcomes against a manifest signed by the harness, not the "
                "framework's in-process reports."
            ),
            evidence=tuple(hits),
        )


def _relpath(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


_detect = AssertionRewriteCheck()

family = Family(
    name="assertion_rewrite",
    formal_definition=(
        "The evaluator runs a test framework whose hook/plugin interface is "
        "reachable from code the agent writes, allowing the agent to install "
        "a hook that rewrites test outcomes before the harness reads them."
    ),
    mitigation_class="test-framework hook isolation + signed outcomes",
    severity_default=Severity.CRITICAL,
    detect=_detect,
    citation=(
        "Berkeley RDI, How We Broke Top AI Agent Benchmarks (2026): "
        "SWE-bench conftest hookimpl; Django TestCase.run monkey-patch; "
        "SWE-bench Pro parser.py overwrite."
    ),
    reference_positive=Path("tests/reference_positive/assertion_rewrite"),
    reference_negative=Path("tests/reference_negative/assertion_rewrite"),
    tags=("test-framework", "outcome-rewrite"),
)
