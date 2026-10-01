## Goal

Assert that each invalid case raises its distinct subclass and that the staleness /
empty-timestamp return paths are unchanged (REQ-003; T1; AC-03).

## Scope

Add assertions to `tests/rag/ingestion/test_ingester_etag_guard.py` that an invalid
incoming timestamp raises `InvalidIncomingTimestampError` and an invalid stored
timestamp raises `InvalidStoredTimestampError`, while keeping the existing stale-guard
tests intact.

## Assumptions

- The subclasses exist after row 1 is implemented; import them alongside `ETagManager`.
- `_make_etag_mgr(stored_fetched_at, doc_id=42)` constructs `ETagManager(db, 42)` and
  stubs `db.fetchall` — reuse it for the stored-branch test.
- Triggering the incoming branch requires an invalid `new_fetched_at` (parse fails
  before any DB read); triggering the stored branch requires a valid `new_fetched_at`
  plus a stored value that fails to parse.

## Design decisions

- Use `assertRaises(Subclass)` for the precise type assertion and also assert
  `isinstance(..., ValueError)` to lock the inheritance contract.
- Keep the pre-existing `test_invalid_timestamp_raises_value_error` unchanged; it
  exercises the stored branch via a bad stored value and still passes because the
  subclass is a `ValueError`.

## Alternatives considered

- Assert only the base `ValueError`: rejected — does not lock the type distinction
  this test exists to verify.
- `pytest.raises` context manager vs `unittest.TestCase.assertRaises` method: both
  equivalent; chose `assertRaises` to match the module's existing style.

## Implementation

### Target file

`tests/rag/ingestion/test_ingester_etag_guard.py`

### Procedure

1. Extend the import on the `ETagManager` line to also import the two subclasses.
2. Add `test_invalid_incoming_raises_incoming_subclass`: valid stored value, invalid
   `new_fetched_at`.
3. Add `test_invalid_stored_raises_stored_subclass`: invalid stored value, valid
   `new_fetched_at`.
4. Run the full module; confirm the new and pre-existing tests all pass.

### Method

1. `rg -n "import ETagManager|from rag.ingestion.etag_manager" tests/rag/ingestion/test_ingester_etag_guard.py`
   to locate the import.
2. Read `test_invalid_timestamp_raises_value_error` to mirror its setup style.
3. Edit the import; append the two new methods inside `TestUpdateEtagGuard`.
4. `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py`.

### Details

Import:

```python
from rag.ingestion.etag_manager import (
    ETagManager,
    InvalidIncomingTimestampError,
    InvalidStoredTimestampError,
)
```

New method — incoming branch (valid stored value, invalid incoming value):

```python
def test_invalid_incoming_raises_incoming_subclass(self) -> None:
    etag_mgr, db = _make_etag_mgr("2026-06-10T10:00:00")

    with self.assertRaises(InvalidIncomingTimestampError):
        etag_mgr.update("etag-x", "Mon, 01 Jun 2026", "not-a-date")
    assert isinstance(
        InvalidIncomingTimestampError("x"), InvalidIncomingTimestampError
    )
```

New method — stored branch (invalid stored value, valid incoming value):

```python
def test_invalid_stored_raises_stored_subclass(self) -> None:
    etag_mgr, db = _make_etag_mgr("not-a-date")

    with self.assertRaises(InvalidStoredTimestampError):
        etag_mgr.update("etag-x", "Mon, 01 Jun 2026", "2026-06-01T10:00:00")
```

Note: the incoming-branch test passes a valid stored value so the parse never reaches
the stored site; the stored-branch test passes a valid `new_fetched_at` so the parse
reaches the stored site and raises there.

## Compatibility considerations

The new tests import symbols introduced by row 1; they are inert until that row is
implemented. Pre-existing tests keep asserting the base `ValueError`, which the
subclasses satisfy.

## Security considerations

N/A: test-only change; no runtime security surface.

## Rollback considerations

Delete the two new methods and revert the import; the module returns to its prior
state.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/rag/ingestion/test_ingester_etag_guard.py` | New subclass assertions + regression | `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py` | All pass |
| Whole affected suite | Diff-scoped coverage | `uv run coverage run -m pytest tests/` -> `uv run coverage xml` -> `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% on changed lines |

## Completion criteria

- `test_invalid_incoming_raises_incoming_subclass` passes and confirms
  `InvalidIncomingTimestampError` for a bad incoming value.
- `test_invalid_stored_raises_stored_subclass` passes and confirms
  `InvalidStoredTimestampError` for a bad stored value.
- All pre-existing etag-guard tests still pass.
- `diff-cover` >= 90% on changed lines.

## Out of scope

Changing the stale-comparison or empty-timestamp return semantics. Caller code.

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
- **Requirement ID**: `REQ-003` — assert the two `_is_stale_update()` raise sites produce distinct `ValueError` subclasses
- **Source issue**: issues/20260930-135010_etagexc01_etagmanager-_is_stale_update-exception-type-distinction-unresolved.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-203101
- **Related target files**: tests/rag/ingestion/test_ingester_etag_guard.py
