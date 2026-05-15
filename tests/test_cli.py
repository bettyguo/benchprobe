"""End-to-end CLI tests.

These exercise the full ``benchprobe audit <bench> --fixture <dir>``
path with stdout capture, plus the leaderboard upsert and render flow.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from benchprobe.cli import app
from benchprobe.core.families import family_registry

runner = CliRunner()
FIXTURE_ROOT = Path(__file__).resolve().parent / "adapters"


def test_cli_audit_swebench_markdown() -> None:
    result = runner.invoke(
        app, ["audit", "swebench", "--fixture", str(FIXTURE_ROOT / "swebench_fixture")]
    )
    # exit code 1 because the fixture is intentionally vulnerable
    assert result.exit_code == 1
    assert "benchprobe audit: swebench" in result.stdout
    assert "env_trojanization" in result.stdout


def test_cli_audit_swebench_json_is_machine_readable() -> None:
    result = runner.invoke(
        app,
        [
            "audit",
            "swebench",
            "--fixture",
            str(FIXTURE_ROOT / "swebench_fixture"),
            "--json",
        ],
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert {v["family"] for v in payload} == set(family_registry.names())
    for v in payload:
        assert v["kind"] in {"pass", "vulnerable", "inconclusive"}
        assert v["severity"] in {"critical", "high", "medium", "low"}


def test_cli_audit_unknown_benchmark_exits_2() -> None:
    result = runner.invoke(
        app,
        [
            "audit",
            "not_real",
            "--fixture",
            str(FIXTURE_ROOT / "swebench_fixture"),
        ],
    )
    assert result.exit_code == 2


def test_cli_audit_unknown_family_exits_2() -> None:
    result = runner.invoke(
        app,
        [
            "audit",
            "swebench",
            "--fixture",
            str(FIXTURE_ROOT / "swebench_fixture"),
            "--family",
            "not_a_family",
        ],
    )
    assert result.exit_code == 2


def test_cli_audit_self_includes_remediation_hints() -> None:
    result = runner.invoke(
        app,
        [
            "audit-self",
            "--benchmark",
            "swebench",
            "--fixture",
            str(FIXTURE_ROOT / "swebench_fixture"),
        ],
    )
    assert result.exit_code in (0, 1)
    assert "Remediation hints" in result.stdout


def test_cli_leaderboard_upsert_and_render(tmp_path: Path) -> None:
    data = tmp_path / "data.json"
    upsert_result = runner.invoke(
        app,
        [
            "leaderboard",
            "upsert",
            "swebench",
            "--fixture",
            str(FIXTURE_ROOT / "swebench_fixture"),
            "--data",
            str(data),
        ],
    )
    # exit 1 means "changed" — the first upsert is always a change
    assert upsert_result.exit_code == 1
    assert data.exists()
    payload = json.loads(data.read_text(encoding="utf-8"))
    assert any(e["benchmark"] == "swebench" for e in payload["entries"])

    # Second upsert is a no-op: same SHA, same verdicts, exit 0
    second = runner.invoke(
        app,
        [
            "leaderboard",
            "upsert",
            "swebench",
            "--fixture",
            str(FIXTURE_ROOT / "swebench_fixture"),
            "--data",
            str(data),
        ],
    )
    assert second.exit_code == 0

    render_result = runner.invoke(
        app,
        [
            "leaderboard",
            "render",
            "--data",
            str(data),
            "--out-dir",
            str(tmp_path / "site"),
        ],
    )
    assert render_result.exit_code == 0
    site_index = tmp_path / "site" / "index.html"
    assert site_index.exists()
    assert "swebench" in site_index.read_text(encoding="utf-8")
