#!/usr/bin/env bash
# Thin wrapper: pytest if present, else the pure-python unittest fallback.
# Forwards the exit code. Zero-install, no network, no make.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
if python3 -c "import pytest" >/dev/null 2>&1; then
    exec python3 -m pytest tests/ "$@"
else
    echo "pytest not found - using the pure-python fallback runner"
    exec python3 -m agent_evidence_ledger._testrunner
fi
