"""CI check: _reset_registry_for_testing() must not be called from production code."""

import pathlib

from shared.tool_registry import _reset_registry_for_testing, get_registry

SCRIPTS_DIR = pathlib.Path("scripts")
_TEST_PATH_PARTS = {"tests", "test"}


def _is_test_file(path: pathlib.Path) -> bool:
    return bool(set(path.parts) & _TEST_PATH_PARTS)


def test_production_code_does_not_call_reset_registry():
    """CI: _reset_registry_for_testing() must not appear in production code."""
    forbidden = "_reset_registry_for_testing"
    violations = []
    for py_file in SCRIPTS_DIR.rglob("*.py"):
        if _is_test_file(py_file):
            continue
        content = py_file.read_text()
        if forbidden in content and f"def {forbidden}" not in content:
            violations.append(str(py_file))
    assert not violations, (
        f"Production code calls {forbidden!r} (test-only API): {violations}"
    )


def test_reset_registry_works_in_tests():
    """Verify the renamed function is importable and callable from test code."""
    _reset_registry_for_testing()
    registry = get_registry()
    assert registry is not None


def test_static_scan_tolerates_definition_file():
    """The definition file (tool_registry.py) must not be flagged as a violation."""
    forbidden = "_reset_registry_for_testing"
    definition_file = SCRIPTS_DIR / "shared" / "tool_registry.py"
    content = definition_file.read_text()
    assert f"def {forbidden}" in content
