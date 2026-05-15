"""Thin shim — invoke ``benchprobe leaderboard render``.

This file exists so the architecture diagram in the README matches the
repo layout (``leaderboard/render.py``). All logic lives in
``benchprobe.leaderboard_render``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from benchprobe.core.leaderboard import LeaderboardStore
from benchprobe.leaderboard_render import render_site


def main() -> int:
    data_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("leaderboard/data.json")
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("leaderboard/site")
    store = LeaderboardStore.load(data_path)
    render_site(store, out_dir)
    print(f"wrote {len(store.entries)} entries to {out_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
