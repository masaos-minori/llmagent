## Goal

Split `_is_stale_update()`'s two invalid-timestamp raise sites into distinct
`ValueError` subclasses so callers can distinguish an invalid incoming timestamp from
an invalid stored timestamp programmatically instead of parsing the message string
(REQ-003; AC-03).

## Scope

Introduce `InvalidIncomingTimestampError` and `InvalidStoredTimestampError` as narrow
`ValueError` subclasses in `scripts/rag/ingestion/etag_manager.py` and raise the
appropriate one at the two `_is_stale_update()` sites (lines 60, 76). Keep the
staleness comparison (`new_dt < stored_dt`) and the empty / missing-timestamp return
paths (`False`) byte-for-byte behaviorally unchanged.

## Assumptions

- Single caller chain: `document_manager.py:112` builds `ETagManager(self._db, doc_id)`
  and calls `.update()`, which invokes `_is_stale_update()`. No other construction site
  exists under `scripts/` (confirmed via `rg 'ETagManager\(' scripts/`).
- The new exceptions subclass `ValueError`, so every existing `except (...ValueError)`
  handler (`document_manager.py:136`, `:159`) continues to catch them without edit.
- The two raise sites are mutually exclusive in practice (the incoming parse precedes
  the stored parse), so a single invalid value maps to exactly one subclass.
- External systems consume ingested documents, not the internal `ValueError` messages,
  so changing exception types does not break an external contract.

## Design decisions

- Two subclasses of `ValueError` (not bare `Exception`): preserves backward
  compatibility with broad `except ValueError` handlers while enabling type-level
  distinction.
- Names `InvalidIncomingTimestampError` / `InvalidStoredTimestampError` mirror the
  existing message text ("Invalid incoming timestamp" / "Invalid stored timestamp").
- Narrow subclasses carry no extra fields beyond the default `ValueError` args; the
  message already encodes the offending value.

## Alternatives considered

- Option (a) — formalize a single shared `ValueError` in documentation only: declined
  by owner (REQ-002 superseded); not implemented.
- Broader base (`Exception`) or a custom hierarchy root: rejected as unnecessary
  expansion — `ValueError` already signals a bad argument and is caught by existing
  handlers.

## Implementation

### Target file

`scripts/rag/ingestion/etag_manager.py`

### Procedure

1. Define the two subclasses directly above the `ETagManager` class (module level).
2. Replace the raise at line 60 (invalid incoming) with `raise
   InvalidIncomingTimestampError(...)`.
3. Replace the raise at line 76 (invalid stored) with `raise
   InvalidStoredTimestampError(...)`.
4. Do not touch the `return False` paths (lines 51-52, 67-68) or the comparison on
   line 78.

### Method

1. `rg -n "_is_stale_update|raise ValueError" scripts/rag/ingestion/etag_manager.py`
   to reconfirm the two sites at their current line numbers.
2. Read the surrounding `update()` / `_is_stale_update()` bodies to confirm the exact
   f-string payloads currently interpolated.
3. Insert the two class definitions before `class ETagManager:`.
4. Edit the two `raise ValueError(...)` statements to reference the matching subclass,
   preserving the original message payload verbatim.
5. Re-run `rg` to confirm no bare `raise ValueError(f"Invalid ... timestamp")` remains.

### Details

Class definitions (module level, above `ETagManager`):

```python
class InvalidIncomingTimestampError(ValueError):
    """Raised when the incoming fetched_at timestamp fails to parse."""


class InvalidStoredTimestampError(ValueError):
    """Raised when a stored fetched_at timestamp fails to parse."""
```

Site 1 (was line 60):

```python
raise InvalidIncomingTimestampError(f"Invalid incoming timestamp: {new_fetched_at}")
```

Site 2 (was line 76):

```python
raise InvalidStoredTimestampError(f"Invalid stored timestamp: {stored_fetched_at}")
```

## Compatibility considerations

Existing `except ValueError` handlers catch the new subclasses because they inherit
`ValueError`. No caller edit is required; audit `document_manager.py:136` / `:159`
confirms neither handler checks the exact exception type. Docs updated separately
(rows 2-3).

## Security considerations

Fail-closed semantics are preserved: both cases still raise rather than silently
accepting a corrupt timestamp. The offending value is interpolated into the message —
this interpolation already existed before this change, so the log-injection exposure is
unchanged (the value originates from DB-stored or HTTP `Last-Modified` data, as before).

## Rollback considerations

Revert the two `raise` statements to bare `ValueError` and delete the two class
definitions. Tests asserting the subclass distinction fail and must be re-run.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/rag/ingestion/etag_manager.py` | Format + lint | `uv run ruff format scripts/rag/ingestion/etag_manager.py` then `uv run ruff check scripts/rag/ingestion/etag_manager.py` | Clean |
| `scripts/rag/ingestion/etag_manager.py` | Type check | `uv run mypy scripts/rag/ingestion/etag_manager.py` | Pass |
| `scripts/rag/ingestion/etag_manager.py` | Security lint | `uv run bandit scripts/rag/ingestion/etag_manager.py` | No new findings |
| `tests/rag/ingestion/test_ingester_etag_guard.py` | Regression + type distinction | `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py` | All pass |
| Whole affected suite | Diff-scoped coverage | `uv run coverage run -m pytest tests/` -> `uv run coverage xml` -> `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% on changed lines |

## Completion criteria

- An invalid incoming timestamp raises `InvalidIncomingTimestampError`; an invalid
  stored timestamp raises `InvalidStoredTimestampError`; both are `ValueError`
  instances.
- Existing etag-guard tests still pass, including `test_invalid_timestamp_raises_value_error`
  (which asserts the base `ValueError`).
- Staleness comparison and empty / missing-timestamp return paths are behaviorally
  unchanged.
- `ruff` / `mypy` / `bandit` clean; `diff-cover` >= 90% on changed lines.

## Out of scope

Caller code changes (audit only; none expected). Documentation updates (rows 2-3).
Empty-string `new_fetched_at` handling (unchanged).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: doc edits are rows 2-3 |

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
- **Requirement ID**: `REQ-003` — split the two `_is_stale_update()` raise sites into distinct `ValueError` subclasses
- **Source issue**: issues/20260930-135010_etagexc01_etagmanager-_is_stale_update-exception-type-distinction-unresolved.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-203101
- **Related target files**: scripts/rag/ingestion/etag_manager.py
