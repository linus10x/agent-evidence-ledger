"""Shared test helpers and sys.path injection so tests run zero-install.

Adds src/ to sys.path so `import agent_evidence_ledger` works without an install
step, both under pytest and under the pure-unittest fallback runner.
"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
