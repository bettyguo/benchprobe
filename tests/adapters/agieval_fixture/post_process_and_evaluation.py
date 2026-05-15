"""Synthetic mirror of AGIEval's post-processing + evaluation."""

from __future__ import annotations

import re


def extract(text: str) -> str:
    match = re.search(r"answer[:\s]+([A-D]|\d+)", text, re.IGNORECASE)
    return match.group(1) if match else ""


def score(answer: str, gold: str) -> float:
    return 1.0 if extract(answer).strip().lower() == gold.strip().lower() else 0.0
