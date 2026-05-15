"""Synthetic mirror of swebench/harness/run_evaluation.py.

Real SWE-bench runs pytest inside the agent's repo checkout. The audit
flags this layout because ``evaluator_paths`` overlap with
``agent_writable_paths``.
"""

import subprocess
import sys


def run() -> int:
    return subprocess.call([sys.executable, "-m", "pytest", "testbed/"])
