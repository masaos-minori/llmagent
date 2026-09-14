## Goal

Ensure `ProcessTerminator.terminate_with_timeout` accepts all callers' parameters and has
a logger import available. Per REQ-001, REQ-002.

## Scope

- Modify exactly one file: `scripts/agent/http_lifecycle_process_terminator.py`
- Verify `terminate_with_timeout` signature accepts parameters from both callers:
  - `HttpServerLifecycleManager._terminate_with_timeout`: `(proc, server_key, timeout)`
  - `ShutdownCoordinator.shutdown_all`: `(proc, server_key, _SHUTDOWN_TIMEOUT_SEC)`
- Ensure logger import is present for warning/info log statements

## Assumptions

- `terminate_with_timeout`'s current signature `(proc, server_key, timeout)` is sufficient
  for both callers (confirmed: both pass positional args in same order)
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Keep `terminate_with_timeout` signature unchanged — it already accepts all required params
- Add `from shared.logger import Logger` import if the file uses the custom Logger class
  (currently uses `logging.getLogger(__name__)` which may be insufficient)

## Alternatives considered

- Changing `terminate_with_timeout` signature to accept additional params: rejected —
  current signature already covers both callers' needs
- Using `logging.getLogger(__name__)` vs `shared.logger.Logger`: confirmed that the file
  currently uses `logger = logging.getLogger(__name__)` and calls `logger.info/warning`;
  adding `from shared.logger import Logger` would require changing all logger calls

## Implementation

### Target file

`scripts/agent/http_lifecycle_process_terminator.py`

### Procedure

1. **Verify `terminate_with_timeout` signature compatibility**:
   - Confirm both callers pass `(proc, server_key, timeout)` in the correct order
   - Current signature: `async def terminate_with_timeout(self, proc: object, server_key: str, timeout: float = 5.0)`
   - Caller 1 (`HttpServerLifecycleManager`): `await self._process_terminator.terminate_with_timeout(proc, server_key, timeout)` — matches
   - Caller 2 (`ShutdownCoordinator`): `await terminator.terminate_with_timeout(proc, server_key, _SHUTDOWN_TIMEOUT_SEC)` — matches

2. **Add logger import if needed**:
   - Currently has `import logging` and `logger = logging.getLogger(__name__)` at line 17
   - Check if the project convention requires `from shared.logger import Logger` instead
   - If so, add the import and replace `logger.info/warning` calls with `Logger.info/warning` usage

### Method

1. Read `http_lifecycle_process_terminator.py` to confirm current logger usage pattern
2. Read other files in the project to determine whether `from shared.logger import Logger` is the convention
3. If convention requires it, add the import and update logger calls; otherwise leave as-is
4. Verify no parameter mismatches between callers and the method signature

### Details

**Step 1 — Signature verification:**

Current signature:
```python
async def terminate_with_timeout(
    self, proc: object, server_key: str, timeout: float = 5.0
) -> None:
```

Caller 1 (`http_lifecycle.py`):
```python
await self._process_terminator.terminate_with_timeout(proc, server_key, timeout)
```
- `proc: subprocess.Popen[bytes]` → `proc: object` ✓ (subtype compatible)
- `server_key: str` → `server_key: str` ✓
- `timeout: float` → `timeout: float` ✓

Caller 2 (`http_lifecycle_shutdown_coordinator.py`):
```python
await terminator.terminate_with_timeout(proc, server_key, _SHUTDOWN_TIMEOUT_SEC)
```
- Same parameter types ✓

No signature changes needed.

**Step 2 — Logger import:**

Currently has:
```python
import logging
...
logger = logging.getLogger(__name__)
```

Check whether the project convention requires `from shared.logger import Logger`.
If yes, add:
```python
from shared.logger import Logger
```
And replace all `logger.info(...)` / `logger.warning(...)` calls accordingly.

If no (standard library `logging` is acceptable), no changes needed.

## Compatibility considerations

- No public API changes to `ProcessTerminator` — method signature unchanged
- Timeout default preserved: `timeout: float = 5.0` (TERMINATE_TIMEOUT_SEC value)

## Security considerations

N/A: no security-sensitive operations introduced.

## Rollback considerations

- Revert any added imports or logger changes to restore original state
- No data loss risk — only import-level changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_process_terminator.py | Type check — verify mypy passes after any changes | `uv run mypy scripts/agent/http_lifecycle_process_terminator.py` | Clean (no errors) |
| scripts/agent/http_lifecycle_process_terminator.py | Import check — verify shared.logger import resolves | `uv run python -c "from agent.http_lifecycle_process_terminator import ProcessTerminator"` | No ImportError |

## Completion criteria

- [x] `terminate_with_timeout` signature verified compatible with both callers
- [x] Logger import decision documented (standard library `logging` sufficient, no change needed)
- [x] mypy passes on `scripts/agent/http_lifecycle_process_terminator.py`
- [x] Import resolves without error

## Out of scope

- Modifying `terminate_with_timeout`'s internal logic (unchanged — single source of truth)
- Changing timeout defaults
- Adding new error handling paths

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260914-120400 | Verified signature compatibility with both callers; no changes needed |
| 2 | Add or update tests per Validation plan | N/A | — | — | No changes made |
| 3 | Run the validation sequence (rules/toolchain.md) | N/A | — | — | No changes made |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No changes needed |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260913-171806_duplicate_sigterm_sigkill_escalation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-215028_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-105630
- **Related target files**: scripts/agent/http_lifecycle_process_terminator.py
