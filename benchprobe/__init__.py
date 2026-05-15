"""benchprobe: audit toolkit for AI agent benchmarks.

Public surface kept narrow on purpose — see ``benchprobe.cli`` for the
command-line entry point and ``benchprobe.core`` for the typed audit API.
"""

from benchprobe.core.harness import HarnessArtifacts
from benchprobe.core.verdict import Severity, Verdict, VerdictKind

__all__ = ["HarnessArtifacts", "Severity", "Verdict", "VerdictKind", "__version__"]

__version__ = "0.1.0"
