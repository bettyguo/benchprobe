"""Synthetic mirror of HumanEval's evaluation entry point."""

from __future__ import annotations


def evaluate_functional_correctness(sample_file: str) -> dict[str, float]:
    return {"pass@1": 0.0}
