## Goal

Make `_HEALTH_RECHECK_INTERVAL_SEC` importable as a public constant `HEALTH_RECHECK_INTERVAL_SEC` so `http_lifecycle.py` can use it instead of the hardcoded `10.0` literal in `verify_running_async()`. No other behavior change.

## Scope

- Rename `_HEALTH_RECHECK_INTERVAL_SEC = 10.0` to `HEALTH_RECHECK_INTERVAL_SEC = 10.0` in `http_lifecycle_health_checker.py`.
- Update any internal references to the old name within this file.

## Assumptions

- `_HEALTH_RECHECK_INTERVAL_SEC` is confirmed unused within `http_lifecycle_health_checker.py` itself — the constant is only referenced by `http_lifecycle.py`'s `verify_running_async()` at L162 (`if time.monotonic() - last_check < 10.0`).
- A private name should not be imported across module boundaries — hence the rename to public.

## Design decisions

- Simple rename only — no behavioral change.
- Do not make the recheck interval configurable via `McpServerConfig` — out of scope per the Plan.

## Alternatives considered

- Adding a separate public constant alongside the private one — rejected because it duplicates the value unnecessarily.
- Making the constant configurable — rejected because the Plan explicitly states this is out of scope.

## Implementation
### Target file

`scripts/agent/http_lifecycle_health_checker.py`

### Procedure

1. Rename `_HEALTH_RECHECK_INTERVAL_SEC` to `HEALTH_RECHECK_INTERVAL_SEC` on L14.
2. Verify no internal references to the old name remain in this file.

### Method

Current state:
```python
_HEALTH_RECHECK_INTERVAL_SEC = 10.0
```

Required change:
```python
HEALTH_RECHECK_INTERVAL_SEC = 10.0
```

No other changes needed — the constant is not referenced internally in this file (confirmed by reading the full file content).

### Details

After renaming, `http_lifecycle.py` can import and use:
```python
from agent.http_lifecycle_health_checker import HEALTH_RECHECK_INTERVAL_SEC
```

And replace the hardcoded `10.0` in `verify_running_async()` at L162:
```python
if time.monotonic() - last_check < HEALTH_RECHECK_INTERVAL_SEC:
    return True
```

Note: This import/update is handled in the next procedure document (REQ-005 in `http_lifecycle.py`).

## Compatibility considerations

- The rename is backward-compatible in terms of value — the constant still equals `10.0`.
- The visibility change (private → public) means external code can now import this constant — this is intentional and desired.
- No existing code in this repository imports `_HEALTH_RECHECK_INTERVAL_SEC` directly (only `http_lifecycle.py` uses the value inline).

## Security considerations

- No security impact — renaming a constant has no security implications.

## Rollback considerations

- If the rename causes issues, simply revert the name back to `_HEALTH_RECHECK_INTERVAL_SEC`.
- The value remains unchanged, so no behavioral rollback is needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `http_lifecycle_health_checker.py` | Static analysis | `uv run ruff check scripts/agent/http_lifecycle_health_checker.py` | Clean |
| `http_lifecycle_health_checker.py` | Type check | `uv run mypy scripts/agent/http_lifecycle_health_checker.py` | Pass (no new regressions) |
| `test_http_lifecycle_health_checker.py` | Unit (new test file) | `uv run pytest tests/agent/test_http_lifecycle_health_checker.py -q` | Constant importable and used; URL fallback behavior documented |

## Completion criteria

- `HEALTH_RECHECK_INTERVAL_SEC` is renamed from `_HEALTH_RECHECK_INTERVAL_SEC`; no internal references to the old name remain.
- `uv run ruff check scripts/agent/http_lifecycle_health_checker.py` passes clean.
- `uv run mypy scripts/agent/http_lifecycle_health_checker.py` passes (no new regressions vs pre-existing errors).

## Out of scope

- Using `HEALTH_RECHECK_INTERVAL_SEC` in `http_lifecycle.py` — handled in the next procedure document (REQ-005).
- Making the recheck interval configurable via `McpServerConfig` — explicitly out of scope per the Plan.
- Adding unit tests for this file — handled in the next procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260915-102515_refactor_http_lifecycle_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-140327_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-140327
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py
