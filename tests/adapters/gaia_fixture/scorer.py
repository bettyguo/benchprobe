"""Synthetic mirror of GAIA's scorer.

normalize_str's aggressive stripping enables the loose-collision
result_pattern_match family, and the public huggingface answer dataset
triggers config_lookup via the adapter's known_remote_answer_sources.
"""

import re


def normalize_str(s: str) -> str:
    return re.sub(r"[\W_]+", "", s.lower())


def score(agent_answer: str, expected: str) -> float:
    return 1.0 if normalize_str(agent_answer) == normalize_str(expected) else 0.0
