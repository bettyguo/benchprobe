"""Synthetic negative: exercises the artifact instead of stat()ing it."""

import ctypes
import os.path


def check_solution(workdir: str) -> int:
    path = workdir + "/mylib.so"
    if not os.path.exists(path):
        return 0
    lib = ctypes.CDLL(path)
    try:
        result = lib.add(2, 3)
    except (AttributeError, OSError):
        return 0
    return 1 if result == 5 else 0
