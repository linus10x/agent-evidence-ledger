"""Zero-install sys.path injection imported by every test module.

conftest.py covers pytest, but the pure-unittest fallback runner does not load
conftest. Each test module does `import _pathsetup  # noqa` so both runners find
the package without an install step.
"""
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_TESTS = os.path.dirname(__file__)
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)
