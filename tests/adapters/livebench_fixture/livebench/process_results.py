"""Synthetic mirror of LiveBench's results processing."""

from __future__ import annotations


def aggregate(scores: list[float]) -> float:
    return sum(scores) / max(1, len(scores))
