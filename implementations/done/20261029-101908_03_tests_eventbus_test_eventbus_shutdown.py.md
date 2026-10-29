## Goal

Pin that two sequential production lifespans in one process work: the second opens a new, usable connection, the closed first connection is never reused, and the shutdown flag does not leak (`REQ-003`).

## Scope

Add one test and one import to `tests/eventbus/test_eventbus_shutdown.py`. No change to existing tests; no production code.

## Assumptions

- Source claims re-verified this cycle: `test_shutdown_clears_app_state_db` (line 233) and `test_second_lifecycle_does_not_inherit_shutdown_flag` (line 255) already drive `eb_app.lifespan(eb_app.app)` and cover the cleared connection reference and the cleared flag; neither asserts that the second lifecycle holds a different, usable connection. `_make_config`, `_SCHEMA_PATH`, and the `monkeypatch` setup (`load_config`, `get_schema_path`, `_DLQ_INTERVAL = 3600.0`) are the pattern those tests use.
- `lifespan()` clears the shutdown flag at start (`scripts/eventbus/app.py:72`) and `_shutdown_lifespan()` sets `app.state.db` to `None` after closing (`app.py` after line 133), so the first connection object is captured inside the first `async with` block.
- Existing imports are `asyncio`, `threading`, `Path`, `Any`, `cast`, `pytest`, and `FastAPI`; `sqlite3` is not imported and is added.
- Overlap: `plans/20261029-092617_eventbus004_test-requirement-id-cleanup.md` edits `REQ-` comments in this file; compatible (different regions); this row lands first.

## Design decisions

- Capture first_db inside the first lifespan and assert on identity and on a closed-connection error after exit; use `run_with_db_lock` for the second connection's query, the same entry point production routes use.
- Append the test after the last existing test; do not extend the two existing tests, to keep their narrow intent.

## Alternatives considered

- Extending `test_second_lifecycle_does_not_inherit_shutdown_flag`: rejected, it would blur two intents; the new test also covers the flag through the working `run_with_db_lock` call.

## Implementation

### Target file

`tests/eventbus/test_eventbus_shutdown.py`

### Procedure

1. Add `import sqlite3` to the import block after `import asyncio`.
2. Append `test_second_lifecycle_opens_new_usable_connection` (new) at the end of the file, as in Method.

### Method

```python
@pytest.mark.asyncio
async def test_second_lifecycle_opens_new_usable_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two sequential lifespans: the second opens a new connection and never reuses
    the closed first one, and the shutdown flag does not leak into it."""
    from eventbus import app as eb_app
    from eventbus.route_helpers import run_with_db_lock

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)

    async with eb_app.lifespan(eb_app.app):
        first_db = eb_app.app.state.db
    async with eb_app.lifespan(eb_app.app):
        second_db = eb_app.app.state.db
        assert second_db is not None
        assert second_db is not first_db
        assert await run_with_db_lock(
            lambda: second_db.execute("SELECT 1").fetchone()[0]
        ) == 1

    with pytest.raises(sqlite3.ProgrammingError):
        first_db.execute("SELECT 1")
```

### Details

- first_db is closed by the first shutdown; `sqlite3.ProgrammingError` ("Cannot operate on a closed database") is the closed-connection signal.
- The `run_with_db_lock` call succeeds only if the shutdown flag was cleared at the second startup.

## Compatibility considerations

N/A: test-only addition; existing tests are untouched.

## Security considerations

N/A: no credentials or tokens involved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_shutdown.py -v` (repeat 3x).
2. Confirm the test fails if the second lifecycle reuses the first connection (temporarily assert `second_db is first_db`).
3. `uv run pytest tests/eventbus`; `uv run ruff check tests/eventbus`; `uv run ruff format --check tests/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.
4. `uv run python tools/stale_detector.py implementations/20261029-101908_03_tests_eventbus_test_eventbus_shutdown.py.md`.

## Completion criteria

- `test_second_lifecycle_opens_new_usable_connection` (new) exists and passes deterministically.
- It asserts a different second connection, a working query through `run_with_db_lock`, and a closed first connection.
- Existing tests pass unchanged; ruff, format, and mypy are clean.

## Out of Scope

- The health fixture (seq 01), the shared helper (seq 02), the `REQ-` comment cleanup (`eventbus004`), and the `/subscribe` restart scenarios of `ebresumetest004`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `sqlite3` import and the two-lifecycle test (Implementation > Procedure/Method/Details) | Completed | 20261029-131310 | 20261029-131310 |  |
| 2 | Run the new and existing shutdown tests (Validation plan) | Completed | 20261029-131310 | 20261029-131310 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-131310 | 20261029-131310 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Tests-only row |

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
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261029-090402_eventbus003_test-lifecycle-production-path.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-092424_eventbus003_test-lifecycle-production-path.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101908
- **Related target files**: `tests/eventbus/test_eventbus_shutdown.py`