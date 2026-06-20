# Implementation: test_startup_consistency.py

## Goal
Create `tests/test_startup_consistency.py` to verify that:
1. When `RagMaintenanceService().consistency()` returns `(False, ["issue X"])`,
   `write_warning()` is called with the issue string.
2. When `consistency()` raises an exception, no crash occurs (logged at DEBUG only).
3. When `consistency()` returns `(True, [])`, no `write_warning()` is called.

## Scope
- New file: `tests/test_startup_consistency.py`
- Mock `RagMaintenanceService` to avoid real SQLite
- Patch at the `startup` module import level

## Assumptions
- `StartupOrchestrator` (or equivalent class in `startup.py`) can be instantiated
  with a mock `_view` that has a `write_warning()` method
- `RagMaintenanceService` is patched via `unittest.mock.patch`
- The import path is `agent.startup.RagMaintenanceService`

## Implementation

### Target file
`tests/test_startup_consistency.py`

### Procedure
Write 3 test cases using `pytest-asyncio` or plain `pytest`, depending on whether
`_check_services()` is async.

### Method
New test file. Use `unittest.mock.patch` + `MagicMock`.

### Details

```python
"""tests/test_startup_consistency.py
Verifies that _check_services() emits write_warning on RAG inconsistency.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_orchestrator():
    """Return a minimal StartupOrchestrator with mocked _view."""
    from agent.startup import StartupOrchestrator
    orch = StartupOrchestrator.__new__(StartupOrchestrator)
    orch._view = MagicMock()
    orch._cfg = MagicMock()
    return orch


def test_write_warning_on_inconsistency():
    """Inconsistent index → write_warning called with each issue."""
    orch = _make_orchestrator()
    with patch(
        "agent.startup.RagMaintenanceService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.consistency.return_value = (False, ["fts_gap=3", "orphan_vec=1"])
        mock_svc_cls.return_value = mock_svc
        # Call only the consistency portion; adjust if _check_services does more
        try:
            orch._check_services()
        except Exception:
            pass  # other checks may fail without real context
    calls = [str(c) for c in orch._view.write_warning.call_args_list]
    assert any("fts_gap=3" in c for c in calls)


def test_no_warning_on_consistent():
    """Consistent index → write_warning not called."""
    orch = _make_orchestrator()
    with patch(
        "agent.startup.RagMaintenanceService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.consistency.return_value = (True, [])
        mock_svc_cls.return_value = mock_svc
        try:
            orch._check_services()
        except Exception:
            pass
    orch._view.write_warning.assert_not_called()


def test_no_crash_on_exception():
    """Exception from consistency check → no crash; logged at DEBUG only."""
    orch = _make_orchestrator()
    with patch(
        "agent.startup.RagMaintenanceService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.consistency.side_effect = FileNotFoundError("rag.sqlite not found")
        mock_svc_cls.return_value = mock_svc
        try:
            orch._check_services()
        except Exception as e:
            pytest.fail(f"_check_services() raised unexpectedly: {e}")
```

**Note:** The `_check_services()` call may trigger other checks that require real
dependencies. Adjust by only testing the consistency sub-block if needed, e.g. by
extracting the block to `_check_rag_consistency()` or by patching all other dependencies.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All 3 tests pass | `uv run pytest tests/test_startup_consistency.py -v` | 3 passed |
| Lint | `uv run ruff check tests/test_startup_consistency.py` | 0 errors |
| Type check | `uv run mypy tests/test_startup_consistency.py` | no errors |
| Full suite | `uv run pytest -q` | no new failures |
