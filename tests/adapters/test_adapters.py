"""Adapter contract tests.

Each adapter's ``expose_artifacts`` must return the documented shape:
- ``benchmark`` matches the adapter's name
- ``root`` is the path we passed in
- ``version_sha`` is one of the validated SHAs
- ``evaluator_paths`` is non-empty (we don't ship adapters that audit nothing)
- ``latest_known_sha`` is in ``validated_shas``

We deliberately do NOT require evaluator_paths to exist on disk in the
fixture — adapters describe layouts, fixtures only need to mirror the
parts the family checks actually open.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchprobe.adapters import adapter_names, get_adapter

FIXTURE_ROOT = Path(__file__).resolve().parent
ADAPTER_FIXTURE_MAP = {
    "swebench": FIXTURE_ROOT / "swebench_fixture",
    "swebench_pro": FIXTURE_ROOT / "swebench_pro_fixture",
    "webarena": FIXTURE_ROOT / "webarena_fixture",
    "gaia": FIXTURE_ROOT / "gaia_fixture",
    "terminal_bench": FIXTURE_ROOT / "terminal_bench_fixture",
    "osworld": FIXTURE_ROOT / "osworld_fixture",
    "frontier_cs": FIXTURE_ROOT / "frontier_cs_fixture",
    "fieldwork_arena": FIXTURE_ROOT / "fieldwork_arena_fixture",
    "car_bench": FIXTURE_ROOT / "car_bench_fixture",
    "humaneval": FIXTURE_ROOT / "humaneval_fixture",
    "mmlu": FIXTURE_ROOT / "mmlu_fixture",
    "bfcl": FIXTURE_ROOT / "bfcl_fixture",
    "agentbench": FIXTURE_ROOT / "agentbench_fixture",
    "agieval": FIXTURE_ROOT / "agieval_fixture",
    "livebench": FIXTURE_ROOT / "livebench_fixture",
}


@pytest.mark.parametrize("name", list(adapter_names()))
def test_adapter_contract(name: str) -> None:
    adapter = get_adapter(name)
    fixture = ADAPTER_FIXTURE_MAP[name]
    assert fixture.exists(), f"adapter fixture missing: {fixture}"
    artifacts = adapter.expose_artifacts(fixture)
    assert artifacts.benchmark == name
    assert artifacts.root == fixture
    assert artifacts.version_sha in adapter.validated_shas
    assert artifacts.evaluator_paths, "adapters must declare at least one evaluator path"
    assert adapter.latest_known_sha() in adapter.validated_shas


def test_adapter_registry_lookup_raises_for_unknown() -> None:
    with pytest.raises(KeyError):
        get_adapter("not_a_real_benchmark")


def test_every_advertised_adapter_has_a_fixture() -> None:
    for name in adapter_names():
        assert name in ADAPTER_FIXTURE_MAP, (
            f"adapter {name} has no fixture in tests/adapters/"
        )
