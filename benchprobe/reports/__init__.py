"""Audit-report renderers (markdown, html)."""

from benchprobe.reports.html import render_html_report
from benchprobe.reports.markdown import render_markdown_report

__all__ = ["render_html_report", "render_markdown_report"]
