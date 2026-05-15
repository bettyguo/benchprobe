"""Synthetic mirror of MMLU's scorer.

Substring extraction over the agent's free-text answer. result_pattern_match
flags this because the matched content can be hidden anywhere in the
agent-controlled output.
"""

from __future__ import annotations

import re


def extract_choice(text: str) -> str | None:
    match = re.search(r"\b([A-D])\b", text)
    return match.group(1) if match else None


def score(answer: str, gold: str) -> float:
    return 1.0 if extract_choice(answer) == gold else 0.0
