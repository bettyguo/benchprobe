"""Evaluator that just shells out to pytest in the agent tree.

(In a real harness this would be more elaborate. For the detector it
suffices that the evaluator runs pytest where the agent tree is rooted.)
"""

import subprocess
import sys


def main() -> int:
    return subprocess.call([sys.executable, "-m", "pytest", "agent_tree/"])
