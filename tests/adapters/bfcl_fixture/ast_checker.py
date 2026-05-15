"""Synthetic mirror of BFCL's AST checker."""

from __future__ import annotations

import ast


def parse_call(text: str) -> ast.Call | None:
    tree = ast.parse(text, mode="eval")
    body = tree.body
    return body if isinstance(body, ast.Call) else None
