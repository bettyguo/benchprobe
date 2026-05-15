"""Synthetic OSWorld evaluator.

Mirrors the shape that triggers config_lookup: the evaluator reads gold
outputs from disk after the VM may have downloaded them from a public
HuggingFace URL.
"""

import os.path


def evaluate(workdir: str, gold_path: str) -> float:
    if not os.path.exists(workdir + "/output.xlsx"):
        return 0.0
    with open(workdir + "/output.xlsx", "rb") as actual, open(gold_path, "rb") as gold:
        return 1.0 if actual.read() == gold.read() else 0.0
