## Goal

Make the health `client` fixture start and stop the application only through the production lifespan, removing the hand-built state that initializes a second, orphaned connection and broker (`REQ-001`: no `_init_state`/`_do_cleanup`, one connection and one broker per test).

## Scope

Modify `tests/eventbus/test_eventbus_health.py` only: the fixture, the two helper functions it uses, and the import that becomes unused. No assertion in any test changes. The shared helper (seq 02) and the lifecycle test (seq 03) are separate documents; no production code.

## Assumptions

- Source claims re-verified this cycle: `_init_state` (line 17) opens a connection and a broker on a throwaway event loop; `_do_cleanup` (line 32) closes them by hand; the `client` fixture (line 48) calls `_init_state` (line 71) and then enters `with TestClient(eb_app.app) as c` (line 75), so `lifespan()` in `scripts/eventbus/app.py:70` opens and assigns a second pair; after the `with` block `_shutdown_lifespan()` sets `app.state.db` to `None`, so `_do_cleanup` has no connection left to close.
- Removing the hand-built state cannot change what a test sees: `lifespan()` overwrites config, database, envelope schema, broker, and token maps from the patched `load_config`, which still returns the same `cfg`.
- Two tests set `app.state.dlq_task = None` after cancelling it (`test_gate_predicate_is_false_when_db_unavailable_or_dlq_task_stopped`, `test_health_503_when_dlq_task_stopped`); `_shutdown_lifespan()` skips a `None` task, as `_do_cleanup` did, so teardown is unchanged for them. `test_health_degraded_when_db_unavailable` replaces `app.state.db` with a mock and does not restore it; the lifespan closes the mock and the real connection is left to garbage collection, exactly as before (not fixed here).
- `asyncio` and `sqlite3` stay used by the tests (lines 39, 111, 154, 191); `Any` is used only by `_init_state`, so its import becomes unused and is removed.
- Overlap: `plans/20261029-092617_eventbus004_test-requirement-id-cleanup.md` edits one comment in this file (the `REQ-005` label); compatible (different lines), land this row first.

## Design decisions

- The fixture keeps the config, the three `monkeypatch.setattr` calls, and the `Authorization` header; it becomes `with TestClient(eb_app.app) as c: ...; yield c` with nothing after the block.
- No replacement helper is introduced; the shared lifecycle fixture work belongs to seq 02 and to `plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md`.

## Alternatives considered

- Reusing `make_eventbus_client()` in this file: rejected, the health config uses a single `auth_token` and would change the roles the tests present.

## Implementation

### Target file

`tests/eventbus/test_eventbus_health.py`

### Procedure

1. Open `tests/eventbus/test_eventbus_health.py`.
2. Delete `async def _init_state` (line 17) and `async def _do_cleanup` (line 32) in full.
3. In the `client` fixture, delete the `# Initialize app.state before creating TestClient` block that runs `_init_state` on a new event loop (lines 66-73) and the `# Cleanup on teardown` block that runs `_do_cleanup` (lines 78-85).
4. Remove `from typing import Any` (line 11); keep `asyncio`, `sqlite3`, `Path`, `pytest`, and `TestClient`.

### Method

Resulting fixture shape (the config and patch lines are unchanged):

```python
@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(...)  # unchanged
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (...)  # unchanged
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    # The production lifespan starts the app and its shutdown sequence stops it.
    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
        yield c
```

### Details

- Do not touch any test body; the `Path(__file__)...` schema path expression stays because the patch uses it.
- After the edit, `rg "_init_state|_do_cleanup" tests/eventbus/test_eventbus_health.py` must return nothing.

## Compatibility considerations

Test behavior is unchanged: every assertion still runs against a lifespan-started app with the same config and token. The only change is the removal of one orphaned connection and broker per test.

## Security considerations

N/A: test fixture token only.

## Rollback considerations

N/A: revert the commit (single-file test change).

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_health.py -v` (repeat 3x; the module shares global state).
2. `uv run pytest tests/eventbus`.
3. `uv run ruff check tests/eventbus`; `uv run ruff format --check tests/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.
4. `uv run python tools/stale_detector.py implementations/20261029-101908_01_tests_eventbus_test_eventbus_health.py.md`.

## Completion criteria

- The file has no `_init_state` or `_do_cleanup`, and its fixture is `with TestClient(eb_app.app) as c`.
- Each test opens exactly one connection and one broker (through the lifespan only).
- All health tests pass with no assertion change; ruff, format, and mypy are clean (no unused `Any`).

## Out of Scope

- The shared helper (seq 02), the lifecycle test (seq 03), the `REQ-005` comment (`eventbus004`), and the mock-database leak noted in Assumptions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the helpers and hand-built setup and teardown from the fixture (Implementation > Procedure/Method/Details) | Pending | — | — | |
| 2 | Run the health tests and the package tests (Validation plan) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261029-090402_eventbus003_test-lifecycle-production-path.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-092424_eventbus003_test-lifecycle-production-path.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101908
- **Related target files**: `tests/eventbus/test_eventbus_health.py`
