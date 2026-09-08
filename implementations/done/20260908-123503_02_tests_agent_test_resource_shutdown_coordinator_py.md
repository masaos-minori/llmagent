## Goal

Create `tests/agent/test_resource_shutdown_coordinator.py`, a new test module asserting
(a) a healthy shutdown completes well under `_GRACEFUL_TIMEOUT_S` seconds (`REQ-001`),
and (b) no `shutdown_timeout`/`shutdown_error` entries are recorded after the
settlement block's removal (`REQ-002`).

## Scope

- In scope: create the new test file with two focused unit tests against
  `ResourceShutdownCoordinator.close_resources()`.
- Out of scope: modifying `scripts/agent/resource_shutdown_coordinator.py` itself
  (covered by the companion procedure
  `implementations/20260908-123503_01_scripts_agent_resource_shutdown_coordinator_py.md`);
  modifying `tests/agent/test_repl.py`'s existing `TestCloseResourcesWALCheckpoint`
  tests (unaffected — those mock `WalCheckpointManager`'s `SQLiteHelper` at a lower
  layer and don't depend on the settlement block).

## Assumptions

- `tests/agent/test_resource_shutdown_coordinator.py` does not currently exist
  (confirmed: file absent).
- This test file can construct `ResourceShutdownCoordinator` directly (`ctx`, `view`,
  `wal` as lightweight mocks) without going through `AgentREPL`, following the same
  construction pattern `tests/agent/test_repl.py`'s `_make_bare_repl()` uses
  (`ResourceShutdownCoordinator(ctx, view, wal)`).
- These tests remain valid regardless of execution order relative to the companion
  WAL-checkpoint-reorder procedure for the same source file
  (`implementations/20260908-115446_...`) — both mock `wal.checkpoint_sync`/
  `wal.backup_sync` directly rather than asserting on internal call order, so they pass
  whether or not that reorder has been applied.

## Design decisions

- Mock `wal.checkpoint_sync` and `wal.backup_sync` as `AsyncMock` returning immediate
  success (`(True, [])`) rather than exercising the real `WalCheckpointManager`/SQLite
  path — keeps both tests fast and focused on settlement-block behavior specifically,
  consistent with this Plan's Out-of-Scope (WAL checkpoint/backup changes).
- Provide `ctx.services = None` so the service-lifecycle-shutdown branch is skipped
  (`logger.debug("No services available to shut down")`), removing an unrelated
  variable from both tests.
- Assert on wall-clock elapsed time for the healthy-timing test (`REQ-001`), and on
  `logger.error` call arguments for the no-stale-error test (`REQ-002`), matching the
  pattern already used by `tests/agent/test_repl.py`'s
  `test_checkpoint_timeout_records_error_and_still_runs_backup`.

## Alternatives considered

- Add these two tests as new methods on `tests/agent/test_repl.py`'s existing
  `TestCloseResourcesWALCheckpoint` class instead of a new file → rejected: the Plan's
  frozen `Implementation Target Files` table specifies
  `tests/agent/test_resource_shutdown_coordinator.py` as its own New file row, distinct
  from `test_repl.py`.
- Use `_make_bare_repl()`-style full `AgentREPL` construction → rejected: unnecessarily
  couples these two focused tests to the entire REPL's construction surface; direct
  `ResourceShutdownCoordinator(ctx, view, wal)` construction is sufficient and matches
  this Plan's narrow target.

## Implementation

### Target file

`tests/agent/test_resource_shutdown_coordinator.py`

### Procedure

1. Create the new test module with a module docstring identifying its purpose
   (regression coverage for the settlement-block removal, `REQ-001`/`REQ-002`).
2. Add a helper that constructs a minimal `ResourceShutdownCoordinator` with mocked
   `ctx`, `view`, and `wal` (`checkpoint_sync`/`backup_sync` as `AsyncMock` returning
   `(True, [])`).
3. Add `test_healthy_shutdown_completes_promptly`: call `close_resources()`, measure
   elapsed wall-clock time, assert it is well under `_GRACEFUL_TIMEOUT_S` (e.g. `< 1.0`
   second).
4. Add `test_no_shutdown_error_entries_after_settlement_block_removal`: call
   `close_resources()` with `agent.resource_shutdown_coordinator.logger` patched,
   assert no `logger.error` call contains `"shutdown_timeout"` or `"shutdown_error"` in
   its arguments.

### Method

Create — new test module.

### Details

```python
"""tests/agent/test_resource_shutdown_coordinator.py

Regression tests for ResourceShutdownCoordinator.close_resources()'s settlement-block
removal: a healthy shutdown must complete promptly (REQ-001), and no
shutdown_timeout/shutdown_error entries may be recorded once the block is removed
(REQ-002).
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.resource_shutdown_coordinator import ResourceShutdownCoordinator


def _make_coordinator() -> ResourceShutdownCoordinator:
    ctx = MagicMock()
    ctx.services = None
    view = MagicMock()
    wal = MagicMock()
    wal.checkpoint_sync = AsyncMock(return_value=(True, []))
    wal.backup_sync = AsyncMock(return_value=("", []))
    return ResourceShutdownCoordinator(ctx, view, wal)


class TestSettlementBlockRemoved:
    """Regression tests for the removed unconditional settlement-block sleep."""

    @pytest.mark.asyncio
    async def test_healthy_shutdown_completes_promptly(self) -> None:
        """A healthy shutdown (no pending tasks, checkpoint/backup succeed
        immediately) completes well under _GRACEFUL_TIMEOUT_S."""
        coordinator = _make_coordinator()
        start = time.monotonic()
        await coordinator.close_resources()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_no_shutdown_error_entries_after_settlement_block_removal(
        self,
    ) -> None:
        """No shutdown_timeout/shutdown_error entries are recorded — the
        settlement block that used to produce them no longer exists."""
        coordinator = _make_coordinator()
        with patch("agent.resource_shutdown_coordinator.logger") as mock_logger:
            await coordinator.close_resources()
        error_messages = [str(c.args) for c in mock_logger.error.call_args_list]
        assert not any("shutdown_timeout" in msg for msg in error_messages)
        assert not any("shutdown_error" in msg for msg in error_messages)
```

Note: `wal.backup_sync` is stubbed defensively (in case `checkpoint_sync` reports
`truncated_or_ok=False` in some future change), but with `(True, [])` returned by
`checkpoint_sync`, the backup branch is skipped in both tests as currently implemented.

## Compatibility considerations

N/A: this is a new test file; it has no existing callers or consumers to break.

## Security considerations

N/A: test-only code with mocked dependencies; no real credentials, network, or
filesystem access.

## Rollback considerations

- Revert by deleting the new file (`git rm tests/agent/test_resource_shutdown_coordinator.py`).
  No other file depends on it.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_resource_shutdown_coordinator.py | Unit: run the new module directly | `uv run pytest tests/agent/test_resource_shutdown_coordinator.py -v` | Both new tests pass |
| tests/agent/test_resource_shutdown_coordinator.py | Regression: full existing `test_repl.py` suite unaffected | `uv run pytest tests/agent/test_repl.py -x -q` | No new failures |

## Completion criteria

- `tests/agent/test_resource_shutdown_coordinator.py` exists and both tests pass once
  the companion procedure's settlement-block removal is applied.
- Neither test depends on execution order relative to the companion
  WAL-checkpoint-reorder procedure for the same source file.

## Out of scope

- Modifying `scripts/agent/resource_shutdown_coordinator.py` (covered by the companion
  procedure document for that file).
- Testing the WAL checkpoint/backup's own timeout paths (already covered by
  `tests/agent/test_repl.py`'s `TestCloseResourcesWALCheckpoint`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the new test module with both tests per Details | Completed | 2026-09-08TXX:XX:XX | 2026-09-08TXX:XX:XX | File created |
| 2 | Run `uv run pytest tests/agent/test_resource_shutdown_coordinator.py -v` | Completed | 2026-09-08TXX:XX:XX | 2026-09-08TXX:XX:XX | 2 passed |
| 3 | Run `uv run pytest tests/agent/test_repl.py -x -q` to confirm no regression | Completed | 2026-09-08TXX:XX:XX | 2026-09-08TXX:XX:XX | Pre-existing failure excluded |
| 4 | Documentation update — N/A, no `docs/*.md` update required for a new test file | Skipped | — | — | No docs/00_index.md task-scope mapping for tests/ |

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
- **Source issue**: issues/20260907-131900_rsc002b_settlement_sleep_violates_no_regression_criterion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-070835_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-123503
- **Related target files**: tests/agent/test_resource_shutdown_coordinator.py
