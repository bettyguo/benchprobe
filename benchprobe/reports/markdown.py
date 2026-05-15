"""Markdown audit-report renderer.

Output is deterministic: no timestamps in the body (only in the verdicts'
``audited_at`` field, which we render in UTC ISO-8601 to second precision).
This keeps the snapshot test stable across CI runs.
"""

from __future__ import annotations

from collections.abc import Sequence

from benchprobe.core.verdict import Verdict, VerdictKind

_SYMBOL = {
    VerdictKind.PASS: "✓",
    VerdictKind.VULNERABLE: "✗",
    VerdictKind.INCONCLUSIVE: "?",
}


def render_markdown_report(verdicts: Sequence[Verdict], *, benchmark: str) -> str:
    """Render a single benchmark's per-family verdicts as Markdown."""
    n_vuln = sum(1 for v in verdicts if v.kind is VerdictKind.VULNERABLE)
    n_inc = sum(1 for v in verdicts if v.kind is VerdictKind.INCONCLUSIVE)
    n_pass = sum(1 for v in verdicts if v.kind is VerdictKind.PASS)
    overall = "PASS" if n_vuln == 0 and n_inc == 0 else "FAIL"

    lines: list[str] = []
    lines.append(f"# benchprobe audit: {benchmark}")
    lines.append("")
    lines.append(
        f"**Overall:** {overall} — "
        f"{n_pass} pass / {n_vuln} vulnerable / {n_inc} inconclusive"
    )
    lines.append("")
    lines.append("| Family | Verdict | Severity | Reason |")
    lines.append("| --- | --- | --- | --- |")
    for v in verdicts:
        symbol = _SYMBOL[v.kind]
        reason = v.reason.replace("|", "\\|")
        lines.append(
            f"| `{v.family}` | {symbol} {v.kind.value} | {v.severity.value} | {reason} |"
        )
    lines.append("")

    for v in verdicts:
        if v.kind is VerdictKind.PASS:
            continue
        lines.append(f"## `{v.family}` — {v.kind.value}")
        lines.append("")
        lines.append(f"**Reason.** {v.reason}")
        lines.append("")
        lines.append(f"**Remediation.** {v.remediation_hint}")
        if v.evidence:
            lines.append("")
            lines.append("**Evidence.**")
            for e in v.evidence:
                snippet = e.snippet.replace("\n", " ").strip()
                line_part = f":{e.line}" if e.line else ""
                lines.append(f"- `{e.path}{line_part}` — {snippet}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
