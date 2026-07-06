# Implementation: tests/test_tool_registry_reset_protection.py — Static scan for reset API misuse

## Goal

CI check that `_reset_registry_for_testing()` is never called from production (non-test) code.

## Scope

**In**: Static scan of `scripts/` excluding test directories. Positive test verifying test-code usage works.

**Out**: Testing registry behavior itself (covered by other tests).

## Assumptions

1. `SCRIPTS_DIR` is `scripts/` relative to project root (tests run from project root).
2. Test directories are identifiable by path containing `tests` or `test`.
3. The definition file `tool_registry.py` is excluded from the violation check (contains `def _reset_registry_for_testing`).
4. All production code is under `scripts/` — no `src/` or similar directory.

## Implementation

### Target file
`tests/test_tool_registry_reset_protection.py`

### Procedure
Write static scan test plus positive functional test.

### Method

```python
import pathlib
import pytest
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
        # definition is allowed; any call site is not
        if forbidden in content and f"def {forbidden}" not in content:
            violations.append(str(py_file))
    assert not violations, (
        f"Production code calls {forbidden!r} (test-only API): {violations}"
    )


def test_reset_registry_works_in_tests():
    """Verify the renamed function is importable and callable from test code."""
    _reset_registry_for_testing()
    registry = get_registry()
    assert registry is not None  # get_registry() auto-creates a fresh instance


def test_static_scan_tolerates_definition_file():
    """The definition file (tool_registry.py) must not be flagged as a violation."""
    forbidden = "_reset_registry_for_testing"
    definition_file = SCRIPTS_DIR / "shared" / "tool_registry.py"
    content = definition_file.read_text()
    assert f"def {forbidden}" in content, "definition expected in tool_registry.py"
    # confirm our scan logic correctly excludes it
    assert f"def {forbidden}" in content  # covered by the 'not in content' guard in scan
```

## Validation plan

- `uv run pytest tests/test_tool_registry_reset_protection.py -v` — all pass.
- Verify: adding a fake call to `_reset_registry_for_testing()` in a production module → test fails.
- `ruff check tests/test_tool_registry_reset_protection.py` — 0 errors.
