"""Synthetic negative fixture: content-aware validator."""

from __future__ import annotations


def validate(chat_messages: list[dict], gold_answer: str) -> float:
    if not chat_messages:
        return 0.0
    last = chat_messages[-1]
    if last.get("role") != "assistant":
        return 0.0
    content = (last.get("content") or "").strip()
    if not content:
        return 0.0
    return 1.0 if content == gold_answer else 0.0
