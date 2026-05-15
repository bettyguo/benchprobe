"""Synthetic conftest demonstrating the assertion-rewrite shape.

This is a fixture, not an exploit. It exists so the detector has
something to flag.
"""

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    # Vulnerable shape: rewriting the outcome unconditionally.
    if report.when == "call":
        report.outcome = "passed"
