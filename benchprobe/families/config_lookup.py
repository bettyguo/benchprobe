"""Family: config-driven remote answer lookup.

**Formal definition.** The task configuration contains, or references via
a network-reachable URL, the gold answer for that task; the agent's
runtime environment has the network access required to fetch it.
Distinguished from ``gold_answer_leak``: that family is a *local* read,
this one is a *remote* fetch.

**Concrete instantiations.**

1. GAIA — validation answers are hosted on a public HuggingFace dataset
   URL; the agent loads them at runtime before submitting. Compounded by
   `normalize_str()` stripping whitespace and punctuation.
2. OSWorld — task instructions or VM environment include URLs to gold
   outputs (e.g. ``https://huggingface.co/.../gold.xlsx``); the agent
   wgets the file straight into the evaluator-expected output path.

**Mitigation class.** Reference data must not be reachable from the
agent's network. Either run the agent offline or filter outbound traffic
to a strict allowlist that excludes the reference-hosting domains.

**Detector strategy.** Look at the adapter's
``known_remote_answer_sources``: if the adapter has documented that
reference data is hosted at a public URL, the family is by definition
reachable unless the adapter explicitly notes a network filter. Then
secondarily scan task configs for URLs matching common gold-hosting
domains (huggingface.co, github raw, gist) — those flag undocumented
exposure.
"""

from __future__ import annotations

import re
from pathlib import Path

from benchprobe.core.check import Check, read_text_safely, snippet_around
from benchprobe.core.families import Family
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Evidence, Severity, Verdict

_GOLD_HOST_RE = re.compile(
    r"https?://("
    r"huggingface\.co|raw\.githubusercontent\.com|gist\.githubusercontent\.com|"
    r"drive\.google\.com|dropbox\.com"
    r")/[^\s\"']+",
    re.IGNORECASE,
)

_NETWORK_FILTER_KEYWORDS = ("offline", "allowlist", "network filter", "no internet", "egress")


class ConfigLookupCheck(Check):
    name = "config_lookup"
    severity_default = Severity.CRITICAL

    def __call__(self, artifacts: HarnessArtifacts) -> Verdict:
        config_dir = artifacts.task_config_dir
        notes_blob = " ".join(artifacts.notes).lower()
        has_filter = any(k in notes_blob for k in _NETWORK_FILTER_KEYWORDS)

        if artifacts.known_remote_answer_sources and not has_filter:
            return self.vulnerable(
                artifacts,
                reason=(
                    f"{len(artifacts.known_remote_answer_sources)} remote "
                    "answer source(s) declared by adapter; adapter notes "
                    "do not declare a network filter on the agent runtime"
                ),
                remediation_hint=(
                    "Run the agent without network access, or apply an "
                    "egress allowlist that excludes the reference-hosting "
                    "domains. Either way, the agent's environment must "
                    "not be able to GET the gold answer file."
                ),
                evidence=tuple(
                    Evidence(path=url, snippet="documented remote answer source")
                    for url in artifacts.known_remote_answer_sources[:5]
                ),
            )

        if config_dir is None or not config_dir.exists():
            if artifacts.known_remote_answer_sources and has_filter:
                return self.passing(
                    artifacts,
                    reason=(
                        "remote answer sources declared but adapter notes "
                        "describe a network filter restricting agent egress"
                    ),
                )
            return self.inconclusive(
                artifacts,
                reason=(
                    "no task_config_dir to scan and no remote answer sources "
                    "declared"
                ),
                remediation_hint=(
                    "Adapter must set `task_config_dir` or "
                    "`known_remote_answer_sources` so this check can run."
                ),
            )

        hits: list[Evidence] = []
        scanned = 0
        for path in sorted(config_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".json", ".yaml", ".yml", ".txt", ".md"}:
                continue
            if scanned >= 256:
                break
            scanned += 1
            text = read_text_safely(path)
            if text is None:
                continue
            for match in _GOLD_HOST_RE.finditer(text):
                rel = _relpath(path, artifacts.root)
                hits.append(
                    Evidence(
                        path=str(rel),
                        snippet=snippet_around(text, match.start(), width=160),
                    )
                )
                if len(hits) >= 5:
                    break
            if len(hits) >= 5:
                break

        if hits:
            return self.vulnerable(
                artifacts,
                reason=(
                    f"{len(hits)} task config(s) reference public hosting "
                    "URLs that could contain gold answers; agent runtime "
                    "without an egress filter can fetch them"
                ),
                remediation_hint=(
                    "Strip reference-data URLs from task configs that ship "
                    "to the agent. If the URLs are intentional, run the "
                    "agent behind an egress allowlist that excludes those "
                    "hosts and ship the filter config alongside the "
                    "evaluator."
                ),
                evidence=tuple(hits),
            )
        return self.passing(
            artifacts,
            reason=(
                f"scanned {scanned} config file(s); no public answer-hosting "
                "URLs detected and adapter declares no remote answer sources"
            ),
        )


def _relpath(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


_detect = ConfigLookupCheck()

family = Family(
    name="config_lookup",
    formal_definition=(
        "The task configuration or runtime environment references a "
        "network-reachable URL containing the gold answer, and the agent's "
        "runtime has the egress to fetch it before submitting."
    ),
    mitigation_class="agent-egress isolation",
    severity_default=Severity.CRITICAL,
    detect=_detect,
    citation=(
        "Berkeley RDI, How We Broke Top AI Agent Benchmarks (2026): "
        "GAIA HuggingFace answer-file load; OSWorld wget of gold.xlsx."
    ),
    reference_positive=Path("tests/reference_positive/config_lookup"),
    reference_negative=Path("tests/reference_negative/config_lookup"),
    tags=("network", "answer-leakage"),
)
