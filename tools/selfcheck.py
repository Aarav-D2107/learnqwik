#!/usr/bin/env python3
"""
Offline self-check for LearnQwik's pure logic.

`pytest` is the real test runner (see backend/pytest.ini) and you should use it
once dependencies are installed:

    cd backend && pytest -q

But the scoring, mastery, recommendation, roadmap, reassessment, parsing and
retrieval modules are written with **zero third-party imports**, on purpose.
That means they can be verified on a machine with nothing installed at all —
no pip, no network, no Supabase, no AI key. This script does exactly that by
providing a minimal `pytest` shim (fixture / raises / approx / importorskip)
and executing the real test files in backend/tests/.

    python3 tools/selfcheck.py

Every assertion here is the same assertion pytest runs. If this passes, the
deterministic core of the product is correct.
"""
import importlib.util
import inspect
import os
import sys
import traceback
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
TESTS = os.path.join(BACKEND, "tests")

# Only these files can run without third-party packages installed.
PURE_TEST_MODULES = [
    "test_scoring.py",
    "test_mastery.py",
    "test_recommendations.py",
    "test_roadmap.py",
    "test_reassessment.py",
    "test_documents.py",
]


# --------------------------------------------------------------- pytest shim
class _Raises:
    def __init__(self, expected, match=None):
        self.expected = expected
        self.match = match

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError("expected %s to be raised" % self.expected.__name__)
        if not issubclass(exc_type, self.expected):
            return False
        if self.match:
            import re
            if not re.search(self.match, str(exc), re.IGNORECASE):
                raise AssertionError("%r did not match %r" % (str(exc), self.match))
        return True


class _Approx:
    def __init__(self, value, tolerance=1e-6):
        self.value = value
        self.tolerance = tolerance

    def __eq__(self, other):
        return abs(float(other) - float(self.value)) <= self.tolerance

    def __repr__(self):
        return "approx(%r)" % self.value


class _Skip(Exception):
    pass


def _make_pytest_shim():
    shim = types.ModuleType("pytest")

    def fixture(func=None, **kwargs):
        def wrap(f):
            f.__is_fixture__ = True
            return f
        return wrap(func) if func else wrap

    def importorskip(name):
        try:
            return importlib.import_module(name)
        except ImportError:
            raise _Skip("%s is not installed" % name)

    shim.fixture = fixture
    shim.raises = lambda expected, match=None: _Raises(expected, match)
    shim.approx = lambda value, **kw: _Approx(value)
    shim.importorskip = importorskip
    shim.skip = lambda reason="": (_ for _ in ()).throw(_Skip(reason))
    return shim


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    sys.path.insert(0, BACKEND)
    sys.modules["pytest"] = _make_pytest_shim()
    import importlib  # noqa: F401  (used inside the shim)

    conftest = _load(os.path.join(TESTS, "conftest.py"), "lq_conftest")
    fixtures = {
        name: fn
        for name, fn in vars(conftest).items()
        if callable(fn) and getattr(fn, "__is_fixture__", False)
    }

    passed = failed = skipped = 0
    failures = []

    for filename in PURE_TEST_MODULES:
        path = os.path.join(TESTS, filename)
        if not os.path.exists(path):
            print("  ?  %s (missing)" % filename)
            continue

        module = _load(path, "lq_" + filename[:-3])
        local_fixtures = dict(fixtures)
        local_fixtures.update({
            name: fn
            for name, fn in vars(module).items()
            if callable(fn) and getattr(fn, "__is_fixture__", False)
        })

        tests = sorted(
            (name, fn) for name, fn in vars(module).items()
            if name.startswith("test_") and callable(fn)
        )
        print("\n%s  (%d tests)" % (filename, len(tests)))

        for name, fn in tests:
            try:
                kwargs = {}
                for param in inspect.signature(fn).parameters:
                    if param not in local_fixtures:
                        raise _Skip("no fixture named %r" % param)
                    kwargs[param] = local_fixtures[param]()
                fn(**kwargs)
                passed += 1
                print("  PASS  %s" % name)
            except _Skip as exc:
                skipped += 1
                print("  SKIP  %s (%s)" % (name, exc))
            except Exception:
                failed += 1
                failures.append((filename, name, traceback.format_exc()))
                print("  FAIL  %s" % name)

    print("\n" + "=" * 62)
    print("passed: %d   failed: %d   skipped: %d" % (passed, failed, skipped))
    print("=" * 62)

    if failures:
        for filename, name, tb in failures:
            print("\n--- %s::%s ---\n%s" % (filename, name, tb))
        return 1

    print("\nAll pure-logic tests passed with zero third-party dependencies.")
    print("Run the full suite (including FastAPI route tests) with:")
    print("    cd backend && pytest -q")
    return 0


if __name__ == "__main__":
    sys.exit(main())
