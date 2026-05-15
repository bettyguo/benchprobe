"""``benchprobe`` command-line entry point.

Three subcommands, kept stable from v0.1:

- ``audit <benchmark> --fixture <path>``: run all family checks against
  a benchmark adapter pointed at ``<path>`` (a real clone or a fixture).
- ``audit-self --family <name> --fixture <path>``: benchmark authors run
  this on their work-in-progress; output includes ``remediation_hint``.
- ``leaderboard render``: regenerate the static site under
  ``leaderboard/site/`` from ``leaderboard/data.json``.

The CLI prints a Markdown report by default; ``--json`` switches to
machine-readable output. ``--html`` writes a self-contained HTML file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

import benchprobe.families  # noqa: F401  # side-effect: registers families
from benchprobe.adapters import adapter_names, get_adapter
from benchprobe.audit import run_audit
from benchprobe.core.families import family_registry
from benchprobe.core.leaderboard import LeaderboardStore, entry_from_verdicts
from benchprobe.core.verdict import VerdictKind
from benchprobe.reports import render_html_report, render_markdown_report

app = typer.Typer(
    name="benchprobe",
    help="Audit AI agent benchmarks for the Berkeley/RDI exploit families.",
    add_completion=False,
    no_args_is_help=True,
)


def _serialize_verdicts(verdicts: list) -> str:  # type: ignore[type-arg]
    payload = [
        {
            "family": v.family,
            "benchmark": v.benchmark,
            "kind": v.kind.value,
            "severity": v.severity.value,
            "reason": v.reason,
            "remediation_hint": v.remediation_hint,
            "evidence": [
                {"path": e.path, "snippet": e.snippet, "line": e.line}
                for e in v.evidence
            ],
            "audited_at": v.audited_at.isoformat(),
            "auditor_version": v.auditor_version,
        }
        for v in verdicts
    ]
    return json.dumps(payload, indent=2, sort_keys=True)


def _warn_stale_adapter(benchmark: str, fixture_root: Path) -> None:
    adapter = get_adapter(benchmark)
    sha_hint = (fixture_root / ".version_sha").read_text(encoding="utf-8").strip() if (
        fixture_root / ".version_sha"
    ).exists() else None
    if sha_hint and sha_hint not in adapter.validated_shas:
        typer.echo(
            f"warning: fixture .version_sha={sha_hint!r} is not in this "
            f"adapter's validated_shas — the audit may be stale.",
            err=True,
        )


@app.command()
def audit(
    benchmark: Annotated[str, typer.Argument(help="Adapter name (e.g. swebench).")],
    fixture: Annotated[
        Path,
        typer.Option(
            "--fixture",
            help="Path to the benchmark clone or fixture directory.",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
    output_json: Annotated[bool, typer.Option("--json", help="Emit JSON instead of Markdown.")] = False,
    output_html: Annotated[
        Path | None, typer.Option("--html", help="Also write a self-contained HTML report to this path.")
    ] = None,
    family: Annotated[
        list[str] | None,
        typer.Option(
            "--family",
            help="Run only the named family/families. Repeatable. Defaults to all.",
        ),
    ] = None,
) -> None:
    """Audit a benchmark adapter pointed at a clone or fixture."""
    if benchmark not in adapter_names():
        typer.echo(
            f"unknown benchmark: {benchmark!r}. "
            f"Available: {', '.join(adapter_names())}.",
            err=True,
        )
        raise typer.Exit(code=2)

    if family:
        unknown = [name for name in family if name not in family_registry]
        if unknown:
            typer.echo(
                f"unknown family/families: {unknown}. "
                f"Available: {family_registry.names()}.",
                err=True,
            )
            raise typer.Exit(code=2)

    _warn_stale_adapter(benchmark, fixture)
    _artifacts, verdicts = run_audit(benchmark, fixture, families=family)

    if output_json:
        typer.echo(_serialize_verdicts(verdicts))
    else:
        typer.echo(render_markdown_report(verdicts, benchmark=benchmark))

    if output_html is not None:
        output_html.parent.mkdir(parents=True, exist_ok=True)
        output_html.write_text(
            render_html_report(verdicts, benchmark=benchmark), encoding="utf-8"
        )

    n_vuln = sum(1 for v in verdicts if v.kind is VerdictKind.VULNERABLE)
    raise typer.Exit(code=1 if n_vuln else 0)


@app.command("audit-self")
def audit_self(
    fixture: Annotated[
        Path,
        typer.Option(
            "--fixture",
            help="Path to the benchmark you are developing.",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
    benchmark: Annotated[
        str,
        typer.Option(
            "--benchmark",
            help="Adapter name to interpret the layout with.",
        ),
    ] = "swebench",
    family: Annotated[
        list[str] | None,
        typer.Option("--family", help="Limit to one family while iterating."),
    ] = None,
) -> None:
    """Run the audit against a work-in-progress benchmark, with hints surfaced."""
    _artifacts, verdicts = run_audit(benchmark, fixture, families=family)
    typer.echo(render_markdown_report(verdicts, benchmark=benchmark))
    failing = [v for v in verdicts if v.kind is not VerdictKind.PASS]
    if failing:
        typer.echo("\n# Remediation hints\n")
        for v in failing:
            typer.echo(f"- **{v.family}** ({v.kind.value}): {v.remediation_hint}")
    raise typer.Exit(code=1 if any(v.kind is VerdictKind.VULNERABLE for v in verdicts) else 0)


leaderboard_app = typer.Typer(
    name="leaderboard",
    help="Manage and render the public leaderboard.",
    no_args_is_help=True,
)
app.add_typer(leaderboard_app, name="leaderboard")


@leaderboard_app.command("render")
def leaderboard_render(
    data: Annotated[
        Path,
        typer.Option(
            "--data",
            help="Path to data.json.",
            exists=True,
        ),
    ] = Path("leaderboard/data.json"),
    out_dir: Annotated[
        Path, typer.Option("--out-dir", help="Static-site output directory.")
    ] = Path("leaderboard/site"),
) -> None:
    """Render ``data.json`` to a static HTML site."""
    from benchprobe.leaderboard_render import render_site

    store = LeaderboardStore.load(data)
    render_site(store, out_dir)
    typer.echo(f"wrote {len(store.entries)} entries to {out_dir}/index.html")


@leaderboard_app.command("upsert")
def leaderboard_upsert(
    benchmark: Annotated[str, typer.Argument(help="Adapter name (e.g. swebench).")],
    fixture: Annotated[
        Path,
        typer.Option(
            "--fixture",
            help="Path to the benchmark clone or fixture directory.",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
    data: Annotated[
        Path, typer.Option("--data", help="Path to data.json.")
    ] = Path("leaderboard/data.json"),
    evidence_url: Annotated[
        str | None,
        typer.Option(
            "--evidence-url",
            help="Permalink to the audit evidence (commit, PR, or report).",
        ),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Print what would change; do not write.")
    ] = False,
) -> None:
    """Audit a benchmark and update its leaderboard row.

    Exits 0 if the row is unchanged, 1 if it changed (so a workflow can
    detect "something to PR"). ``--dry-run`` prints the diff and exits.
    """
    adapter = get_adapter(benchmark)
    _, verdicts = run_audit(benchmark, fixture)
    entry = entry_from_verdicts(
        benchmark=benchmark,
        version_sha=adapter.latest_known_sha(),
        verdicts=verdicts,
        evidence_url=evidence_url,
    )
    store = LeaderboardStore.load(data) if data.exists() else LeaderboardStore()
    changed = store.upsert(entry)
    if dry_run:
        typer.echo(
            f"dry-run: benchmark={benchmark} changed={changed} "
            f"verdicts={ {k: v.value for k, v in entry.family_verdicts.items()} }"
        )
        raise typer.Exit(code=1 if changed else 0)
    store.save(data)
    typer.echo(
        f"updated {data}: benchmark={benchmark} changed={changed}",
    )
    raise typer.Exit(code=1 if changed else 0)


def main() -> None:
    """Programmatic entry — equivalent to invoking ``benchprobe`` on the shell."""
    app()


if __name__ == "__main__":
    main()
    sys.exit(0)
