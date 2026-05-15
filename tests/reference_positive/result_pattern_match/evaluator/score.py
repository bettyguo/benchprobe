"""Synthetic positive: substring match + eval() on agent output."""

from __future__ import annotations


def score(agent_output: str, must_include: list[str]) -> float:
    for needle in must_include:
        if needle in agent_output:
            return 1.0
    return 0.0


def parse_structured(agent_output: str):
    # Anti-pattern documented by Berkeley RDI: eval()ing agent output.
    return eval(agent_output)
