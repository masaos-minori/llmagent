## Goal

Add a `sqlite3.Error`-callback regression test (`REQ-002`, `REQ-003`; AC-1, AC-3) to
`tests/rag/ingestion/test_rag_ingester_callback.py`: an `on_ingest_complete` callback that
raises `sqlite3.Error` must be logged and swallowed so `ingest_all(force=False,
on_ingest_complete=...)` returns its consistency report normally (no exception propagates).
The existing happy-path test stays unchanged and green.

## Scope
**Release unit**: callback-catch-widening (Plan Phase 1)

## Assumptions
- The existing `ingester` fixture (`test_rag_ingester_callback.py:55-79`) is reusable: it
  patches `rag.ingestion.ingester.SQLiteHelper` to an in-memory fake and patches
  `rag.ingestion.document_manager.check_rag_consistency` to return a `MagicMock` report,
  so `ingest_all` reaches `check_consistency` → `_invoke_callback` without hitting the
  filesystem or a real DB.
- `check_consistency` returns the mocked report through `ingest_all`; asserting on the
  returned value proves nothing escaped.
- `caplog` captures the module-level logger's ERROR record for the callback failure. If
  capture yields zero records because the logger's propagation differs, attach
  `caplog.handler` to the relevant stdlib logger directly (same pattern as
  `tests/integration/test_production_security_regression.py`) and remove it after.

## Design decisions
- **Drive `ingest_all` end-to-end, assert on the return value and the log.** Build the
  raising callback as a `lambda: (_ for _ in ()).throw(sqlite3.Error("boom"))` (or a small
  function) so it raises `sqlite3.Error` when invoked inside `_invoke_callback`. Call
  `ingest_all(force=False, on_ingest_complete=raising)` inside a `caplog.at_level` block,
  capture the return value, then assert.
- **Assert exactly-one ERROR record with the existing message.** `len([r for r in
  caplog.records if r.levelno == logging.ERROR]) == 1` and the record's message equals
  `"on_ingest_complete callback failed"` pins both the logging and the unchanged message
  (AC-1, AC-2).
- **RED-first.** The test fails against current code (the narrow `except (TypeError,
  ValueError)` does not catch `sqlite3.Error`, so it escapes `ingest_all`) and goes GREEN
  after the companion `document_manager.py` change widens the catch.

## Alternatives considered
- Patching `DocumentManager._invoke_callback` directly: works but asserts on the mock, not
  on the real catch behavior. The end-to-end `ingest_all` call pins the actual fix
  (REQ-002 intent).

## Implementation
### Target file
- `tests/rag/ingestion/test_rag_ingester_callback.py`

### Procedure
1. Add `import logging` to the imports.
2. Add a `test_callback_failure_does_not_break_ingest_all` test function using the existing
   `ingester` fixture.
3. Assert the return value is the mocked report, no exception propagated, and exactly one
   ERROR record with the existing message was logged.
4. Confirm the existing happy-path test `test_ingest_all_calls_on_ingest_complete` stays
   unchanged and green.

### Method
```python
import logging


def test_callback_failure_does_not_break_ingest_all(ingester) -> None:
    """A callback raising sqlite3.Error is logged and swallowed, not propagated."""

    def raising_callback() -> None:
        raise sqlite3.Error("boom")

    mock_chunk_dir = MagicMock()
    mock_chunk_dir.glob.return_value = [MagicMock()]

    with caplog.at_level(logging.ERROR, logger="rag.ingestion.document_manager"):
        with (
            patch.object(ingester, "_chunk_dir", mock_chunk_dir),
            patch.object(type(ingester), "_process_url_groups", return_value=[]),
        ):
            report = ingester.ingest_all(
                force=False, on_ingest_complete=raising_callback
            )

    # Nothing escaped: ingest_all returned its consistency report normally.
    assert report is not None
    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_records) == 1
    assert error_records[0].getMessage() == "on_ingest_complete callback failed"
```
- If `caplog.records` is empty because the module logger's propagation suppresses capture,
  attach the handler directly first:
  ```python
  stdlib_logger = logging.getLogger("rag.ingestion.document_manager")
  old_propagate = stdlib_logger.propagate
  stdlib_logger.propagate = True
  try:
      with caplog.at_level(logging.ERROR, logger="rag.ingestion.document_manager"):
          ...
  finally:
      stdlib_logger.propagate = old_propagate
  ```
- Do not modify `test_ingest_all_calls_on_ingest_complete` or any other existing test.

## Compatibility considerations
This document adds a test only; it does not change production behavior. The new test
depends on the `document_manager.py` change (companion document) landing first, so it fails
RED against current code (the exception escapes) and goes GREEN after.

### Verification results (20261106)
- Verified against current code: the `ingester` fixture exists at
  `test_rag_ingester_callback.py:54-79` (patches `rag.ingestion.ingester.SQLiteHelper` to
  `_FakeSQLiteHelper` and `rag.ingestion.document_manager.check_rag_consistency` to a
  `MagicMock` report) and the happy-path test `test_ingest_all_calls_on_ingest_complete`
  exists unchanged.
- Verified: `except (TypeError, ValueError):` at `document_manager.py:149` does not catch
  `sqlite3.Error`, so the RED expectation holds.
- Execution order: this document runs FIRST (Plan Phase 1 RED), then the companion
  `20261106-155620_01` catch widening (Phase 2 GREEN).
- Executed 20261106: the plain `caplog.at_level` capture returned 0 records because
  `document_manager.logger` is a `shared.logger.Logger` with `propagate=False`
  (`scripts/shared/logger.py:140`); the documented fallback (attach `caplog.handler`
  directly to `document_manager.logger._logger`, remove after) captured the record and
  the test passes.

## Security considerations
N/A: test-only addition, no input handling or credential change.

## Rollback considerations
Revert the commit to this test file. The new test function is additive.

## Validation plan
- New test fails against current code (exception escapes `ingest_all`) and passes after the
  `document_manager.py` fix (Phase 1 → 2).
- `uv run pytest tests/rag/ingestion/test_rag_ingester_callback.py -v` passes, incl. the
  unchanged happy-path test.
- `uv run pytest tests/rag/ingestion` passes.
- Static gates: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll` — clean.

## Completion criteria
- The `sqlite3.Error`-callback regression test exists, fails against current code, and
  passes after the catch widening, asserting the report is returned and one ERROR record
  with the unchanged message was logged.
- The existing happy-path test remains unchanged and green.

## Out of Scope
- Changing the happy-path test or any other existing test.
- Any production-file change (covered by the companion `document_manager.py` document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `sqlite3.Error`-callback regression test | Completed | 2026-11-06 | 2026-11-06 | REQ-002; RED confirmed (sqlite3.Error escaped ingest_all), GREEN after widening |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-06 | 2026-11-06 | 2/2 passed incl. unchanged happy-path test |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261106-073538_raging012_ingest-callback-narrow-catch.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-104959_raging012_ingest-callback-narrow-catch.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-155620
- **Related target files**: `tests/rag/ingestion/test_rag_ingester_callback.py`
