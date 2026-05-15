"""Exploit family implementations.

Importing this package registers every shipped family on
``benchprobe.core.family_registry``. v0.1 ships eight families; the
contributor template (``_template.py``) is *not* registered — it is a
scaffold for new contributions.
"""

from benchprobe.core.families import family_registry
from benchprobe.families.assertion_rewrite import family as assertion_rewrite_family
from benchprobe.families.config_lookup import family as config_lookup_family
from benchprobe.families.empty_response_acceptance import family as empty_response_acceptance_family
from benchprobe.families.env_trojanization import family as env_trojanization_family
from benchprobe.families.gold_answer_leak import family as gold_answer_leak_family
from benchprobe.families.judge_prompt_injection import family as judge_prompt_injection_family
from benchprobe.families.result_pattern_match import family as result_pattern_match_family
from benchprobe.families.wrapper_no_op import family as wrapper_no_op_family

for _family in (
    env_trojanization_family,
    gold_answer_leak_family,
    judge_prompt_injection_family,
    empty_response_acceptance_family,
    config_lookup_family,
    assertion_rewrite_family,
    wrapper_no_op_family,
    result_pattern_match_family,
):
    family_registry.register(_family)

__all__ = [
    "assertion_rewrite_family",
    "config_lookup_family",
    "empty_response_acceptance_family",
    "env_trojanization_family",
    "gold_answer_leak_family",
    "judge_prompt_injection_family",
    "result_pattern_match_family",
    "wrapper_no_op_family",
]
