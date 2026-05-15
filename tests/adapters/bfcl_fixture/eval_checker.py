"""Synthetic mirror of BFCL's eval_checker.

Loose comparison after string normalization — result_pattern_match
flags this because semantically distinct arguments can collide.
"""

from __future__ import annotations


def normalize(s: str) -> str:
    return "".join(s.split()).lower()


def matches(predicted: dict[str, str], gold: dict[str, str]) -> bool:
    return all(
        normalize(str(predicted.get(k, ""))) == normalize(str(v))
        for k, v in gold.items()
    )
