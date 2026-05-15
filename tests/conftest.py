"""Shared test helpers.

Fixtures here build synthetic ``HarnessArtifacts`` instances from on-disk
reference directories under ``tests/reference_positive`` and
``tests/reference_negative``. Each subdirectory is a tiny scrubbed mirror
of the shape one benchmark exposes — never real benchmark code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
POSITIVE = REPO_ROOT / "tests" / "reference_positive"
NEGATIVE = REPO_ROOT / "tests" / "reference_negative"


@pytest.fixture(scope="session")
def reference_positive_root() -> Path:
    return POSITIVE


@pytest.fixture(scope="session")
def reference_negative_root() -> Path:
    return NEGATIVE
