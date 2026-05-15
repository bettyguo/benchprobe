"""Evaluator that runs pytest with `--no-conftest` so agent hooks don't load.

The adapter notes for this fixture declare confcutdir enforcement,
which the detector reads to downgrade the verdict to PASS.
"""

import subprocess
import sys


def main() -> int:
    return subprocess.call(
        [sys.executable, "-m", "pytest", "--no-conftest", "--confcutdir=evaluator"]
    )
