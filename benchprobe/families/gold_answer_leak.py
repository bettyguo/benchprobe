"""Family: gold-answer leak via shared filesystem.

**Formal definition.** Reference answers (gold labels, expected outputs,
solution diffs) are reachable from inside the agent's execution context
through the local filesystem at audit time. Distinguished from
``config_lookup`` by mechanism: leak is *local read*, lookup is *remote
fetch*.

**Concrete instantiations.**

1. WebArena — `config_files/{task_id}.json` contains the gold answer
   alongside the task spec, and the agent's headless Chromium can
   navigate to `file:///proc/self/cwd/config_files/{task_id}.json` to
   read it directly. ~100% on all 812 tasks. (Berkeley RDI, post 2.)
2. Several SWE-bench-like setups expose the patched test files at a
   discoverable path inside the agent's container.

**Mitigation class.** Mount reference data read-only inside a *separate*
container/process from the agent. The agent's filesystem view must not
expose any path containing gold answers — not even at a different mount
point.

**Detector strategy.** Walk ``task_config_dir`` looking for files that
contain both task-prompt-like fields and gold-answer-like fields in the
same JSON document. The signature lives in real WebArena configs:
`{"intent": "...", "eval": {"reference_answers": {...}}}`. If task and
gold co-locate in one file, the leak is reachable.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchprobe.core.check import Check, read_text_safely
from benchprobe.core.families import Family
from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Evidence, Severity, Verdict

_TASK_FIELDS = frozenset(
    {"intent", "task", "instruction", "prompt", "goal", "question"}
)
_GOLD_FIELDS = frozenset(
    {
        "eval",
        "reference_answers",
        "reference_answer",
        "expected",
        "answer",
        "gold",
        "ground_truth",
        "solution",
    }
)


def _contains_any(d: dict[str, object], keys: frozenset[str]) -> str | None:
    for key in d:
        if key in keys:
            return key
    return None


def _has_co_located_gold(payload: object) -> tuple[str, str] | None:
    """Return ``(task_key, gold_key)`` if a dict colocates task and gold."""
    if not isinstance(payload, dict):
        return None
    task_hit = _contains_any(payload, _TASK_FIELDS)
    gold_hit = _contains_any(payload, _GOLD_FIELDS)
    if task_hit and gold_hit:
        return (task_hit, gold_hit)
    return None


class GoldAnswerLeakCheck(Check):
    name = "gold_answer_leak"
    severity_default = Severity.CRITICAL

    def __call__(self, artifacts: HarnessArtifacts) -> Verdict:
        config_dir = artifacts.task_config_dir
        if config_dir is None or not config_dir.exists():
            return self.inconclusive(
                artifacts,
                reason="adapter exposed no task_config_dir to audit",
                remediation_hint=(
                    "Adapter must set `task_config_dir` so this check can "
                    "scan for task/gold co-location."
                ),
            )

        leaks: list[Evidence] = []
        scanned = 0
        for path in sorted(config_dir.rglob("*.json")):
            if scanned >= 256:
                break
            scanned += 1
            text = read_text_safely(path)
            if text is None:
                continue
            try:
                payload = json.loads(text)
            except (json.JSONDecodeError, ValueError):
                continue
            hit = _has_co_located_gold(payload)
            if hit:
                task_key, gold_key = hit
                rel = _relpath(path, artifacts.root)
                leaks.append(
                    Evidence(
                        path=str(rel),
                        snippet=(
                            f'task field "{task_key}" and gold field '
                            f'"{gold_key}" colocate in one config file'
                        ),
                    )
                )
                if len(leaks) >= 5:
                    break

        if scanned == 0:
            return self.inconclusive(
                artifacts,
                reason=f"task_config_dir {config_dir} contains no .json files",
                remediation_hint=(
                    "Verify the adapter points at the correct config directory."
                ),
            )

        if leaks:
            return self.vulnerable(
                artifacts,
                reason=(
                    f"{len(leaks)} task config(s) co-locate the task spec and the "
                    "gold answer in the same file reachable by the agent — read "
                    "by file:// navigation or an in-process file open"
                ),
                remediation_hint=(
                    "Split task spec from gold answers. Mount gold answers "
                    "read-only in the evaluator's container only, and never "
                    "expose the path on any volume the agent can read."
                ),
                evidence=tuple(leaks),
            )
        return self.passing(
            artifacts,
            reason=(
                f"scanned {scanned} task config file(s); no co-location of task "
                "spec and gold answer detected"
            ),
        )


def _relpath(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


_detect = GoldAnswerLeakCheck()

family = Family(
    name="gold_answer_leak",
    formal_definition=(
        "Reference answers are reachable from inside the agent's execution "
        "context via the local filesystem at audit time — typically because "
        "task spec and gold answer live in the same config file the agent "
        "can read."
    ),
    mitigation_class="reference-data isolation",
    severity_default=Severity.CRITICAL,
    detect=_detect,
    citation=(
        "Berkeley RDI, How We Broke Top AI Agent Benchmarks (2026): "
        "WebArena file:// navigation to config_files/{task_id}.json."
    ),
    reference_positive=Path("tests/reference_positive/gold_answer_leak"),
    reference_negative=Path("tests/reference_negative/gold_answer_leak"),
    tags=("filesystem", "answer-leakage"),
)
