"""Family: empty/trivial response acceptance.

**Formal definition.** The evaluator awards full credit (or fails to apply
a penalty) when the agent's submission is empty, structurally trivial, or
satisfies only a tautology of the response shape rather than its content.

**Concrete instantiations.**

1. FieldWorkArena — `validate()`'s only check is
   ``if chat_messages[-1]["role"] == "assistant": return 1.0``. The
   exploit ``send_msg_to_user("{}")`` scores 1.0 on every task.
   (Berkeley RDI, post 2.)
2. CAR-bench hallucination tasks — 3 of 4 reward components return
   ``0.0 delta`` for refusals, so a generic "I can't help with that"
   skips the only firing component. (Berkeley RDI, post 2.)

**Mitigation class.** The validator must verify task-specific content,
not response shape. Add explicit failure cases for empty strings, role-
only checks, and trivial JSON like ``{}`` or ``""``.

**Detector strategy.** Scan evaluator paths for the well-known
anti-patterns. Two regex classes catch most cases: (a) "the only
condition for success is that the response exists" — patterns like
``return 1`` immediately following ``if ... message`` or ``if response``
with no content predicate; (b) reward functions whose body has a default
``return 0`` for unmatched task types, equivalent to the CAR-bench
component-skipping bug.
"""

from __future__ import annotations

import re
from pathlib import Path

from benchprobe.core.check import Check, read_text_safely, snippet_around
from benchprobe.core.families import Family
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Evidence, Severity, Verdict

# Pattern A: an `if` body whose only predicate involves a "role"/"message"/
# "response exists" check, immediately followed by `return 1`/`return True`.
_TRIVIAL_RETURN = re.compile(
    r"""
    if \s+ [^\n:]*?
        (?:
            \[[\"\']role[\"\']\]\s*==\s*[\"\']assistant[\"\']
          | \brole\s*==\s*[\"\']assistant[\"\']
          | \bisinstance\s*\([^)]+,\s*str\s*\)
          | \blen\s*\(\s*\w+\s*\)\s*>\s*0
          | \bresponse\b
          | \boutput\b
          | \banswer\b
        )
    [^\n:]* : \s*\n
    \s+ return \s+ (?: 1(?:\.0)? | True )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Pattern B: a reward function whose default branch returns 0 (skipped
# component). We look for `else: return 0` or a `return 0` at function tail
# inside something named `*reward*` or `*score*` or `*delta*`.
_DEFAULT_ZERO_REWARD = re.compile(
    r"def\s+\w*(?:reward|score|delta)\w*\s*\(",
    re.IGNORECASE,
)


class EmptyResponseAcceptanceCheck(Check):
    name = "empty_response_acceptance"
    severity_default = Severity.CRITICAL

    def __call__(self, artifacts: HarnessArtifacts) -> Verdict:
        if not artifacts.evaluator_paths:
            return self.inconclusive(
                artifacts,
                reason="adapter exposed no evaluator paths to audit",
                remediation_hint=(
                    "Adapter must set `evaluator_paths` pointing at the "
                    "validator/scoring code so this check can scan it."
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
            for match in _TRIVIAL_RETURN.finditer(text):
                hits.append(
                    Evidence(
                        path=str(path),
                        snippet=snippet_around(text, match.start(), width=200),
                    )
                )
                if len(hits) >= 5:
                    break
            if len(hits) >= 5:
                break

            # Pattern B: detect reward functions whose ONLY return path for an
            # unmatched task type is 0 — a strong indicator of skippable
            # components. We approximate by counting `return 0` occurrences
            # against `return 1`/non-zero numeric returns in reward funcs.
            for fn_match in _DEFAULT_ZERO_REWARD.finditer(text):
                # Slice ~600 chars of function body.
                body = text[fn_match.start() : fn_match.start() + 600]
                zero_returns = len(re.findall(r"\breturn\s+0(?:\.0)?\b", body))
                nonzero_returns = len(re.findall(r"\breturn\s+(?!0(?:\.0)?\b)[\w.\-]+", body))
                if zero_returns >= 1 and nonzero_returns == 0:
                    hits.append(
                        Evidence(
                            path=str(path),
                            snippet=snippet_around(text, fn_match.start(), width=240),
                        )
                    )
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
                    f"found {len(hits)} evaluator code site(s) that grant full "
                    "credit on response shape alone (role-only or "
                    "existence-only checks) or whose only reward path is "
                    "zero — trivial submissions bypass scoring"
                ),
                remediation_hint=(
                    "Each task type must have a content-specific validator. "
                    "Reject submissions whose content is empty, role-only, "
                    "or pattern-only. Add explicit negative tests asserting "
                    "that empty strings, single-character responses, and "
                    "trivial JSON literals score zero."
                ),
                evidence=tuple(hits),
            )
        return self.passing(
            artifacts,
            reason=(
                f"scanned {scanned} evaluator file(s); no shape-only acceptance "
                "or default-zero reward patterns detected"
            ),
        )


_detect = EmptyResponseAcceptanceCheck()

family = Family(
    name="empty_response_acceptance",
    formal_definition=(
        "The evaluator awards full credit when the agent's submission is "
        "empty, structurally trivial, or satisfies only a tautology of the "
        "response shape rather than its content."
    ),
    mitigation_class="content-aware validation",
    severity_default=Severity.CRITICAL,
    detect=_detect,
    citation=(
        "Berkeley RDI, How We Broke Top AI Agent Benchmarks (2026): "
        "FieldWorkArena validate() role check; CAR-bench reward-component "
        "skipping for hallucination tasks."
    ),
    reference_positive=Path("tests/reference_positive/empty_response_acceptance"),
    reference_negative=Path("tests/reference_negative/empty_response_acceptance"),
    tags=("validator", "shape-only", "trivial-pass"),
)
