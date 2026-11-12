## Goal

Add tests to `tests/eventbus/test_eventbus_health.py` asserting that a terminal-failed `dlq_outbox` row surfaces as a `dlq_outbox_failed` reason with the count, that a failing `_dlq_loop` cycle surfaces as a `dlq_sweep_failing` reason with the stored result, that both keep HTTP 503 while leaving `liveness`/`readiness` unchanged, and that `/health` still rejects non-Monitoring roles (`REQ-005` / `AC-5`).

## Scope
**Release unit**: eventbus-health-observability (user-approved 2026-11-12: the count function, loop recording, route, and tests cannot be validated alone; full suite and diff-cover run once after seq 04)

## Assumptions
- The sibling route change (`scripts/eventbus/health_route.py`, seq 03) adds `terminal_failed_outbox` and `last_dlq_sweep` fields and the two degraded reasons before this test runs.
- Step 3a corrections (2026-11-12): the existing `client` fixture builds the app with a single shared `auth_token`, which holds the control-plane roles and always passes `/health`, so a 403 test needs a role-scoped client. `tests/eventbus/eventbus_helpers.py` already provides `make_eventbus_client(tmp_path, monkeypatch, default_role=...)` (a role-scoped `TestClient`, entered as a context manager) and `eventbus_auth_headers(role)`; `eventbus_test_config` takes no `port` or token keywords, so the earlier draft's `eventbus_test_config(tmp_path, port=..., **tokens)` and its generator-returning `_client` factory are not used.
- A `failed` outbox row requires a parent `events` row (`dlq_outbox.event_id REFERENCES events(event_id)`; `events` requires `event_id`, `topic`, `payload`, `producer`, `published_at`), so the test inserts an event first. The live connection is shared with the route through `asyncio.to_thread` (`check_same_thread=False`), so the insert holds `eventbus.db_conn.get_db_lock()`.
- The real `_dlq_loop` starts with the app and records a cycle result shortly after startup, which would race with a test that writes `app.state.last_dlq_cycle_*` directly. The role-scoped fixture therefore replaces `eventbus.app._dlq_loop` with an idle coroutine before the app starts (`dlq_task` still runs, so liveness stays true), and the loop's own recording is tested separately by driving one cycle.

## Design decisions
- One fixture `monitoring_client` (new) wraps `make_eventbus_client(..., default_role="monitoring")` and the idle-loop patch; the 403 test overrides the header per request with `eventbus_auth_headers("operator")`.
- Create the `failed` row with two `INSERT`s on `eb_app.app.state.db` under the DB lock; this exercises the real `count_failed_outbox` query end to end.
- Simulate a failing sweep by writing `eb_app.app.state.last_dlq_cycle_result = "failed"` (and a time) on `app.state`; the idle loop never overwrites it.
- Drive `_dlq_loop` for exactly one cycle by replacing the module's `asyncio` with a stub whose `sleep` raises, so the `ok` and `failed` recordings (REQ-005 in `app.py`) are covered without waiting for the 60 s interval.

## Alternatives considered
- Polling until the first real cycle finishes before overriding `app.state`: rejected - a timing poll; the idle-loop patch is deterministic.
- Reusing the shared `client` fixture for the role-rejection test: rejected - its token holds the control-plane roles, so it can never produce a 403.

## Implementation
### Target file
`tests/eventbus/test_eventbus_health.py`

### Procedure
1. Add `from tests.eventbus.eventbus_helpers import eventbus_auth_headers, make_eventbus_client` (the import form `tests/eventbus/test_eventbus_ack_endpoint.py` uses) and the stdlib imports the tests need (`types`, `Any`).
2. Add the fixture `monitoring_client` (new) after `client`, and the helper `_insert_failed_outbox` (new).
3. In `TestHealth`, add the tests below; add `TestDlqLoopRecording` (new) for the loop recording.
4. Do not modify or remove any existing test.

### Method
```python
def _insert_failed_outbox(db: Any) -> None:
    """Insert one event and a terminal 'failed' dlq_outbox row (under the DB lock)."""
    from eventbus.db_conn import get_db_lock
    from eventbus.json_utils import now_iso

    with get_db_lock():
        db.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at) "
            "VALUES ('evt-health-failed', 't', '{}', 'test', ?)",
            (now_iso(),),
        )
        db.execute(
            "INSERT INTO dlq_outbox (event_id, requested_at, status, attempts) "
            "VALUES ('evt-health-failed', ?, 'failed', 3)",
            (now_iso(),),
        )
        db.commit()


@pytest.fixture
def monitoring_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from eventbus import app as eb_app

    async def _idle_dlq_loop(app: Any) -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(eb_app, "_dlq_loop", _idle_dlq_loop)
    with make_eventbus_client(tmp_path, monkeypatch, default_role="monitoring") as c:
        yield c
```

Tests in `TestHealth` (each uses `monitoring_client` (new)): healthy payload reports `terminal_failed_outbox == 0`, `last_dlq_sweep == {"result": "not_run", "time": None}` and status 200; a terminal-failed row gives 503 with `terminal_failed_outbox >= 1` and `dlq_outbox_failed`; a `failed` sweep result gives 503 with `last_dlq_sweep.result == "failed"` and `dlq_sweep_failing`; both together leave `liveness`/`readiness` true and `is_ready(...)` true; `monitoring_client.get("/health", headers=eventbus_auth_headers("operator"))` gives 403.

`TestDlqLoopRecording` (new): a helper runs `eb_app._dlq_loop(eb_app.app)` for one cycle through `asyncio.run` with `monkeypatch.setattr(eb_app, "asyncio", types.SimpleNamespace(sleep=_raise_stop))`; one test asserts `ok` and a `Z`-suffixed time after a clean cycle, another patches `eb_app.sweep_orphans` to raise `sqlite3.OperationalError` and asserts `failed` and a time.

### Details
- Every test that changes `app.state.last_dlq_cycle_*` restores `not_run`/`None` in a `finally` block so other tests observe the default.
- `eventbus_auth_headers("operator")` presents the Operator token, which lacks `MONITORING`, so `require_role(Role.MONITORING)` returns 403 (verify at run time; if it returns 200, use the publisher token and record the correction).
- The loop tests use the started app (`monitoring_client` (new)) for a real `app.state.config`/`db` and never wait on the 60 s interval.

## Compatibility considerations
- Purely additive: four new tests and two new helpers/fixtures. No existing test renamed or removed; the existing `client` fixture is untouched.
- The new role-scoped fixture builds its own app instance; teardown cancels the DLQ task via the normal `TestClient` context manager, matching `client`.

## Security considerations
- Tests present role-scoped tokens to verify the `/health` role gate; the Operator token must NOT grant MONITORING (asserted implicitly by the 403). No secrets are persisted.

## Rollback considerations
- N/A: revert the commit; the added tests and fixtures are isolated to this file.

## Validation plan
- `uv run pytest tests/eventbus -v` — the four new tests pass; the ten existing health tests, shutdown tests, and DLQ outbox tests still pass.
- `uv run ruff format tests/eventbus/test_eventbus_health.py`, `uv run ruff check tests/eventbus/test_eventbus_health.py` — clean.
- `uv run mypy tests/eventbus/test_eventbus_health.py` — passes.
- `uv run python tools/check_module_size.py` — module stays under the size gate.

## Completion criteria
- `test_health_reports_terminal_failed_outbox` (new) asserts 503, `terminal_failed_outbox >= 1`, and `dlq_outbox_failed` in `degraded_reasons`.
- `test_health_reports_failing_sweep` (new) asserts 503, `last_dlq_sweep.result == "failed"`, and `dlq_sweep_failing` in `degraded_reasons`.
- `test_new_degraded_reasons_do_not_change_liveness_or_readiness` (new) asserts both reasons coexist with `liveness`/`readiness` still `True` and `is_ready(...) is True`.
- The healthy-path test and the two `_dlq_loop` recording tests (new) pass.
- `test_health_rejects_non_monitoring_role` (new) asserts HTTP 403 for the Operator token.
- `ruff format`, `ruff check`, `mypy`, `check_module_size.py` pass; the full `tests/eventbus` suite passes.

## Out of Scope
- The route change that produces these fields and reasons — sibling procedure (`scripts/eventbus/health_route.py`, seq 03).
- Adding `count_failed_outbox` to `dlq_repo.py` — sibling procedure (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-141757 | 20261112-141757 | Changed: tests/eventbus/test_eventbus_health.py (fixtures monitoring_client/real_dlq_loop, 6 health tests, 2 loop-recording tests). Step 3b: rewrote method (make_eventbus_client, idle loop patch, DB lock) |
| 2 | Add or update tests per Validation plan | Completed | 20261112-141757 | 20261112-141757 | 18 passed in tests/eventbus/test_eventbus_health.py (ordered and random) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261112-141757 | 20261112-144314 | 3e passed (ruff, mypy, mock-patch targets); end-of-unit full suite next End-of-unit run (seq 01-04): full suite 12101 passed, 3 failed (tests/mcp_servers mdq-server import tests: mdq database schema message, unrelated, failed in every run); one earlier run also failed tests/eventbus/test_eventbus_dlq_outbox.py::test_restart_with_pending_rows (timing, not reproducible: 20 isolated runs pass, passed in the final run); diff-cover 100% (23 lines) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261112-144314 | 20261112-144314 | N/A: documentation is covered by sibling procedures seq 09, 10, 11 |

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
- **Requirement ID**: `REQ-005` — `/health` outbox and sweep reporting tests (count, reasons, 503 rule, liveness/readiness unchanged, role checks)
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `tests/eventbus/test_eventbus_health.py`