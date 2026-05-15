"""Benchmark adapters.

Each adapter describes (does not embed) one benchmark. v0.1 ships 15
adapters covering benchmarks documented in Berkeley/RDI's published
audit and the ``moogician/trustworthy-env`` exploit catalogue.

Plugin discovery is a v0.2 concern; the registry is hardcoded so the
audit toolkit's surface area is reviewable.
"""

from __future__ import annotations

from benchprobe.adapters.agentbench import AgentBenchAdapter
from benchprobe.adapters.agieval import AGIEvalAdapter
from benchprobe.adapters.bfcl import BFCLAdapter
from benchprobe.adapters.car_bench import CARBenchAdapter
from benchprobe.adapters.fieldwork_arena import FieldWorkArenaAdapter
from benchprobe.adapters.frontier_cs import FrontierCSAdapter
from benchprobe.adapters.gaia import GaiaAdapter
from benchprobe.adapters.humaneval import HumanEvalAdapter
from benchprobe.adapters.livebench import LiveBenchAdapter
from benchprobe.adapters.mmlu import MMLUAdapter
from benchprobe.adapters.osworld import OSWorldAdapter
from benchprobe.adapters.swebench import SWEBenchAdapter
from benchprobe.adapters.swebench_pro import SWEBenchProAdapter
from benchprobe.adapters.terminal_bench import TerminalBenchAdapter
from benchprobe.adapters.webarena import WebArenaAdapter
from benchprobe.core.harness import HarnessAdapter

_ADAPTERS: dict[str, HarnessAdapter] = {
    "swebench": SWEBenchAdapter(),
    "swebench_pro": SWEBenchProAdapter(),
    "webarena": WebArenaAdapter(),
    "gaia": GaiaAdapter(),
    "terminal_bench": TerminalBenchAdapter(),
    "osworld": OSWorldAdapter(),
    "frontier_cs": FrontierCSAdapter(),
    "fieldwork_arena": FieldWorkArenaAdapter(),
    "car_bench": CARBenchAdapter(),
    "humaneval": HumanEvalAdapter(),
    "mmlu": MMLUAdapter(),
    "bfcl": BFCLAdapter(),
    "agentbench": AgentBenchAdapter(),
    "agieval": AGIEvalAdapter(),
    "livebench": LiveBenchAdapter(),
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
    "AGIEvalAdapter",
    "AgentBenchAdapter",
    "BFCLAdapter",
    "CARBenchAdapter",
    "FieldWorkArenaAdapter",
    "FrontierCSAdapter",
    "GaiaAdapter",
    "HumanEvalAdapter",
    "LiveBenchAdapter",
    "MMLUAdapter",
    "OSWorldAdapter",
    "SWEBenchAdapter",
    "SWEBenchProAdapter",
    "TerminalBenchAdapter",
    "WebArenaAdapter",
    "adapter_names",
    "get_adapter",
]
