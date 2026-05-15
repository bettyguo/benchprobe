"""Synthetic Terminal-Bench checker.

Two anti-patterns relevant to the auditor:
- Existence-only validation (wrapper_no_op).
- A trivial empty-response acceptance branch (empty_response_acceptance).
"""

import os.path


def check(workdir: str, response: str) -> int:
    if os.path.exists(workdir + "/result.txt"):
        return 1
    if response:
        return 1
    return 0
