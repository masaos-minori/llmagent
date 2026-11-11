## Goal

Add tests to `tests/eventbus/test_eventbus_health.py` asserting that a terminal-failed `dlq_outbox` row surfaces as a `dlq_outbox_failed` reason with the count, that a failing `_dlq_loop` cycle surfaces as a `dlq_sweep_failing` reason with the stored result, that both keep HTTP 503 while leaving `liveness`/`readiness` unchanged, and that `/health` still rejects non-Monitoring roles (`REQ-005` / `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The sibling route change (`scripts/eventbus/health_route.py`, seq 03) adds `terminal_failed_outbox` and `last_dlq_sweep` fields and the two degraded reasons before this test runs.
- The existing `client` fixture (lines 16-40) builds the app with a single shared `auth_token`, so `"test-token"` holds every control-plane role and always passes `/health`; a role-rejection test needs a **role-scoped** client.
- `tests/eventbus/eventbus_helpers.py` provides `eventbus_test_tokens()` (each role gets a distinct token granting exactly its role) and `eventbus_auth_headers(role)` (the `Authorization` header for one role).
- A `failed` outbox row requires a parent `events` row (foreign key `dlq_outbox.event_id REFERENCES events(event_id)`), so the test inserts an event first.

## Design decisions
- Add a small role-scoped client fixture next to `client` that builds the app via `eventbus_test_config(...)` and exposes `eventbus_auth_headers`, so each new test presents exactly the role it wants to exercise.
- Create the `failed` row by executing two `INSERT`s against `eb_app.app.state.db` (the same connection the route reads) and committing; this exercises the real `count_failed_outbox` query end-to-end.
- Simulate a failing sweep by writing `eb_app.app.state.last_dlq_cycle_result = "failed"` (and an ISO time) directly on `app.state` — no need to drive the background loop.

## Alternatives considered
- Driving `_dlq_loop` to failure by mocking `sweep_orphans`: rejected — setting `app.state.last_dlq_cycle_result` directly tests the exact contract `/health` reads and is deterministic.
- Reusing the shared `client` fixture for the role-rejection test: rejected — its single token holds all control-plane roles, so it can never produce a 403.

## Implementation
### Target file
`tests/eventbus/test_eventbus_health.py`

### Procedure
1. Import the helpers at the top: `from tests.eventbus.eventbus_helpers import eventbus_test_config, eventbus_test_tokens, eventbus_auth_headers` (adjust the import path to match how `eventbus_helpers` is imported elsewhere in `tests/eventbus/`).
2. Add a role-scoped fixture `scoped_client` (new) after `client` that builds the app with `eventbus_test_config(tmp_path, **eventbus_test_tokens())`, yields a `TestClient` with a per-request `Authorization` header selected by a `role` argument, and sets the schema-path monkeypatches like `client`.
3. In `TestHealth`, add the four tests below.
4. Do not modify or remove any existing test.

### Method
Helper to create a terminal-failed outbox row on the live DB:
```python
def _insert_failed_outbox(db: Any) -> None:
    """Insert one event and a terminal 'failed' dlq_outbox row for health tests."""
    from eventbus.json_utils import now_iso

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
```

Role-scoped fixture:
```python
@pytest.fixture
def scoped_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from eventbus import app as eb_app

    cfg = eventbus_test_config(
        tmp_path,
        port=8016,
        **eventbus_test_tokens(),
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    def _client(role: str) -> TestClient:
        with TestClient(eb_app.app) as c:
            c.headers.update(eventbus_auth_headers(role))
            yield c

    return _client
```

Tests to append inside `TestHealth`:
```python
    def test_health_reports_terminal_failed_outbox(self, scoped_client) -> None:
        from eventbus import app as eb_app

        _insert_failed_outbox(eb_app.app.state.db)
        resp = scoped_client("monitoring").get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["terminal_failed_outbox"] >= 1
        assert "dlq_outbox_failed" in body["degraded_reasons"]
        # The new reason is a real failure, not a capacity-only one.
        assert body["liveness"] is True
        assert body["readiness"] is True

    def test_health_reports_failing_sweep(self, scoped_client) -> None:
        from eventbus import app as eb_app
        from eventbus.json_utils import now_iso

        eb_app.app.state.last_dlq_cycle_result = "failed"
        eb_app.app.state.last_dlq_cycle_time = now_iso()
        try:
            resp = scoped_client("monitoring").get("/health")
        finally:
            eb_app.app.state.last_dlq_cycle_result = "not_run"
            eb_app.app.state.last_dlq_cycle_time = None
        assert resp.status_code == 503
        body = resp.json()
        assert body["last_dlq_sweep"]["result"] == "failed"
        assert "dlq_sweep_failing" in body["degraded_reasons"]

    def test_new_degraded_reasons_do_not_change_liveness_or_readiness(
        self, scoped_client
    ) -> None:
        from eventbus import app as eb_app
        from eventbus.health_route import is_ready

        _insert_failed_outbox(eb_app.app.state.db)
        eb_app.app.state.last_dlq_cycle_result = "failed"
        try:
            body = scoped_client("monitoring").get("/health").json()
        finally:
            eb_app.app.state.last_dlq_cycle_result = "not_run"
        # Both reasons are present, yet the deployment gate booleans are untouched.
        assert "dlq_outbox_failed" in body["degraded_reasons"]
        assert "dlq_sweep_failing" in body["degraded_reasons"]
        assert body["liveness"] is True
        assert body["readiness"] is True
        assert is_ready(body["liveness"], body["readiness"]) is True

    def test_health_rejects_non_monitoring_role(self, scoped_client) -> None:
        resp = scoped_client("operator").get("/health")
        assert resp.status_code == 403
```

### Details
- `_insert_failed_outbox` (new) commits on the live connection; the route's `count_failed_outbox(db)` then returns `>= 1`. If the fixture's DB is rolled back between requests, re-insert inside each test before the request (as shown).
- The `finally` blocks restore `last_dlq_cycle_result`/`last_dlq_cycle_time` so other tests observe the default `not_run` state.
- `scoped_client("operator")` presents the Operator token, which lacks `MONITORING`, so `require_role(Role.MONITORING)` returns 403 — the same rejection path the existing shared-token tests rely on.

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
- `test_health_rejects_non_monitoring_role` (new) asserts HTTP 403 for the Operator token.
- `ruff format`, `ruff check`, `mypy`, `check_module_size.py` pass; the full `tests/eventbus` suite passes.

## Out of Scope
- The route change that produces these fields and reasons — sibling procedure (`scripts/eventbus/health_route.py`, seq 03).
- Adding `count_failed_outbox` to `dlq_repo.py` — sibling procedure (seq 01).

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
- **Requirement ID**: `REQ-005` — `/health` outbox and sweep reporting tests (count, reasons, 503 rule, liveness/readiness unchanged, role checks)
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `tests/eventbus/test_eventbus_health.py`
