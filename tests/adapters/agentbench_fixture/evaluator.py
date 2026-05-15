"""Synthetic mirror of AgentBench's evaluator."""

from __future__ import annotations


def grade(submission: dict[str, str], task: dict[str, str]) -> float:
    return 1.0 if submission.get("answer") == task.get("answer") else 0.0
