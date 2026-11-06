## Goal

Add a `caplog` regression test (`REQ-003`) that pins the fixed stale-skip log line:
trigger the stale-skip path and assert exactly one clean INFO record whose rendered
message contains both timestamps and the `doc_id`, with no logging error. Existing 9
tests stay unchanged and green.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `caplog` can capture the module-level `Logger` instance. `Logger` sets
  `propagate=False` on its underlying stdlib logger, so the capture handler must be
  attached to that logger directly — use `caplog.at_level(logging.INFO,
  logger="rag.ingestion.etag_manager")`, which pytest attaches to the named logger
  (same pattern as `tests/db/test_create_schema.py` and
  `tests/integration/test_production_security_regression.py`). If capture yields zero
  records, attach `caplog.handler` to
  `logging.getLogger("rag.ingestion.etag_manager")` directly before the call (as the
  security-regression test does) and remove it after.
- The stale-skip is reached when the stored `fetched_at` is newer than the incoming
  `new_fetched_at` (`_is_stale_update` returns the stored string).

## Design decisions
- **Drive `update()` end-to-end, assert on the captured record.** Build a real
  `ETagManager` via the existing `_make_etag_mgr(stored_fetched_at)` helper with a
  stored timestamp newer than the incoming one, call `update()` inside the
  `caplog.at_level(...)` block, then inspect `caplog.records`.
- **Assert on `record.getMessage()`.** `getMessage()` renders the message with its
  args; asserting it returns a string containing both timestamps and `doc_id=` proves
  the `%`-arg formatting no longer raises `TypeError: not enough arguments`.
- **Exactly-one-record assertion.** `len(caplog.records) == 1` and
  `caplog.records[0].levelno == logging.INFO` pin that the skip path emits a single
  INFO line and nothing else.

## Alternatives considered
- Patching `rag.ingestion.etag_manager.logger` with `unittest.mock.patch` (the pattern
  of the existing 9 tests): works but asserts on the mock, not on real `%`-arg
  rendering. The `caplog` approach pins the actual formatting fix (REQ-003 intent).

## Implementation
### Target file
- `tests/rag/ingestion/test_ingester_etag_guard.py`

### Procedure
1. Add a test method to `TestUpdateEtagGuard` (or a new class) that triggers the
   stale-skip and captures the log via `caplog`.
2. Assert exactly one INFO record, that `getMessage()` formats without raising, and
   that it contains both timestamps and `doc_id=42`.
3. Confirm the 9 existing tests remain unchanged and green.

### Method
- Use a stored timestamp `"2026-06-10T10:00:00"` and an incoming
  `"2026-06-01T10:00:00"` (older) so the update is stale.
- Inside the `caplog.at_level` block call
  `etag_mgr.update("etag-old", "Mon, 01 Jun 2026", "2026-06-01T10:00:00")`.
- Assert on `caplog.records[0].getMessage()`.

### Details
```python
import logging

def test_stale_skip_emits_clean_log_line(self, caplog) -> None:
    etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00")

    with caplog.at_level(logging.INFO, logger="rag.ingestion.etag_manager"):
        etag_mgr.update("etag-old", "Mon, 01 Jun 2026", "2026-06-01T10:00:00")

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == logging.INFO
    text = record.getMessage()  # must render without raising TypeError
    assert "2026-06-01T10:00:00" in text   # incoming timestamp
    assert "2026-06-10T10:00:00" in text   # stored timestamp
    assert "doc_id=42" in text
```
- If `caplog.records` is empty because `propagate=False` suppresses capture, attach the
  handler directly first:
  ```python
  stdlib_logger = logging.getLogger("rag.ingestion.etag_manager")
  old_propagate = stdlib_logger.propagate
  stdlib_logger.propagate = True
  try:
      with caplog.at_level(logging.INFO, logger="rag.ingestion.etag_manager"):
          etag_mgr.update(...)
  finally:
      stdlib_logger.propagate = old_propagate
  ```
- `db.execute` / `db.commit` must not be called on the skip path (add
  `db.execute.assert_not_called()` for extra lock-down, mirroring
  `test_stale_incoming_skips_update`).
- Do not modify any of the 9 existing test methods.

## Compatibility considerations
This document adds a test only; it does not change production behavior. The new test
depends on the `etag_manager.py` change (companion document) landing first, so it fails
RED against current code (the malformed call raises inside logging) and goes GREEN after.

## Security considerations
N/A: test-only addition, no input handling or credential change.

## Rollback considerations
Revert the commit to this test file. The new method is additive and isolated.

## Validation plan
- New test fails against current code (malformed log call) and passes after the
  `etag_manager.py` fix (Phase 1 -> 2).
- `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py -v` passes, incl. the
  9 unchanged guard tests.
- `uv run pytest tests/rag/ingestion` passes.
- Static gates: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll` — clean.

## Completion criteria
- The `caplog` stale-skip test exists, fails against current code, and passes after the
  fix, asserting one INFO record containing both timestamps and `doc_id=42`.
- All 9 existing guard tests remain unchanged and green.

## Out of Scope
- Changing guard decision logic or the other 9 tests.
- Any production-file change (covered by the companion `etag_manager.py` document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `caplog` regression test | Completed | — | 20261106-192106 | REQ-003 RED confirmed on HEAD code (TypeError not enough arguments), GREEN after fix; pytest-style class for caplog fixture |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261106-192106 | 9 guard tests + TestResolveIncomingGuard + ingestion dir all green |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|-------|----------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261106-073538_raging008_etagmanager-stale-log-error.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-103659_raging008_etagmanager-stale-log-error.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-153919
- **Related target files**: `tests/rag/ingestion/test_ingester_etag_guard.py`