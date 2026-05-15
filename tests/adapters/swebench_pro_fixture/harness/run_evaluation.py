"""Synthetic mirror of SWE-bench Pro's run_evaluation.

The harness reads ``workspace/parser.py`` after the agent's run, so any
agent-supplied parser replacement is the source of truth — flagged by
the assertion_rewrite family because the agent-writable tree contains
the parser.
"""

from __future__ import annotations

from pathlib import Path


def run(workspace: Path) -> int:
    parser_path = workspace / "parser.py"
    if not parser_path.exists():
        return 1
    return 0
