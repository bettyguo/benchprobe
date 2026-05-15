"""Synthetic mirror of CAR-bench's reward computation.

Three of four reward components return zero delta on hallucination
tasks where the agent refuses. The empty_response_acceptance family
flags this because a content-free refusal dodges every firing
component.
"""

from __future__ import annotations


def policy_followed(messages: list[dict[str, str]]) -> float:
    return 1.0 if messages and messages[-1]["role"] == "assistant" else 0.0


def state_match(_: object) -> float:
    return 0.0


def tool_subset(_: object) -> float:
    return 0.0


def compute_reward(messages: list[dict[str, str]]) -> float:
    return policy_followed(messages) + state_match(None) + tool_subset(None)
