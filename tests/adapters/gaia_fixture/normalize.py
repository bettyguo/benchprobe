"""Synthetic mirror of normalize.py — referenced by the GAIA adapter."""

import re


def normalize_str(s: str) -> str:
    return re.sub(r"[\W_]+", "", s.lower())
