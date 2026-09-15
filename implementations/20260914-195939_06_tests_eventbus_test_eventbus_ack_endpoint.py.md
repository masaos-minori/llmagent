# Implementation Procedure: Update ack endpoint tests for principal-based flow

## Goal

Update `tests/eventbus/test_eventbus_ack_endpoint.py` to work with the principal-based authentication flow where `resolve_principal()` returns `Principal` objects instead of raw token strings.

## Scope

- Replace `verify_bearer_token` usage with `resolve_principal` in test fixture routes.
- Update test assertions to verify `Principal.roles` instead of raw token values.
- Ensure ack endpoint behavior remains correct after principal model change.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The `Principal` dataclass has fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- C: The existing test structure (TestAckEndpoint, TestAckMonotonicOffset) remains compatible.
- D: The ack endpoint's HTTP response format remains unchanged.

## Design decisions

- **Test fixture preservation**: Keep the existing fixture structure but update it to use `resolve_principal()`.
- **HTTP-level testing focus**: This test file focuses on HTTP-level ack behavior — status codes, response bodies, offset updates.
- **No behavioral change**: The ack endpoint's behavior should not change — only the authentication mechanism changes.

## Alternatives considered

- **Remove `verify_bearer_token` from test fixtures**: Have tests rely entirely on `resolve_principal()` output. This was rejected because it makes tests harder to debug when failures occur.
- **Keep both verification paths temporarily**: Accept both `verify_bearer_token` and `resolve_principal` during transition. This adds complexity without security benefit.

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

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_endpoint.py`

### Procedure

#### Step 1: Update imports in test fixture (REQ-002)

Replace the current import statement in the fixture function (lines 17-39):

Current code:
```python
@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig
    
    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        auth_token="test-token",
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)
    
    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
        yield c
```

New code:
```python
@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.auth import resolve_principal
    from eventbus.config import EventBusConfig
    
    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        auth_token="test-token",
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)
    
    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
        yield c
```

The key change is adding `from eventbus.auth import resolve_principal` to ensure the principal model is available for the test fixture.

#### Step 2: Verify ack endpoint behavior remains correct (REQ-003)

All existing test methods in `TestAckEndpoint` and `TestAckMonotonicOffset` classes remain valid — they test HTTP-level ack behavior which is independent of the authentication mechanism. No changes needed to test methods.

#### Step 3: Add principal field validation test (REQ-003)

Add a new test method to verify that the ack endpoint correctly validates principal fields:

```python
class TestAckPrincipalValidation:
    """Tests for Principal field validation in ack endpoint."""

    @pytest.mark.asyncio
    async def test_ack_with_insufficient_roles_returns_403(self) -> None:
        """A publisher cannot ACK events (requires CONSUMER role)."""
        from unittest.mock import MagicMock
        
        from eventbus.auth import _TOKEN_ROLE_MAP, Principal, require_role
        
        # Simulate a publisher token being used for ack
        token = "publisher-token"
        _TOKEN_ROLE_MAP[token] = {Role.PUBLISHER}
        try:
            # The ack endpoint requires CONSUMER role
            dep = require_role(Role.CONSUMER)
            
            # Create a mock request with publisher token
            mock_request = MagicMock()
            mock_request.url.path = "/events/test-event-id/ack"
            
            # Try to get the dependency — should fail with 403
            with pytest.raises(HTTPException) as exc_info:
                await dep(mock_request, token=MagicMock(credentials=token))
            assert exc_info.value.status_code == 403
        finally:
            _TOKEN_ROLE_MAP.pop(token, None)
```

### Details

- REQ-002: `resolve_principal` imported in test fixture.
- REQ-003: Principal field validation test added for insufficient roles.

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
| tests/eventbus/test_eventbus_ack_endpoint.py | Integration: all ack tests pass | uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py -v | All existing tests pass |
| tests/eventbus/test_eventbus_ack_endpoint.py | Unit: principal validation | uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py::TestAckPrincipalValidation -v | New test passes |
| tests/eventbus/test_eventbus_ack_endpoint.py | Static analysis: no raw token exposure | uv run bandit -r tests/eventbus/ -c pyproject.toml | No high/medium findings |

## Completion criteria

- [ ] `resolve_principal` imported in test fixture imports section.
- [ ] All existing ack tests pass without modification.
- [ ] New principal field validation test added for insufficient roles.
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
| 2 | Verify ack endpoint behavior remains correct | Pending | — | — | No changes needed |
| 3 | Add principal field validation test | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260914-102249_eventbus02_principal-based-authentication-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-171329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-195939
- **Related target files**: tests/eventbus/test_eventbus_ack_endpoint.py

## Execution Status

| REQ ID | Description | Status |
|--------|-------------|--------|
| REQ-001 | Update client fixture to populate token maps | ✅ Implemented |
