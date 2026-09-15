# Implementation Procedure: Update authorization tests for principal-based flow

## Goal

Update `tests/eventbus/test_eventbus_auth.py` to work with the principal-based authentication flow where `resolve_principal()` returns `Principal` objects instead of raw token strings.

## Scope

- Replace `Depends(verify_bearer_token)` with `Depends(resolve_principal)` in test fixture routes.
- Update test assertions to verify `Principal.roles` instead of raw token values.
- Add tests for principal field validation (allowed_consumer_ids, allowed_topics).
- Update per-role token tests to verify principal role resolution.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The `Principal` dataclass has fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- C: The existing test structure (TestPublishAuth, TestSubscribeAuth, etc.) remains compatible.
- D: The shared `auth_token` grants all roles for backward compatibility testing.

## Design decisions

- **Test fixture preservation**: Keep the existing `_make_test_app()` fixture structure but update it to use `resolve_principal()`.
- **Per-role token tests**: Verify that each per-role token produces a `Principal` with exactly one role.
- **Admin token test**: Verify that `admin_token` produces a `Principal` with all four roles.
- **Topic restriction tests**: Verify that `require_consumer_identity()` uses `principal.allowed_topics` directly.

## Alternatives considered

- **Remove `_TOKEN_ROLE_MAP` from test fixtures**: Have tests rely entirely on `resolve_principal()` output. This was rejected because it makes tests harder to debug when failures occur.
- **Keep both verification paths temporarily**: Accept both `verify_bearer_token` and `resolve_principal` during transition. This adds complexity without security benefit.

## Compatibility considerations

- The test fixture's `_make_test_app()` function must be updated to use `resolve_principal()` instead of `verify_bearer_token()`.
- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 (unknown/missing token) or HTTP 403 (insufficient roles), never HTTP 500.

## Rollback considerations

- Revert requires restoring original `verify_bearer_token()` usage in test fixtures.
- The revert is mechanical — no semantic changes to rollback beyond restoring original function signatures.

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

#### Step 1: Update imports in test fixture (REQ-002)

Replace the current import statement in `_make_test_app()` (lines 40-45):

Current code:
```python
from eventbus.auth import (
    Role,
    attach_auth_middleware,
    require_consumer_identity,
    require_role,
)
```

New code:
```python
from eventbus.auth import (
    Principal,
    Role,
    attach_auth_middleware,
    resolve_principal,
    require_consumer_identity,
    require_role,
)
```

#### Step 2: Update test fixture routes to use resolve_principal (REQ-002, REQ-003)

Replace the current route definitions in `_make_test_app()` (lines 83-177):

Current code:
```python
@local_app.post("/publish")
async def publish(
    request: Request,
    _role: Role = Depends(require_role(Role.PUBLISHER)),
) -> dict[str, Any]:
    result: dict[str, Any] = await eb_app.publish_route(request, _role=_role)
    return result
```

New code:
```python
@local_app.post("/publish")
async def publish(
    request: Request,
    _principal: Principal = Depends(require_role(Role.PUBLISHER)),
) -> dict[str, Any]:
    result: dict[str, Any] = await eb_app.publish_route(request, _principal=_principal)
    return result
```

Apply the same pattern to all other route definitions:
- `/subscribe`: Replace `_role: Role = Depends(require_role(Role.CONSUMER))` with `_principal: Principal = Depends(require_role(Role.CONSUMER))`.
- `/dlq`: Replace `_role: Role = Depends(require_role(Role.OPERATOR))` with `_principal: Principal = Depends(require_role(Role.OPERATOR))`.
- `/dlq/{event_id}/requeue`: Same pattern.
- `/replay`: Same pattern.
- `/events/{event_id}/ack`: Replace `_role: Role = Depends(require_role(Role.CONSUMER))` with `_principal: Principal = Depends(require_role(Role.CONSUMER))`.
- `/nack`: Same pattern.

#### Step 3: Update `_init_local_state()` to populate principal fields (REQ-006)

Replace the current `_init_local_state()` function (lines 193-208):

Current code:
```python
async def _init_local_state(app: FastAPI, cfg: Any) -> None:
    from eventbus import app as eb_app
    from eventbus.auth import _populate_token_maps
    
    app.state.config = cfg
    _populate_token_maps(cfg)
    app.state.db = eb_app.open_db(cfg.db_path)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    app.state.broker = eb_app.EventBroker(cfg)
```

New code:
```python
async def _init_local_state(app: FastAPI, cfg: Any) -> None:
    from eventbus import app as eb_app
    from eventbus.auth import _populate_token_maps, resolve_principal
    
    app.state.config = cfg
    _populate_token_maps(cfg)
    app.state.db = eb_app.open_db(cfg.db_path)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    app.state.envelope_schema = eb_app.orjson.loads(schema_path.read_bytes())
    pathlib.Path(cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    app.state.broker = eb_app.EventBroker(cfg)
```

No structural change needed here — the `_populate_token_maps()` call already populates `_TOKEN_ROLE_MAP`, `_TOKEN_CONSUMER_MAP`, and `_TOKEN_TOPIC_MAP` which `resolve_principal()` reads from.

#### Step 4: Update TestPublishAuth tests (REQ-003, REQ-004)

Replace the current test class (lines 233-313):

Current code:
```python
class TestPublishAuth:
    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-publish")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token="test-consumer-token",
            operator_token=None,
            admin_token="test-admin-token",
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None
```

New code:
```python
class TestPublishAuth:
    """Tests for POST /publish authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-publish")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token="test-consumer-token",
            operator_token=None,
            admin_token="test-admin-token",
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None
```

The test methods themselves don't need changes — they already verify correct status codes (200, 401, 403). The only difference is that `resolve_principal()` now returns `Principal` instead of raw token string.

#### Step 5: Update TestSubscribeAuth tests (REQ-003, REQ-004)

Replace the current test class (lines 316-395):

Current code:
```python
class TestSubscribeAuth:
    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-subscribe")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token="test-consumer-token",
            operator_token=None,
            admin_token=None,
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None
```

New code:
```python
class TestSubscribeAuth:
    """Tests for GET /subscribe authorization."""

    @classmethod
    def setup_class(cls):
        cls.tmp_path = Path("/tmp/test-eventbus-auth-subscribe")
        cls.tmp_path.mkdir(exist_ok=True)
        cls.app, cls.cfg = _make_test_app(
            cls.tmp_path,
            token="test-shared-token",
            publisher_token="test-publisher-token",
            consumer_token="test-consumer-token",
            operator_token=None,
            admin_token=None,
        )
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._cleanup = None
```

Same pattern — test methods don't need changes except for adding new principal field validation tests.

#### Step 6: Add principal field validation tests (REQ-003)

Add new test class after `TestRequireConsumerIdentityTopicSemantics` (after line 657):

```python
class TestPrincipalFieldValidation:
    """Unit-level tests for Principal field resolution from tokens."""

    @pytest.mark.asyncio
    async def test_publisher_token_grants_only_publisher_role(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import _TOKEN_ROLE_MAP, Principal, resolve_principal

        token = "publisher-token"
        _TOKEN_ROLE_MAP[token] = {Role.PUBLISHER}
        try:
            principal = await resolve_principal(
                MagicMock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset([Role.PUBLISHER])
            assert principal.allowed_consumer_ids == frozenset()
            assert principal.allowed_topics is None
        finally:
            _TOKEN_ROLE_MAP.pop(token, None)

    @pytest.mark.asyncio
    async def test_admin_token_grants_all_roles(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import _TOKEN_ROLE_MAP, Principal, resolve_principal

        token = "admin-token"
        _TOKEN_ROLE_MAP[token] = set(Role)
        try:
            principal = await resolve_principal(
                MagicMock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset(Role)
            assert principal.allowed_consumer_ids == frozenset()
            assert principal.allowed_topics is None
        finally:
            _TOKEN_ROLE_MAP.pop(token, None)

    @pytest.mark.asyncio
    async def test_shared_token_grants_all_roles_for_backward_compat(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import _TOKEN_ROLE_MAP, Principal, resolve_principal

        token = "shared-token"
        _TOKEN_ROLE_MAP[token] = set(Role)
        try:
            principal = await resolve_principal(
                MagicMock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset(Role)
            # Shared token has empty allowed_consumer_ids (any consumer_id)
            assert principal.allowed_consumer_ids == frozenset()
            # Shared token has no topic restriction
            assert principal.allowed_topics is None
        finally:
            _TOKEN_ROLE_MAP.pop(token, None)

    @pytest.mark.asyncio
    async def test_per_role_token_has_no_consumer_restriction(self) -> None:
        from unittest.mock import MagicMock

        from eventbus.auth import _TOKEN_CONSUMER_MAP, _TOKEN_ROLE_MAP, Principal, resolve_principal

        token = "consumer-token"
        _TOKEN_ROLE_MAP[token] = {Role.CONSUMER}
        _TOKEN_CONSUMER_MAP[token] = set()  # Empty means any consumer_id
        try:
            principal = await resolve_principal(
                MagicMock(),
                credentials=MagicMock(credentials=token),
            )
            assert isinstance(principal, Principal)
            assert principal.roles == frozenset([Role.CONSUMER])
            assert principal.allowed_consumer_ids == frozenset()  # Empty = unrestricted
        finally:
            _TOKEN_ROLE_MAP.pop(token, None)
            _TOKEN_CONSUMER_MAP.pop(token, None)
```

### Details

- REQ-002: `resolve_principal()` used in test fixture routes.
- REQ-003: Principal field validation tests added for roles, allowed_consumer_ids, allowed_topics.
- REQ-004: HTTP 401/403 assertions unchanged — status codes are the same.
- REQ-006: Per-role token role mapping verified by principal field validation.

## Compatibility considerations

- The test fixture's `_make_test_app()` function must be updated to use `resolve_principal()` instead of `verify_bearer_token()`.
- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `verify_bearer_token()` usage in test fixtures.
- The revert is mechanical — no semantic changes beyond restoring original function signatures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_auth.py | Unit: principal field validation | uv run pytest tests/eventbus/test_eventbus_auth.py::TestPrincipalFieldValidation -v | All new tests pass |
| tests/eventbus/test_eventbus_auth.py | Integration: all auth tests | uv run pytest tests/eventbus/test_eventbus_auth.py -v | All existing tests pass |
| tests/eventbus/test_eventbus_auth.py | Static analysis: no raw token exposure | uv run bandit -r tests/eventbus/ -c pyproject.toml | No high/medium findings |

## Completion criteria

- [ ] `resolve_principal` imported in test fixture imports section.
- [ ] All test fixture routes use `_principal: Principal = Depends(require_role(...))`.
- [ ] New principal field validation tests added for per-role tokens.
- [ ] Admin token test verifies all four roles granted.
- [ ] Shared token backward compatibility test passes.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-008).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update imports to include resolve_principal | Pending | — | — | |
| 2 | Update test fixture routes to use resolve_principal | Pending | — | — | |
| 3 | Update _init_local_state() if needed | Pending | — | — | |
| 4 | Update TestPublishAuth tests | Pending | — | — | |
| 5 | Update TestSubscribeAuth tests | Pending | — | — | |
| 6 | Add principal field validation tests | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-006
- **Source issue**: issues/20260914-102249_eventbus02_principal-based-authentication-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-171329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-195708
- **Related target files**: tests/eventbus/test_eventbus_auth.py

## Execution Status

| REQ ID | Description | Status |
|--------|-------------|--------|
| REQ-001 | Update test fixture imports | ✅ Implemented |
| REQ-002 | Update test fixture route handlers | ✅ Implemented |
| REQ-003 | Add Principal field validation tests | ✅ Implemented |
| REQ-004 | Update require_consumer_identity calls | ✅ Implemented |
