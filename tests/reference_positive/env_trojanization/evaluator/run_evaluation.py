# Synthetic evaluator file inside the agent-writable tree.
# A real run_evaluation.py would import pytest and invoke it on the agent's
# checkout. The detector flags the file because of where it lives, not what
# it contains.

def main() -> int:
    return 0
