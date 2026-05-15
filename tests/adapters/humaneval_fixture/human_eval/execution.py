"""Synthetic mirror of HumanEval's execution module.

HumanEval execs agent-supplied code in a process whose namespace the
agent controls. The assertion_rewrite family treats the submission as
an agent-writable tree colocated with the evaluator's import path.
"""

from __future__ import annotations


def check_correctness(problem: dict[str, str], completion: str) -> dict[str, object]:
    return {"passed": False, "result": "stub"}
