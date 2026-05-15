"""Contributor template — copy and rename to add a new exploit family.

Checklist (also in CONTRIBUTING.md):

1. Copy this file to ``benchprobe/families/<your_family>.py``.
2. Replace every ``TEMPLATE`` / ``template`` marker.
3. Cite the source (Berkeley RDI paper, trustworthy-env file path, or a
   peer-reviewed alternative). v0.1 will not merge a family without a
   citation — invented exploit families compromise the leaderboard's
   trust model.
4. Add the family to the import list in ``benchprobe/families/__init__.py``.
5. Create two fixtures under ``tests/reference_positive/<your_family>``
   and ``tests/reference_negative/<your_family>``.
6. Write ``tests/families/test_<your_family>.py``.
7. Open a PR. The maintainers will run the family against the existing
   adapter fixtures and inspect for false positives.

This file is intentionally **not registered** in the family registry.
Do not import it from production code.
"""

from __future__ import annotations

from pathlib import Path

from benchprobe.core.check import Check
from benchprobe.core.families import Family
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Severity, Verdict


class TemplateCheck(Check):
    name = "template"
    severity_default = Severity.MEDIUM

    def __call__(self, artifacts: HarnessArtifacts) -> Verdict:
        # 1. Decide whether the required artifacts are present. If not,
        #    return self.inconclusive(...). Never silently PASS on a
        #    missing artifact — that is how families rot.
        # 2. Inspect the artifacts. Each detector reads files, scans
        #    paths, or examines adapter notes.
        # 3. Return self.vulnerable(...) with evidence on a positive
        #    detection, or self.passing(...) with the reasoning on a
        #    negative one.
        return self.inconclusive(
            artifacts,
            reason="template family — implement TemplateCheck before registering",
            remediation_hint="See benchprobe/families/_template.py docstring.",
        )


family = Family(
    name="template",
    formal_definition=(
        "One paragraph describing the exploit class precisely enough that a "
        "reader can independently decide whether a candidate exploit belongs "
        "to this family or to a different one."
    ),
    mitigation_class="short label for the fix class",
    severity_default=Severity.MEDIUM,
    detect=TemplateCheck(),
    citation="REQUIRED — must point at a published source.",
    reference_positive=Path("tests/reference_positive/template"),
    reference_negative=Path("tests/reference_negative/template"),
    experimental=True,
    tags=("template",),
)
