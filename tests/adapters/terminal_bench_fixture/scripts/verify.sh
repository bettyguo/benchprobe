#!/usr/bin/env bash
# Synthetic Terminal-Bench verifier.
# Anti-pattern: passes based on file existence only.

set -euo pipefail

if [ -f "/workspace/output/mylib.so" ]; then
    echo "PASS"
    exit 0
fi
echo "FAIL"
exit 1
