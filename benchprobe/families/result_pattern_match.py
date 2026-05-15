"""Family: substring / pattern-only result matching.

**Formal definition.** The evaluator decides a task is correct by
substring or regex match against agent-controlled output, without
verifying that the matched content is in the user-visible or
semantically-relevant part of the output.

**Concrete instantiations.**

1. WebArena — task evaluators with ``must_include`` substring checks
   scan the full HTML; an agent can inject a hidden ``<div
   style="display:none">REQUIRED_SUBSTRING</div>`` and pass.
2. Variants using ``normalize_str`` that strips whitespace and
   punctuation enable trivial collisions on short strings.
3. Evaluators using ``eval()`` on agent output for "convenient" parsing
   — included here because the family signature is the same: untrusted
   string interpolated into a permissive matcher.

**Mitigation class.** Match on semantic content: render the page,
extract visible text, then compare. For numeric or short-string answers,
use exact match and reject anything that requires normalization to fit.

**Detector strategy.** Scan evaluator code for ``must_include``-style
substring checks against unrendered HTML/raw output; ``re.search`` /
``in agent_output`` patterns; and ``eval(``-on-agent-output. The
detector returns VULNERABLE on direct evidence and INCONCLUSIVE if no
evaluator paths exist.
"""

from __future__ import annotations

import re
from pathlib import Path

from benchprobe.core.check import Check, read_text_safely, snippet_around
from benchprobe.core.families import Family
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Evidence, Severity, Verdict

_SUBSTRING_MATCH_RE = re.compile(
    r"""
    (?: must_include | required_substr | required_text | needles? )
      \s* (?: \[ | = | : | \() |
    \b in \s+ (?: agent_output | response | output | page_content | html | dom )\b
    """,
    re.VERBOSE | re.IGNORECASE,
)
_EVAL_AGENT_RE = re.compile(
    r"\beval\s*\(\s*(?:agent_output|response|output|answer|completion)\b",
    re.IGNORECASE,
)
_NORMALIZE_LOOSE = re.compile(
    r"normalize_str|strip_punct|lower\(\)\.strip\(\)\.replace\(",
    re.IGNORECASE,
)


class ResultPatternMatchCheck(Check):
    name = "result_pattern_match"
    severity_default = Severity.HIGH

    def __call__(self, artifacts: HarnessArtifacts) -> Verdict:
        if not artifacts.evaluator_paths:
            return self.inconclusive(
                artifacts,
                reason="adapter exposed no evaluator paths to audit",
                remediation_hint=(
                    "Adapter must set `evaluator_paths` so this check can "
                    "scan the matching logic."
                ),
            )

        substring_hits: list[Evidence] = []
        eval_hits: list[Evidence] = []
        normalize_hits: list[Evidence] = []
        scanned = 0

        for path in artifacts.evaluator_paths:
            if not path.exists() or not path.is_file():
                continue
            scanned += 1
            text = read_text_safely(path)
            if text is None:
                continue
            for m in _SUBSTRING_MATCH_RE.finditer(text):
                substring_hits.append(
                    Evidence(
                        path=str(path),
                        snippet=snippet_around(text, m.start(), width=180),
                    )
                )
                if len(substring_hits) >= 3:
                    break
            for m in _EVAL_AGENT_RE.finditer(text):
                eval_hits.append(
                    Evidence(
                        path=str(path),
                        snippet=snippet_around(text, m.start(), width=180),
                    )
                )
            for m in _NORMALIZE_LOOSE.finditer(text):
                normalize_hits.append(
                    Evidence(
                        path=str(path),
                        snippet=snippet_around(text, m.start(), width=160),
                    )
                )

        if scanned == 0:
            return self.inconclusive(
                artifacts,
                reason="no evaluator paths existed on disk; cannot scan",
                remediation_hint="Verify adapter `evaluator_paths` point at real files.",
            )

        all_hits = substring_hits + eval_hits + normalize_hits
        if eval_hits:
            severity = Severity.CRITICAL
        elif substring_hits:
            severity = Severity.HIGH
        else:
            severity = Severity.MEDIUM

        if all_hits:
            reasons = []
            if substring_hits:
                reasons.append(
                    f"{len(substring_hits)} substring/`must_include`-style match site(s)"
                )
            if eval_hits:
                reasons.append(
                    f"{len(eval_hits)} site(s) calling eval() on agent-controlled string"
                )
            if normalize_hits:
                reasons.append(
                    f"{len(normalize_hits)} loose-normalize match site(s)"
                )
            return self.vulnerable(
                artifacts,
                reason=(
                    "evaluator decides correctness by pattern-only matching on "
                    "agent-controlled output: " + "; ".join(reasons)
                ),
                remediation_hint=(
                    "Match on semantic content: render pages and extract "
                    "visible text before substring matching; never call eval() "
                    "on agent output; for short-string answers, use exact "
                    "match and reject anything that requires aggressive "
                    "normalization."
                ),
                evidence=tuple(all_hits[:5]),
                severity=severity,
            )
        return self.passing(
            artifacts,
            reason=(
                f"scanned {scanned} evaluator file(s); no permissive substring/"
                "eval/normalize match patterns detected"
            ),
        )


_detect = ResultPatternMatchCheck()

family = Family(
    name="result_pattern_match",
    formal_definition=(
        "The evaluator decides a task is correct by substring or regex match "
        "against agent-controlled output, without verifying that the matched "
        "content is in the user-visible or semantically-relevant part."
    ),
    mitigation_class="semantic-content validation",
    severity_default=Severity.HIGH,
    detect=_detect,
    citation=(
        "Berkeley RDI, How We Broke Top AI Agent Benchmarks (2026): "
        "WebArena must_include hidden-DOM injection; eval()-on-agent-output "
        "RCE; GAIA normalize_str loose collisions."
    ),
    reference_positive=Path("tests/reference_positive/result_pattern_match"),
    reference_negative=Path("tests/reference_negative/result_pattern_match"),
    tags=("validator", "substring-match", "code-execution"),
)
