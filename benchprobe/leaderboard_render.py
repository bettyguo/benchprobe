"""Render ``leaderboard/data.json`` to a publication-quality static site.

Output is a single self-contained ``index.html`` plus a styles file:
no CDN dependencies, no tracking, no required JavaScript for the core
table. Vanilla JS adds sortable columns, a text filter, expandable
cell-detail rows, and a BibTeX copy button — but the page is fully
readable with JavaScript disabled.

Design goals: dense data + restrained typography + multi-modal verdict
encoding (color *and* glyph *and* text) so the leaderboard is
accessible, printable, and citation-worthy.
"""

from __future__ import annotations

import datetime as _dt
import json
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

from benchprobe.core.families import Family
from benchprobe.core.leaderboard import LeaderboardStore
from benchprobe.core.verdict import VerdictKind

if TYPE_CHECKING:
    from benchprobe.core.leaderboard import LeaderboardEntry


# ---------------------------------------------------------------------------
# Verdict presentation
# ---------------------------------------------------------------------------

_GLYPH: dict[VerdictKind, str] = {
    VerdictKind.PASS: "✓",
    VerdictKind.VULNERABLE: "✗",
    VerdictKind.INCONCLUSIVE: "◐",
}
_LABEL: dict[VerdictKind, str] = {
    VerdictKind.PASS: "pass",
    VerdictKind.VULNERABLE: "vulnerable",
    VerdictKind.INCONCLUSIVE: "inconclusive",
}
_CLASS: dict[VerdictKind, str] = {
    VerdictKind.PASS: "v-pass",
    VerdictKind.VULNERABLE: "v-vuln",
    VerdictKind.INCONCLUSIVE: "v-inc",
}


# ---------------------------------------------------------------------------
# Static assets — embedded so the site is self-contained
# ---------------------------------------------------------------------------

_STYLES = """
:root {
  --bg: #faf9f6;
  --surface: #ffffff;
  --ink: #1a1a1a;
  --ink-muted: #5a5a5a;
  --ink-faint: #8a8a8a;
  --rule: #d8d6cf;
  --rule-strong: #b8b6af;
  --accent: #2a3a5f;
  --pass: #1d6a3f;
  --pass-bg: #e7f1ea;
  --vuln: #a4282d;
  --vuln-bg: #f5e0e1;
  --inc: #8a6d00;
  --inc-bg: #f6efd4;
  --code-bg: #f3f1ea;
  --sans: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --serif: "Source Serif 4", "Source Serif Pro", "Charter", "Iowan Old Style", "Baskerville", "Times New Roman", Times, serif;
  --mono: ui-monospace, "JetBrains Mono", "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--serif);
  font-size: 16px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
main { max-width: 1240px; margin: 0 auto; padding: 0 24px 64px; }

/* Masthead -------------------------------------------------------------- */
header.masthead {
  border-bottom: 2px solid var(--ink);
  padding: 28px 0 18px;
  margin-bottom: 28px;
}
.kicker {
  font-family: var(--sans);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-muted);
  margin: 0 0 6px;
}
h1.title {
  font-family: var(--serif);
  font-weight: 700;
  font-size: clamp(28px, 4vw, 44px);
  line-height: 1.1;
  margin: 0 0 8px;
  letter-spacing: -0.01em;
}
.subtitle {
  font-family: var(--serif);
  font-style: italic;
  color: var(--ink-muted);
  margin: 0 0 14px;
  font-size: 18px;
}
.metaline {
  font-family: var(--sans);
  font-size: 13px;
  color: var(--ink-muted);
  display: flex;
  flex-wrap: wrap;
  gap: 16px 22px;
  align-items: baseline;
}
.metaline strong { color: var(--ink); font-weight: 600; }
.metaline a { color: var(--accent); text-decoration: none; border-bottom: 1px solid currentColor; }

/* Summary cards --------------------------------------------------------- */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin: 0 0 32px;
}
.card {
  background: var(--surface);
  border: 1px solid var(--rule);
  padding: 14px 16px 12px;
}
.card-label {
  font-family: var(--sans);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-faint);
  margin: 0 0 4px;
}
.card-value {
  font-family: var(--serif);
  font-size: 30px;
  font-weight: 700;
  line-height: 1;
  margin: 0;
}
.card-note {
  font-family: var(--sans);
  font-size: 12px;
  color: var(--ink-muted);
  margin: 4px 0 0;
}

/* Section primitives ---------------------------------------------------- */
section { margin: 40px 0; }
h2 {
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--rule-strong);
}
section > p.lede {
  font-family: var(--serif);
  font-size: 16px;
  color: var(--ink-muted);
  margin: 6px 0 18px;
  max-width: 780px;
}

/* Heatmap --------------------------------------------------------------- */
.heatmap-wrap {
  background: var(--surface);
  border: 1px solid var(--rule);
  padding: 16px;
  overflow-x: auto;
}
svg.heatmap { display: block; }
svg.heatmap text { font-family: var(--sans); }

/* Controls -------------------------------------------------------------- */
.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin: 0 0 12px;
  font-family: var(--sans);
  font-size: 13px;
  color: var(--ink-muted);
}
.controls input[type="search"] {
  flex: 0 1 280px;
  padding: 6px 10px;
  border: 1px solid var(--rule-strong);
  background: var(--surface);
  font-family: var(--sans);
  font-size: 13px;
}
.controls input[type="search"]:focus {
  outline: 2px solid var(--accent);
  outline-offset: 0;
}
.legend { display: flex; gap: 14px; align-items: center; }
.legend .swatch {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.swatch-chip {
  display: inline-block;
  width: 14px; height: 14px;
  border: 1px solid var(--rule-strong);
  text-align: center;
  line-height: 12px;
  font-size: 11px;
  font-family: var(--sans);
  font-weight: 600;
}

/* Leaderboard table ----------------------------------------------------- */
.table-wrap { overflow-x: auto; border: 1px solid var(--rule); background: var(--surface); }
table.lb {
  border-collapse: collapse;
  width: 100%;
  font-family: var(--sans);
  font-size: 13px;
  min-width: 1100px;
}
table.lb thead th {
  position: sticky;
  top: 0;
  background: var(--surface);
  border-bottom: 2px solid var(--ink);
  padding: 10px 8px;
  text-align: left;
  vertical-align: bottom;
  font-weight: 600;
  color: var(--ink);
  user-select: none;
  white-space: nowrap;
}
table.lb thead th.fam {
  text-align: center;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0;
  writing-mode: horizontal-tb;
  min-width: 84px;
}
table.lb thead th.sortable { cursor: pointer; }
table.lb thead th.sortable:hover { color: var(--accent); }
table.lb thead th.sortable::after {
  content: " ⇅";
  color: var(--ink-faint);
  font-size: 10px;
}
table.lb thead th.sort-asc::after { content: " ↑"; color: var(--ink); }
table.lb thead th.sort-desc::after { content: " ↓"; color: var(--ink); }
table.lb tbody td {
  padding: 8px;
  border-top: 1px solid var(--rule);
  vertical-align: middle;
}
table.lb tbody tr:nth-child(4n+1) td { background: rgba(216, 214, 207, 0.18); }
table.lb tbody tr.detail-row td {
  background: var(--surface) !important;
  border-top: 1px solid var(--rule);
}
table.lb tbody td.bench {
  font-family: var(--serif);
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
}
table.lb tbody td.sha {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-muted);
}
table.lb tbody td.audited {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-muted);
  white-space: nowrap;
}
table.lb tbody td.overall {
  font-family: var(--sans);
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
table.lb tbody td.cell {
  text-align: center;
  cursor: pointer;
  font-family: var(--sans);
  font-weight: 600;
  width: 84px;
  position: relative;
}
.cell.v-pass { background: var(--pass-bg); color: var(--pass); }
.cell.v-vuln { background: var(--vuln-bg); color: var(--vuln); }
.cell.v-inc  { background: var(--inc-bg);  color: var(--inc); }
.cell .glyph { display: block; font-size: 16px; line-height: 1; }
.cell .lbl   { display: block; font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 2px; opacity: 0.85; }
td.overall.v-pass { color: var(--pass); }
td.overall.v-vuln { color: var(--vuln); }
td.overall.v-inc  { color: var(--inc); }

/* Detail row ------------------------------------------------------------ */
.detail {
  padding: 16px 20px;
  background: var(--surface);
  border-left: 3px solid var(--accent);
  font-family: var(--sans);
  font-size: 13px;
  line-height: 1.6;
}
.detail h4 {
  font-family: var(--serif);
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 6px;
}
.detail .meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 18px;
  margin: 0 0 10px;
  color: var(--ink-muted);
}
.detail .meta b { color: var(--ink); font-weight: 600; }
.detail dl { margin: 6px 0 0; }
.detail dt { font-weight: 600; margin-top: 8px; }
.detail dd { margin: 0 0 4px; color: var(--ink-muted); }
.detail code { font-family: var(--mono); background: var(--code-bg); padding: 1px 4px; font-size: 12px; }
.detail .pill {
  display: inline-block;
  padding: 1px 8px;
  border: 1px solid currentColor;
  border-radius: 2px;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-weight: 600;
}

/* Methodology section --------------------------------------------------- */
.fam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}
.fam-card {
  background: var(--surface);
  border: 1px solid var(--rule);
  padding: 16px 18px;
}
.fam-card h3 {
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--accent);
}
.fam-card .sev { font-family: var(--sans); font-size: 11px; color: var(--ink-muted); letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 8px; }
.fam-card p { font-family: var(--serif); font-size: 14px; margin: 0 0 8px; }
.fam-card dl { font-family: var(--sans); font-size: 12px; color: var(--ink-muted); margin: 0; }
.fam-card dt { font-weight: 600; color: var(--ink); }
.fam-card dd { margin: 0 0 6px; }

/* Citation -------------------------------------------------------------- */
.cite-wrap { background: var(--surface); border: 1px solid var(--rule); }
.cite-wrap pre {
  margin: 0;
  padding: 16px 18px;
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
}
.cite-wrap .copy-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  border-top: 1px solid var(--rule);
  font-family: var(--sans);
  font-size: 12px;
  color: var(--ink-muted);
}
button.copy {
  font-family: var(--sans);
  font-size: 12px;
  padding: 4px 10px;
  border: 1px solid var(--rule-strong);
  background: var(--bg);
  cursor: pointer;
}
button.copy:hover { border-color: var(--ink); }
button.copy:active { background: var(--rule); }
button.copy.copied { border-color: var(--pass); color: var(--pass); }

/* Footer ---------------------------------------------------------------- */
footer.site {
  margin-top: 56px;
  padding-top: 16px;
  border-top: 1px solid var(--rule-strong);
  font-family: var(--sans);
  font-size: 12px;
  color: var(--ink-muted);
  display: flex;
  flex-wrap: wrap;
  gap: 10px 24px;
  justify-content: space-between;
}
footer.site a { color: var(--accent); text-decoration: none; border-bottom: 1px solid currentColor; }

/* Responsive ------------------------------------------------------------ */
@media (max-width: 720px) {
  main { padding: 0 16px 48px; }
  h1.title { font-size: 28px; }
  .cards { grid-template-columns: repeat(2, 1fr); }
  table.lb { font-size: 12px; }
}

/* Print ----------------------------------------------------------------- */
@media print {
  body { background: #fff; color: #000; }
  .controls, button.copy, footer.site .source { display: none; }
  .detail-row { display: none; }
  table.lb thead th { position: static; }
  .cards { break-inside: avoid; }
  .fam-card { break-inside: avoid; }
  a { color: #000; }
}

/* Reduced motion -------------------------------------------------------- */
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
}
"""


_SCRIPT = """
(function () {
  // ----- sortable -----------------------------------------------------
  const table = document.querySelector('table.lb');
  if (!table) return;
  const tbody = table.tBodies[0];

  function rowGroups() {
    // Each "logical row" is a primary row plus its hidden detail row.
    const groups = [];
    Array.from(tbody.rows).forEach(r => {
      if (r.classList.contains('detail-row')) {
        if (groups.length) groups[groups.length - 1].push(r);
      } else {
        groups.push([r]);
      }
    });
    return groups;
  }

  function sortBy(idx, key, dir) {
    const groups = rowGroups();
    groups.sort((a, b) => {
      const av = a[0].dataset[key] ?? a[0].cells[idx]?.innerText ?? '';
      const bv = b[0].dataset[key] ?? b[0].cells[idx]?.innerText ?? '';
      const na = parseFloat(av), nb = parseFloat(bv);
      let cmp;
      if (!isNaN(na) && !isNaN(nb)) cmp = na - nb;
      else cmp = String(av).localeCompare(String(bv));
      return dir === 'desc' ? -cmp : cmp;
    });
    groups.forEach(g => g.forEach(r => tbody.appendChild(r)));
  }

  table.querySelectorAll('thead th.sortable').forEach((th, i) => {
    th.addEventListener('click', () => {
      const cur = th.classList.contains('sort-asc') ? 'asc' :
                  th.classList.contains('sort-desc') ? 'desc' : null;
      const next = cur === 'asc' ? 'desc' : 'asc';
      table.querySelectorAll('thead th').forEach(x => {
        x.classList.remove('sort-asc', 'sort-desc');
      });
      th.classList.add(next === 'asc' ? 'sort-asc' : 'sort-desc');
      sortBy(i, th.dataset.sortKey || '', next);
    });
  });

  // ----- filter -------------------------------------------------------
  const filter = document.getElementById('lb-filter');
  if (filter) {
    filter.addEventListener('input', () => {
      const q = filter.value.trim().toLowerCase();
      rowGroups().forEach(g => {
        const text = g[0].innerText.toLowerCase();
        const visible = !q || text.includes(q);
        g.forEach(r => {
          if (r.classList.contains('detail-row')) {
            // keep detail rows hidden by default; filter only main rows.
            r.style.display = (visible && r.dataset.open === '1') ? '' : 'none';
          } else {
            r.style.display = visible ? '' : 'none';
          }
        });
      });
    });
  }

  // ----- cell expand --------------------------------------------------
  tbody.querySelectorAll('td.cell').forEach(td => {
    td.setAttribute('role', 'button');
    td.setAttribute('tabindex', '0');
    td.setAttribute('aria-expanded', 'false');
    function toggle() {
      const fam = td.dataset.family;
      const row = td.parentElement;
      const detail = row.nextElementSibling;
      if (!detail || !detail.classList.contains('detail-row')) return;
      const cell = detail.querySelector('td');
      const panels = cell.querySelectorAll('.detail');
      let opened = false;
      panels.forEach(p => {
        if (p.dataset.family === fam) {
          const isOpen = p.style.display !== 'none' && p.style.display !== '';
          panels.forEach(q => { q.style.display = 'none'; });
          if (!isOpen) { p.style.display = 'block'; opened = true; }
        }
      });
      detail.dataset.open = opened ? '1' : '0';
      detail.style.display = opened ? '' : 'none';
      td.setAttribute('aria-expanded', opened ? 'true' : 'false');
    }
    td.addEventListener('click', toggle);
    td.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    });
  });

  // ----- copy bibtex --------------------------------------------------
  const copyBtn = document.querySelector('button.copy');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      const pre = document.querySelector('.cite-wrap pre');
      if (!pre) return;
      const text = pre.innerText;
      const done = () => {
        copyBtn.classList.add('copied');
        copyBtn.textContent = 'Copied';
        setTimeout(() => {
          copyBtn.classList.remove('copied');
          copyBtn.textContent = 'Copy BibTeX';
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, () => {});
      } else {
        const r = document.createRange();
        r.selectNodeContents(pre);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(r);
        try { document.execCommand('copy'); done(); } catch (e) {}
      }
    });
  }
})();
"""


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _ordered_families(store: LeaderboardStore) -> list[str]:
    seen: list[str] = []
    for entry in store.entries:
        for fam in entry.family_verdicts:
            if fam not in seen:
                seen.append(fam)
    seen.sort()
    return seen


def _family_meta() -> dict[str, Family]:
    """Look up family metadata at render time; survives an empty registry."""
    try:
        # Imports the families package, which registers every shipped family
        # on the shared registry as a side effect.
        import benchprobe.families  # noqa: F401
        from benchprobe.core.families import family_registry
    except Exception:
        return {}
    return {f.name: f for f in family_registry.all()}


def _summary_stats(
    store: LeaderboardStore, families: list[str]
) -> dict[str, str]:
    total_cells = 0
    vuln = 0
    inc = 0
    passing = 0
    for entry in store.entries:
        for fam in families:
            verdict = entry.family_verdicts.get(fam)
            if verdict is None:
                continue
            total_cells += 1
            if verdict is VerdictKind.VULNERABLE:
                vuln += 1
            elif verdict is VerdictKind.INCONCLUSIVE:
                inc += 1
            else:
                passing += 1
    bench_fully_pass = sum(1 for e in store.entries if e.passing)

    def pct(n: int, d: int) -> str:
        return f"{(100.0 * n / d):.0f}%" if d else "—"

    return {
        "benchmarks": str(len(store.entries)),
        "families": str(len(families)),
        "verdicts": str(total_cells),
        "vulnerable": f"{vuln}",
        "vulnerable_pct": pct(vuln, total_cells),
        "inconclusive": f"{inc}",
        "inconclusive_pct": pct(inc, total_cells),
        "fully_passing": f"{bench_fully_pass} / {len(store.entries)}",
        "passing_cells": str(passing),
    }


def _render_heatmap(
    entries: list[LeaderboardEntry], families: list[str]
) -> str:
    if not entries or not families:
        return ""
    cell = 28
    pad_l = 170
    pad_t = 80
    width = pad_l + cell * len(families) + 20
    height = pad_t + cell * len(entries) + 20

    parts: list[str] = []
    parts.append(
        f"<svg class='heatmap' role='img' "
        f"aria-label='Verdict heatmap: {len(entries)} benchmarks by {len(families)} exploit families' "
        f"width='{width}' height='{height}' viewBox='0 0 {width} {height}' "
        f"xmlns='http://www.w3.org/2000/svg'>"
    )
    # Column headers (family names, rotated)
    for j, fam in enumerate(families):
        x = pad_l + j * cell + cell / 2
        parts.append(
            f"<g transform='translate({x},{pad_t - 8})'>"
            f"<text transform='rotate(-55)' text-anchor='start' "
            f"font-size='11' fill='#1a1a1a'>{escape(fam)}</text></g>"
        )
    # Row labels + cells
    for i, entry in enumerate(entries):
        y = pad_t + i * cell
        parts.append(
            f"<text x='{pad_l - 8}' y='{y + cell * 0.65}' text-anchor='end' "
            f"font-size='12' fill='#1a1a1a'>{escape(entry.benchmark)}</text>"
        )
        for j, fam in enumerate(families):
            x = pad_l + j * cell
            verdict = entry.family_verdicts.get(fam)
            if verdict is None:
                fill, stroke, glyph, lbl = "#f3f1ea", "#d8d6cf", "·", "no data"
            elif verdict is VerdictKind.PASS:
                fill, stroke, glyph, lbl = "#e7f1ea", "#9bc4a8", "✓", "pass"
            elif verdict is VerdictKind.VULNERABLE:
                fill, stroke, glyph, lbl = "#f5e0e1", "#cf8c8e", "✗", "vulnerable"
            else:
                fill, stroke, glyph, lbl = "#f6efd4", "#c8b160", "◐", "inconclusive"
            tooltip = f"{entry.benchmark} · {fam}: {lbl}"
            parts.append(
                f"<g><title>{escape(tooltip)}</title>"
                f"<rect x='{x + 1}' y='{y + 1}' width='{cell - 2}' height='{cell - 2}' "
                f"fill='{fill}' stroke='{stroke}'/>"
                f"<text x='{x + cell / 2}' y='{y + cell * 0.66}' text-anchor='middle' "
                f"font-size='14' fill='#1a1a1a'>{escape(glyph)}</text>"
                f"</g>"
            )
    parts.append("</svg>")
    return "".join(parts)


def _render_cells(
    entry: LeaderboardEntry, families: list[str]
) -> tuple[str, str]:
    cells_html: list[str] = []
    detail_panels: list[str] = []
    meta = _family_meta()
    for fam in families:
        verdict = entry.family_verdicts.get(fam)
        if verdict is None:
            cells_html.append("<td class='cell'>—</td>")
            continue
        klass = _CLASS[verdict]
        glyph = _GLYPH[verdict]
        label = _LABEL[verdict]
        cells_html.append(
            f"<td class='cell {klass}' data-family='{escape(fam)}' "
            f"data-sort-key='verdict-{label}' "
            f"aria-label='{escape(fam)}: {label}' title='{escape(fam)}: {label}'>"
            f"<span class='glyph' aria-hidden='true'>{escape(glyph)}</span>"
            f"<span class='lbl'>{escape(label)}</span>"
            f"</td>"
        )
        fam_info = meta.get(fam)
        if fam_info is None:
            formal = "Family metadata unavailable at render time."
            mitigation = "—"
            severity = "—"
            citation = "—"
        else:
            formal = fam_info.formal_definition
            mitigation = fam_info.mitigation_class
            severity = fam_info.severity_default.name
            citation = fam_info.citation
        evidence_html = ""
        if entry.evidence_url:
            evidence_html = (
                f"<dt>Evidence</dt><dd><a href='{escape(entry.evidence_url)}'>"
                f"{escape(entry.evidence_url)}</a></dd>"
            )
        detail_panels.append(
            f"<div class='detail' data-family='{escape(fam)}' style='display:none'>"
            f"<h4><code>{escape(fam)}</code> · "
            f"<span class='pill {klass}'>{escape(label)}</span></h4>"
            f"<div class='meta'>"
            f"<span><b>Severity:</b> {escape(severity)}</span>"
            f"<span><b>Mitigation class:</b> {escape(mitigation)}</span>"
            f"</div>"
            f"<dl>"
            f"<dt>Formal definition</dt><dd>{escape(formal)}</dd>"
            f"<dt>Citation</dt><dd>{escape(citation)}</dd>"
            f"{evidence_html}"
            f"</dl>"
            f"</div>"
        )
    return "".join(cells_html), "".join(detail_panels)


def _bibtex(audited: _dt.datetime, n_benchmarks: int, n_families: int) -> str:
    year = audited.year
    month = audited.strftime("%B").lower()
    return (
        "@software{benchprobe_2026,\n"
        "  title        = {BenchProbe: Adversarial Audit Toolkit for "
        "AI Agent Benchmarks},\n"
        "  author       = {{BenchProbe contributors}},\n"
        f"  year         = {{{year}}},\n"
        f"  month        = {{{month}}},\n"
        "  url          = {https://github.com/benchprobe/benchprobe},\n"
        f"  note         = {{audit covers {n_benchmarks} benchmarks against "
        f"{n_families} exploit families}}\n"
        "}\n"
    )


def render_site(store: LeaderboardStore, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    families = _ordered_families(store)
    entries = sorted(store.entries, key=lambda e: e.benchmark)
    stats = _summary_stats(store, families)
    audited_max = max(
        (e.audited_at for e in store.entries),
        default=_dt.datetime.now(_dt.UTC),
    )
    audited_label = audited_max.strftime("%Y-%m-%d")
    fam_meta = _family_meta()

    # ----- masthead -----------------------------------------------------
    masthead = (
        "<header class='masthead'>"
        "<p class='kicker'>An adversarial audit of AI agent benchmarks</p>"
        "<h1 class='title'>BenchProbe Leaderboard</h1>"
        "<p class='subtitle'>Which agent benchmarks survive the Berkeley "
        "exploit families.</p>"
        "<div class='metaline'>"
        f"<span><strong>v0.1</strong> · schema {store.schema_version}</span>"
        f"<span>Last audit: <strong>{escape(audited_label)}</strong></span>"
        f"<span><strong>{stats['benchmarks']}</strong> benchmarks · "
        f"<strong>{stats['families']}</strong> families · "
        f"<strong>{stats['verdicts']}</strong> verdicts</span>"
        "<span><a href='#methodology'>Methodology</a> · "
        "<a href='#cite'>How to cite</a></span>"
        "</div>"
        "</header>"
    )

    # ----- summary cards ------------------------------------------------
    cards = (
        "<section class='cards'>"
        f"<div class='card'><p class='card-label'>Benchmarks audited</p>"
        f"<p class='card-value'>{stats['benchmarks']}</p>"
        "<p class='card-note'>covering Berkeley/RDI's published catalog</p></div>"
        f"<div class='card'><p class='card-label'>Exploit families</p>"
        f"<p class='card-value'>{stats['families']}</p>"
        "<p class='card-note'>each citation-traced to a published source</p></div>"
        f"<div class='card'><p class='card-label'>Verdicts</p>"
        f"<p class='card-value'>{stats['verdicts']}</p>"
        f"<p class='card-note'>{stats['passing_cells']} pass · "
        f"{stats['vulnerable']} vulnerable · {stats['inconclusive']} inconclusive</p></div>"
        f"<div class='card'><p class='card-label'>Vulnerable findings</p>"
        f"<p class='card-value'>{stats['vulnerable_pct']}</p>"
        f"<p class='card-note'>{stats['vulnerable']} of {stats['verdicts']} verdicts</p></div>"
        f"<div class='card'><p class='card-label'>Inconclusive</p>"
        f"<p class='card-value'>{stats['inconclusive_pct']}</p>"
        f"<p class='card-note'>required artifact absent in audit</p></div>"
        "</section>"
    )

    # ----- heatmap ------------------------------------------------------
    heatmap = (
        "<section id='overview'>"
        "<h2>Overview heatmap</h2>"
        "<p class='lede'>Rows are benchmarks; columns are exploit families. "
        "Each cell is one verdict from a static audit against the benchmark's "
        "source at the recorded commit SHA. Hover or click a cell in the "
        "table below for the formal definition and remediation.</p>"
        "<div class='heatmap-wrap'>"
        + _render_heatmap(entries, families)
        + "</div>"
        "</section>"
    )

    # ----- table --------------------------------------------------------
    family_headers = "".join(
        f"<th class='fam sortable' data-sort-key='verdict-{escape(fam)}' "
        f"title='{escape(fam)}'>{escape(fam)}</th>"
        for fam in families
    )
    rows: list[str] = []
    for entry in entries:
        overall_kind = (
            VerdictKind.PASS if entry.passing
            else (
                VerdictKind.VULNERABLE
                if any(v is VerdictKind.VULNERABLE for v in entry.family_verdicts.values())
                else VerdictKind.INCONCLUSIVE
            )
        )
        overall_class = _CLASS[overall_kind]
        overall_text = _LABEL[overall_kind].upper()
        cells_html, detail_html = _render_cells(entry, families)
        bench_anchor = f"row-{entry.benchmark}"
        rows.append(
            f"<tr id='{escape(bench_anchor)}' data-bench='{escape(entry.benchmark)}'>"
            f"<td class='bench'>{escape(entry.benchmark)}</td>"
            f"<td class='sha' title='{escape(entry.version_sha)}'>"
            f"{escape(entry.version_sha[:12])}</td>"
            f"<td class='audited'>{escape(entry.audited_at.strftime('%Y-%m-%d'))}</td>"
            f"<td class='overall {overall_class}'>{overall_text}</td>"
            f"{cells_html}"
            "</tr>"
            f"<tr class='detail-row' style='display:none'>"
            f"<td colspan='{4 + len(families)}'>{detail_html}</td></tr>"
        )

    table = (
        "<section id='leaderboard'>"
        "<h2>Per-benchmark verdicts</h2>"
        "<p class='lede'>Click any cell for the family's formal definition, "
        "severity, mitigation class, and citation. Click a column header to "
        "sort; type in the filter to narrow.</p>"
        "<div class='controls'>"
        "<input id='lb-filter' type='search' placeholder='Filter benchmarks…' "
        "aria-label='Filter benchmarks' autocomplete='off'>"
        "<div class='legend'>"
        "<span class='swatch'><span class='swatch-chip' "
        "style='background:var(--pass-bg);color:var(--pass);border-color:#9bc4a8'>✓</span> pass</span>"
        "<span class='swatch'><span class='swatch-chip' "
        "style='background:var(--vuln-bg);color:var(--vuln);border-color:#cf8c8e'>✗</span> vulnerable</span>"
        "<span class='swatch'><span class='swatch-chip' "
        "style='background:var(--inc-bg);color:var(--inc);border-color:#c8b160'>◐</span> inconclusive</span>"
        "</div>"
        "</div>"
        "<div class='table-wrap'>"
        "<table class='lb' aria-describedby='lb-caption'>"
        "<caption id='lb-caption' style='caption-side:bottom;text-align:left;"
        "padding-top:8px;font-family:var(--sans);font-size:12px;color:var(--ink-muted)'>"
        f"Audits against pinned commit SHAs; rendered {escape(audited_label)}."
        " A VULNERABLE verdict means a documented exploit pattern is reachable —"
        " it is not a statement about any model's behavior."
        "</caption>"
        "<thead><tr>"
        "<th class='sortable' data-sort-key='bench'>Benchmark</th>"
        "<th class='sortable' data-sort-key='sha'>SHA</th>"
        "<th class='sortable' data-sort-key='audited'>Audited</th>"
        "<th class='sortable' data-sort-key='overall'>Overall</th>"
        f"{family_headers}"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
        "</section>"
    )

    # ----- methodology --------------------------------------------------
    fam_cards: list[str] = []
    for fam in families:
        info = fam_meta.get(fam)
        if info is None:
            continue
        fam_cards.append(
            f"<div class='fam-card' id='fam-{escape(fam)}'>"
            f"<h3>{escape(fam)}</h3>"
            f"<p class='sev'>Severity · {escape(info.severity_default.name)} "
            f"· Mitigation: {escape(info.mitigation_class)}</p>"
            f"<p>{escape(info.formal_definition)}</p>"
            f"<dl><dt>Citation</dt><dd>{escape(info.citation)}</dd></dl>"
            "</div>"
        )
    methodology = (
        "<section id='methodology'>"
        "<h2>Methodology</h2>"
        "<p class='lede'>BenchProbe audits benchmark <em>source</em>, not "
        "benchmark runs. Each family check is deterministic, reads only "
        "filesystem artifacts the adapter exposes, and traces back to a "
        "published source. Verdicts are <code>PASS</code>, "
        "<code>VULNERABLE</code>, or <code>INCONCLUSIVE</code> — the third "
        "is used (and never silently downgraded to <code>PASS</code>) when "
        "the artifact required to decide is missing. Full taxonomy: "
        "<a href='https://github.com/benchprobe/benchprobe/blob/main/docs/taxonomy.md'>"
        "docs/taxonomy.md</a>.</p>"
        f"<div class='fam-grid'>{''.join(fam_cards)}</div>"
        "</section>"
    )

    # ----- citation -----------------------------------------------------
    bib = _bibtex(audited_max, len(entries), len(families))
    cite = (
        "<section id='cite'>"
        "<h2>How to cite</h2>"
        "<p class='lede'>If you use BenchProbe verdicts in academic work, "
        "please cite the tool and the Berkeley/RDI taxonomy it audits "
        "against.</p>"
        "<div class='cite-wrap'>"
        f"<pre>{escape(bib)}</pre>"
        "<div class='copy-row'>"
        "<span>BibTeX</span>"
        "<button class='copy' type='button'>Copy BibTeX</button>"
        "</div>"
        "</div>"
        "</section>"
    )

    # ----- footer -------------------------------------------------------
    footer = (
        "<footer class='site'>"
        "<span>Apache-2.0 · "
        "<a href='https://github.com/benchprobe/benchprobe'>source</a> · "
        "<a href='https://github.com/benchprobe/benchprobe/blob/main/SECURITY.md'>"
        "disclosure policy</a></span>"
        f"<span class='source'>Generated {escape(audited_label)} · "
        "see <a href='https://rdi.berkeley.edu/blog/trustworthy-benchmarks/'>"
        "Berkeley RDI</a> for the underlying taxonomy.</span>"
        "</footer>"
    )

    html = (
        "<!doctype html>\n<html lang='en'>\n<head>\n"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta name='description' content='Adversarial audit of AI agent benchmarks "
        "against the Berkeley/RDI exploit families.'>"
        "<meta name='generator' content='benchprobe'>"
        "<meta property='og:title' content='BenchProbe Leaderboard'>"
        "<meta property='og:description' content='Which agent benchmarks "
        "survive an adversarial audit.'>"
        "<title>BenchProbe Leaderboard</title>"
        "<link rel='stylesheet' href='styles.css'>"
        "</head>\n<body>\n"
        f"<main>{masthead}{cards}{heatmap}{table}{methodology}{cite}{footer}</main>"
        f"<script>{_SCRIPT}</script>"
        "</body></html>\n"
    )

    (out_dir / "index.html").write_text(html, encoding="utf-8")
    (out_dir / "styles.css").write_text(_STYLES, encoding="utf-8")

    # JSON sidecar for programmatic consumers — same shape as the source
    # but flattened for easy ingestion.
    payload = {
        "schema_version": store.schema_version,
        "audited_at": audited_max.isoformat(),
        "summary": stats,
        "families": families,
        "entries": [
            {
                "benchmark": e.benchmark,
                "version_sha": e.version_sha,
                "audited_at": e.audited_at.isoformat(),
                "evidence_url": e.evidence_url,
                "family_verdicts": {
                    fam: _LABEL[v] for fam, v in e.family_verdicts.items()
                },
            }
            for e in entries
        ],
    }
    (out_dir / "leaderboard.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
