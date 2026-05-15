"""Benchmark adapters.

Each adapter describes (does not embed) one benchmark. v0.1 ships five —
SWE-bench, WebArena, GAIA, Terminal-Bench, OSWorld — all hardcoded.
Plugin discovery is a v0.2 concern; for now the registry is explicit.
"""

from __future__ import annotations

from benchprobe.adapters.gaia import GaiaAdapter
from benchprobe.adapters.osworld import OSWorldAdapter
from benchprobe.adapters.swebench import SWEBenchAdapter
from benchprobe.adapters.terminal_bench import TerminalBenchAdapter
from benchprobe.adapters.webarena import WebArenaAdapter
from benchprobe.core.harness import HarnessAdapter

_ADAPTERS: dict[str, HarnessAdapter] = {
    "swebench": SWEBenchAdapter(),
    "webarena": WebArenaAdapter(),
    "gaia": GaiaAdapter(),
    "terminal_bench": TerminalBenchAdapter(),
    "osworld": OSWorldAdapter(),
}


def get_adapter(name: str) -> HarnessAdapter:
    """Look up a registered adapter by canonical name."""
    if name not in _ADAPTERS:
        raise KeyError(
            f"unknown benchmark adapter: {name!r}. "
            f"Available: {sorted(_ADAPTERS.keys())}."
        )
    return _ADAPTERS[name]


def adapter_names() -> tuple[str, ...]:
    return tuple(_ADAPTERS.keys())


__all__ = [
    "GaiaAdapter",
    "OSWorldAdapter",
    "SWEBenchAdapter",
    "TerminalBenchAdapter",
    "WebArenaAdapter",
    "adapter_names",
    "get_adapter",
]
