"""Renderer tests."""

from __future__ import annotations

from datetime import UTC, datetime

from benchprobe.core.verdict import Evidence, Severity, Verdict, VerdictKind
from benchprobe.reports import render_html_report, render_markdown_report


def _verdict(kind: VerdictKind, family: str = "f") -> Verdict:
    return Verdict(
        family=family,
        benchmark="b",
        kind=kind,
        severity=Severity.HIGH,
        reason=f"reason for {family}",
        remediation_hint="do X",
        evidence=(Evidence(path="foo/bar.py", snippet="line"),),
        audited_at=datetime(2026, 5, 14, tzinfo=UTC),
    )


def test_markdown_report_lists_every_family() -> None:
    md = render_markdown_report(
        [_verdict(VerdictKind.PASS, "a"), _verdict(VerdictKind.VULNERABLE, "b")],
        benchmark="b",
    )
    assert "| `a` |" in md
    assert "| `b` |" in md
    assert "FAIL" in md
    assert "Remediation" in md


def test_markdown_report_overall_pass_when_all_pass() -> None:
    md = render_markdown_report(
        [_verdict(VerdictKind.PASS), _verdict(VerdictKind.PASS, "g")],
        benchmark="b",
    )
    assert "**Overall:** PASS" in md


def test_html_report_renders_table_and_details() -> None:
    html = render_html_report(
        [_verdict(VerdictKind.VULNERABLE), _verdict(VerdictKind.PASS, "g")],
        benchmark="b",
    )
    assert "<table>" in html
    assert "foo/bar.py" in html
    assert "VULNERABLE" in html
