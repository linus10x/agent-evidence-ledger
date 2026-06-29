#!/usr/bin/env bash
# Thin wrapper: run the zero-install demo and forward its exit code. No make.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m agent_evidence_ledger.demo "$@"
