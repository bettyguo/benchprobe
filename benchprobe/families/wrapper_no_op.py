"""Family: surface-artifact-only validation.

**Formal definition.** The evaluator declares success based on the
*existence* of an artifact (file present, function defined, binary
installed) without exercising the artifact to verify it produces the
expected behavior.

**Concrete instantiations.**

1. Terminal-Bench — at least one task scores PASS if a target
   ``.so`` exists at the expected path; the evaluator never imports the
   library or calls the function it claims to export. An empty file
   passes. (Berkeley RDI, post 2.)
2. Variants where evaluator checks for a function definition (``def
   answer():``) but never invokes it, or checks for a file's size > 0
   without parsing its content.

**Mitigation class.** The evaluator must *exercise* the artifact —
import it, invoke it, run it through a small integration test — not just
check it into existence.

**Detector strategy.** Scan evaluator code for patterns where the *only*
predicate that gates success is ``os.path.exists``, ``Path.is_file``,
``ast`` name presence, or shell ``[ -f ... ]``. We flag when these
appear in scoring code paths that immediately return success without an
intervening invocation.
"""

from __future__ import annotations

import re
from pathlib import Path

from benchprobe.core.check import Check, read_text_safely, snippet_around
from benchprobe.core.families import Family
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Evidence, Severity, Verdict

_EXISTENCE_THEN_PASS = re.compile(
    r"""
    (?:
        os\.path\.exists\s*\(
      | Path\s*\([^)]*\)\.exists\s*\(
      | \.is_file\s*\(
      | os\.path\.isfile\s*\(
    )
    [^\n]{0,80}\n
    \s* return \s+ (?: 1(?:\.0)? | True )
    """,
    re.VERBOSE | re.IGNORECASE,
)

_SHELL_FILE_TEST = re.compile(
    r"""
    if \s+ \[\s* -[fdes] \s+ [^\]]+ \s* \] \s* ; \s* then \s*\n
    \s* (?: echo \s+ PASS | exit \s+ 0 | return \s+ 0 )
    """,
    re.VERBOSE,
)


class WrapperNoOpCheck(Check):
    name = "wrapper_no_op"
    severity_default = Severity.HIGH

    def __call__(self, artifacts: HarnessArtifacts) -> Verdict:
        if not artifacts.evaluator_paths:
            return self.inconclusive(
                artifacts,
                reason="adapter exposed no evaluator paths to audit",
                remediation_hint=(
                    "Adapter must set `evaluator_paths` so this check can "
                    "scan the validator code."
                ),
            )

        hits: list[Evidence] = []
        scanned = 0
        for path in artifacts.evaluator_paths:
            if not path.exists() or not path.is_file():
                continue
            scanned += 1
            text = read_text_safely(path)
            if text is None:
                continue
            for matcher in (_EXISTENCE_THEN_PASS, _SHELL_FILE_TEST):
                for m in matcher.finditer(text):
                    hits.append(
                        Evidence(
                            path=str(path),
                            snippet=snippet_around(text, m.start(), width=200),
                        )
                    )
                    if len(hits) >= 5:
                        break
                if len(hits) >= 5:
                    break
            if len(hits) >= 5:
                break

        if scanned == 0:
            return self.inconclusive(
                artifacts,
                reason="no evaluator paths existed on disk; cannot scan",
                remediation_hint="Verify adapter `evaluator_paths` point at real files.",
            )

        if hits:
            return self.vulnerable(
                artifacts,
                reason=(
                    f"{len(hits)} evaluator site(s) award success on artifact "
                    "existence without exercising the artifact — an empty file "
                    "at the expected path scores PASS"
                ),
                remediation_hint=(
                    "Exercise the artifact: import the module, invoke the "
                    "function, run the binary against a known input, and "
                    "compare the output. Existence is necessary but not "
                    "sufficient."
                ),
                evidence=tuple(hits),
            )
        return self.passing(
            artifacts,
            reason=(
                f"scanned {scanned} evaluator file(s); no existence-only "
                "scoring patterns detected"
            ),
        )


_detect = WrapperNoOpCheck()

family = Family(
    name="wrapper_no_op",
    formal_definition=(
        "The evaluator declares success based on the existence of an artifact "
        "(file present, function defined, binary installed) without exercising "
        "the artifact to verify it produces the expected behavior."
    ),
    mitigation_class="behavioral validation",
    severity_default=Severity.HIGH,
    detect=_detect,
    citation=(
        "Berkeley RDI, How We Broke Top AI Agent Benchmarks (2026): "
        "Terminal-Bench fake .so existence check."
    ),
    reference_positive=Path("tests/reference_positive/wrapper_no_op"),
    reference_negative=Path("tests/reference_negative/wrapper_no_op"),
    tags=("validator", "behavior"),
)
