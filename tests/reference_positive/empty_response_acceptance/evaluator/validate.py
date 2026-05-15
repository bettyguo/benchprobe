"""Synthetic positive fixture for empty_response_acceptance.

Mirrors the FieldWorkArena anti-pattern: success is awarded based on
response-shape alone.
"""

from __future__ import annotations


def validate(chat_messages: list[dict]) -> float:
    if chat_messages[-1]["role"] == "assistant":
        return 1.0
    return 0.0
