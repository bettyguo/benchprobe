"""Synthetic mirror of SWE-bench Pro's workspace parser.

The agent's workspace is a write-able tree. The parser lives in it, so
the agent can overwrite the parser before the harness invokes it —
this is the assertion_rewrite shape Berkeley/RDI documented.
"""

from __future__ import annotations


def parse_test_log(text: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for line in text.splitlines():
        if " PASSED " in line or " FAILED " in line:
            status = "PASSED" if " PASSED " in line else "FAILED"
            out.append({"line": line, "status": status})
    return out
