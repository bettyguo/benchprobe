"""Synthetic positive: passes purely on file existence.

Mirrors the Terminal-Bench fake-.so anti-pattern.
"""

import os.path


def check_solution(workdir: str) -> int:
    if os.path.exists(workdir + "/mylib.so"):
        return 1
    return 0
