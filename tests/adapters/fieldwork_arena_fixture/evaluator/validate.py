"""Synthetic mirror of FieldWorkArena's validate().

This is the exact shape Berkeley/RDI flagged: any assistant message
scores 1.0 regardless of content. The empty_response_acceptance family
flags it because the validator never inspects the message body.
"""

from __future__ import annotations


def validate(chat_messages: list[dict[str, str]]) -> float:
    if chat_messages and chat_messages[-1]["role"] == "assistant":
        return 1.0
    return 0.0
