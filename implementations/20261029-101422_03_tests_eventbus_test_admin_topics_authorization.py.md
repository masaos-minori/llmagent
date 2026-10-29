## Goal

Add regression tests for the admin update publish order: a failing principal-map build leaves the previous config and principal map active and does not report success (`REQ-003`), and the no-op and effective-update behavior stays pinned (`REQ-004`).

## Scope

Add a test class to `tests/eventbus/test_admin_topics_authorization.py`. No change to existing tests, the `admin_client` fixture, or production code.

## Assumptions

- Source claims re-verified this cycle: `TestValidation.test_invalid_body_rejected_without_corrupting_state` is at line 242 and covers body validation only; `admin_client` (fixture, lines 17-73 and 113-117) returns an unentered `TestClient(eb_app.app)` with `admin_token="admin-tok"`, `consumer_token="consumer-tok"`, and initial `consumer_authorization={"c1": ["topicA"]}`; `principal_map` is imported from `tests.eventbus.eventbus_helpers` at line 14; `pytest`, `Any`, and `TestClient` are already imported.
- Names created by earlier rows: `eventbus.admin_route._build_principal_map` is imported into `admin_route` by seq 02 (created by seq 01); it exists when this row runs.
- A build exception is unhandled by the route, so it yields a 500; the precedent for asserting a 500 is `TestClient(client.app, raise_server_exceptions=False)` in `tests/eventbus/test_eventbus_publish.py:193`.
- The initial `consumer_authorization` equals the body `{"c1": ["topicA"]}`, so that body is a no-op on a fresh fixture.
- Overlap: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md` extends the two audit tests (lines 188-213) in this file, and `plans/20261029-092617_eventbus004_test-requirement-id-cleanup.md` edits comments in it. Judgment: compatible (different regions; this row only appends a class), sequencing: land after `ebaudit005`, before `eventbus004`.

## Design decisions

- Patch the helper where `admin_route` imports it (`eventbus.admin_route._build_principal_map`), because the handler resolves the module-level name; `tools/check_mock_patch_targets.py` confirms the target.
- Assert object identity (`is`) for `app.state.config` and `principal_map()` so "unchanged" means "not republished", not merely "equal".

## Alternatives considered

- `pytest.raises` through the default `TestClient`: rejected, it depends on whether an exception handler swallows the error; the `raise_server_exceptions=False` pattern asserts the outcome the route actually returns.

## Implementation

### Target file

`tests/eventbus/test_admin_topics_authorization.py`

### Procedure

1. Open `tests/eventbus/test_admin_topics_authorization.py` and add the class below after `TestValidation` (after line 264).
2. Run the file and confirm all existing tests still pass unchanged.

### Method

```python
class TestPublishOrder:
    def test_failed_principal_build_keeps_previous_generation(
        self, admin_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from eventbus import app as eb_app

        config_before = eb_app.app.state.config
        map_before = principal_map()

        def _boom(config: Any) -> Any:
            raise ValueError("principal build failed")

        monkeypatch.setattr("eventbus.admin_route._build_principal_map", _boom)
        failing = TestClient(admin_client.app, raise_server_exceptions=False)
        resp = failing.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicB"]}},
        )

        assert resp.status_code == 500
        assert eb_app.app.state.config is config_before
        assert principal_map() is map_before

    def test_noop_update_publishes_nothing(self, admin_client: TestClient) -> None:
        from eventbus import app as eb_app

        config_before = eb_app.app.state.config
        map_before = principal_map()

        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicA"]}},
        )

        assert resp.status_code == 200
        assert resp.json()["changed"] is False
        assert eb_app.app.state.config is config_before
        assert principal_map() is map_before

    def test_effective_update_publishes_config_and_map(
        self, admin_client: TestClient
    ) -> None:
        from eventbus import app as eb_app

        config_before = eb_app.app.state.config
        map_before = principal_map()

        resp = admin_client.post(
            "/admin/topics/authorization",
            headers={"Authorization": "Bearer admin-tok"},
            json={"consumer_authorization": {"c1": ["topicB"]}},
        )

        assert resp.status_code == 200
        assert resp.json()["changed"] is True
        assert eb_app.app.state.config is not config_before
        assert principal_map() is not map_before
        assert principal_map()["consumer-tok"].consumer_grants == frozenset(
            {("c1", "topicB")}
        )
```

### Details

- Existing tests in the file are not modified; the new class only appends.
- If `app.state.config` or the principal map is shared across tests by the autouse reset in `tests/eventbus/conftest.py`, the identity checks are still local to one test.

## Compatibility considerations

N/A: test-only addition; no production behavior or existing test changes.

## Security considerations

N/A: fixture tokens only (`admin-tok`, `consumer-tok`); no real credentials.

## Rollback considerations

N/A: revert the commit.

## Validation plan

1. `uv run pytest tests/eventbus/test_admin_topics_authorization.py -v`; temporarily confirm `test_failed_principal_build_keeps_previous_generation` (new) fails against the pre-change `admin_route.py` (config would already be published).
2. `uv run pytest tests/eventbus`.
3. `uv run ruff check tests/eventbus`; `uv run ruff format --check tests/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run python tools/check_mock_patch_targets.py`.
4. `uv run python tools/stale_detector.py implementations/20261029-101422_03_tests_eventbus_test_admin_topics_authorization.py.md`.

## Completion criteria

- `TestPublishOrder` (new) exists with the failing-build, no-op, and effective-update tests, and all pass.
- The failing-build test asserts an unchanged config object and principal map and a non-success response.
- Existing tests pass unchanged; ruff, format, mypy, and the mock-patch check are clean.

## Out of Scope

- Audit assertions (`ebaudit005`), comment identifier cleanup (`eventbus004`), and fixture lifecycle changes (`eventbus003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestPublishOrder` (new) with the three tests (Implementation > Procedure/Method/Details) | Pending | — | — | Needs seq 01 and seq 02 first |
| 2 | Run the new and existing tests (Validation plan) | Pending | — | — | |
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
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261029-090157_eventbus001_admin-authz-publish-order.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-091959_eventbus001_admin-authz-publish-order.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101422
- **Related target files**: `tests/eventbus/test_admin_topics_authorization.py`
