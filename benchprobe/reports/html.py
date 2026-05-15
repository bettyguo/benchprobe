"""HTML audit-report renderer.

Single self-contained HTML file with inline CSS so it can be stored next
to ``data.json`` or attached to a PR without a build step.
"""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

from benchprobe.core.verdict import Verdict, VerdictKind

_SYMBOL = {
    VerdictKind.PASS: ("pass", "PASS"),
    VerdictKind.VULNERABLE: ("vuln", "VULNERABLE"),
    VerdictKind.INCONCLUSIVE: ("inc", "INCONCLUSIVE"),
}

_CSS = """
body { font-family: -apple-system, system-ui, sans-serif; max-width: 920px; margin: 2em auto; padding: 0 1em; color: #1d1f21; }
h1 { border-bottom: 1px solid #d0d0d0; padding-bottom: .25em; }
table { border-collapse: collapse; width: 100%; margin-bottom: 2em; }
th, td { border: 1px solid #d0d0d0; padding: .4em .6em; text-align: left; vertical-align: top; }
th { background: #f6f8fa; }
.pass { color: #117a3a; font-weight: 600; }
.vuln { color: #b3261e; font-weight: 600; }
.inc  { color: #8a6d00; font-weight: 600; }
.family-block { margin-bottom: 2em; }
.family-block h2 { margin-bottom: .25em; }
.evidence { background: #f6f8fa; padding: .4em .6em; border-left: 3px solid #999; font-family: ui-monospace, monospace; font-size: 90%; white-space: pre-wrap; }
code { background: #f6f8fa; padding: 1px 4px; border-radius: 3px; }
"""


def render_html_report(verdicts: Sequence[Verdict], *, benchmark: str) -> str:
    n_vuln = sum(1 for v in verdicts if v.kind is VerdictKind.VULNERABLE)
    n_inc = sum(1 for v in verdicts if v.kind is VerdictKind.INCONCLUSIVE)
    n_pass = sum(1 for v in verdicts if v.kind is VerdictKind.PASS)
    overall_class, overall_text = (
        ("pass", "PASS") if n_vuln == 0 and n_inc == 0 else ("vuln", "FAIL")
    )

    rows: list[str] = []
    for v in verdicts:
        cls, label = _SYMBOL[v.kind]
        rows.append(
            "<tr>"
            f"<td><code>{escape(v.family)}</code></td>"
            f"<td class='{cls}'>{label}</td>"
            f"<td>{escape(v.severity.value)}</td>"
            f"<td>{escape(v.reason)}</td>"
            "</tr>"
        )

    detail_blocks: list[str] = []
    for v in verdicts:
        if v.kind is VerdictKind.PASS:
            continue
        evidence_html = ""
        if v.evidence:
            ev_lines = "\n".join(
                f"{escape(e.path)}{':' + str(e.line) if e.line else ''} — {escape(e.snippet)}"
                for e in v.evidence
            )
            evidence_html = f"<div class='evidence'>{ev_lines}</div>"
        cls, label = _SYMBOL[v.kind]
        detail_blocks.append(
            "<div class='family-block'>"
            f"<h2><code>{escape(v.family)}</code> — <span class='{cls}'>{label}</span></h2>"
            f"<p><b>Reason.</b> {escape(v.reason)}</p>"
            f"<p><b>Remediation.</b> {escape(v.remediation_hint)}</p>"
            f"{evidence_html}"
            "</div>"
        )

    return (
        "<!doctype html>\n"
        "<html lang='en'>\n<head>\n"
        f"<meta charset='utf-8'><title>benchprobe audit: {escape(benchmark)}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>\n"
        f"<h1>benchprobe audit: {escape(benchmark)}</h1>\n"
        f"<p><b>Overall:</b> <span class='{overall_class}'>{overall_text}</span> — "
        f"{n_pass} pass / {n_vuln} vulnerable / {n_inc} inconclusive</p>\n"
        "<table><thead><tr><th>Family</th><th>Verdict</th><th>Severity</th><th>Reason</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>\n"
        f"{''.join(detail_blocks)}"
        "</body></html>\n"
    )
