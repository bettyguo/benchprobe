"""Synthetic evaluator mirroring WebArena's matching shape."""

import re


def evaluate_substring(rendered_html: str, must_include: list[str]) -> float:
    for needle in must_include:
        if needle in rendered_html:
            return 1.0
    return 0.0


def evaluate_regex(rendered_html: str, pattern: str) -> float:
    return 1.0 if re.search(pattern, rendered_html) else 0.0


def evaluate_unsafe(agent_output: str):
    # Anti-pattern present in some early WebArena evaluator variants.
    return eval(agent_output)
