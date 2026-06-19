"""Pure-python (unittest-based) fallback runner used when pytest is absent.

A fresh clone with no pytest still gets a real pass/fail. It discovers the
tests/ modules, installs a tiny `pytest` shim (parametrize + raises) so the
pytest-style test functions import and run, executes every `test_*` function,
and exits non-zero on any failure.
"""
import importlib.util
import os
import sys
import traceback
import types


def _install_pytest_shim():
    # The fallback runner is self-contained and must not depend on pytest being
    # installed OR absent. It force-installs its own minimal shim so the
    # pytest-style test functions (parametrize / raises) run identically whether
    # or not real pytest is present. This is the zero-install proof path.
    shim = types.ModuleType("pytest")

    class _Mark:
        @staticmethod
        def parametrize(argnames, argvalues):
            def deco(fn):
                fn._params = (argnames, list(argvalues))
                return fn
            return deco

    class _Raises:
        def __init__(self, exc):
            self.exc = exc

        def __enter__(self):
            return self

        def __exit__(self, etype, eval_, tb):
            if etype is None:
                raise AssertionError("expected %r, none raised" % (self.exc,))
            return issubclass(etype, self.exc)

    shim.mark = _Mark()
    shim.raises = lambda exc: _Raises(exc)
    # Drop any sub-modules of a previously-imported real pytest, then install.
    for name in [m for m in sys.modules if m == "pytest" or m.startswith("pytest.")]:
        del sys.modules[name]
    sys.modules["pytest"] = shim


def _iter_test_files(tests_dir):
    for name in sorted(os.listdir(tests_dir)):
        if name.startswith("test_") and name.endswith(".py"):
            yield name[:-3], os.path.join(tests_dir, name)


def _load_module(modname, path):
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_one(fn):
    """Run a test function, expanding a single-arg parametrize. Returns list of
    (label, ok, err)."""
    results = []
    params = getattr(fn, "_params", None)
    if params is None:
        try:
            fn()
            results.append((fn.__name__, True, None))
        except Exception:
            results.append((fn.__name__, False, traceback.format_exc()))
        return results
    argnames, argvalues = params
    for val in argvalues:
        label = "%s[%r]" % (fn.__name__, val)
        try:
            if isinstance(argnames, (list, tuple)):
                fn(*val)
            else:
                fn(val)
            results.append((label, True, None))
        except Exception:
            results.append((label, False, traceback.format_exc()))
    return results


def main():
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tests_dir = os.path.join(here, "tests")
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)
    src_dir = os.path.join(here, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    _install_pytest_shim()

    passed = 0
    failed = 0
    failures = []
    for modname, path in _iter_test_files(tests_dir):
        mod = _load_module(modname, path)
        for attr in sorted(dir(mod)):
            if not attr.startswith("test_"):
                continue
            obj = getattr(mod, attr)
            if not callable(obj):
                continue
            for label, ok, err in _run_one(obj):
                if ok:
                    passed += 1
                else:
                    failed += 1
                    failures.append(("%s::%s" % (modname, label), err))

    print("=" * 60)
    for name, err in failures:
        print("FAILED %s" % name)
        print(err)
    print("pure-python runner: %d passed, %d failed" % (passed, failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
