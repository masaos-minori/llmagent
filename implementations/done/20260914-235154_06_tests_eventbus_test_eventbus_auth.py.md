## Goal

Add tests for unified 401 response format; verify every public endpoint returns consistent auth failures.

## Scope

- `tests/eventbus/test_eventbus_auth.py`: Add tests for unified 401 response format across all endpoints (T-8); add test for no-double-authentication processing (T-9).

## Assumptions

- A: The plan's decision to centralize 401 responses means all authentication failures should return the same JSON schema: `{"error": "Unauthorized", "detail": "<reason>", "WWW-Authenticate": "Bearer realm=\"eventbus\""}`.
- B: The existing test infrastructure uses `_make_test_app()` fixture to create FastAPI apps with auth middleware registered.
- C: The existing tests already check for 401 status codes but do not verify the response body format.

## Design decisions

- **Reuse existing test infrastructure**: Use `_make_test_app()` fixture to create test apps; use `TestClient` to make requests.
- **Test response body format**: In addition to checking status code, verify the response body matches the expected JSON schema.
- **Test WWW-Authenticate header**: Verify the header is present and has the correct value.
- **Separate middleware-level from handler-level tests**: Middleware-level rejections happen before route handlers; handler-level rejections happen after token verification.

## Alternatives considered

- Using `pytest.fixture` for common test setup: rejected because the existing tests use inline `setup_class`/`teardown_class`, and adding fixtures would change the test style unnecessarily.
- Testing via integration tests only: rejected because unit-level tests provide more direct control over which authentication path is exercised.

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

1. Add test for unified 401 response format: missing Authorization header (T-8).
2. Add test for unified 401 response format: invalid Bearer token (T-8).
3. Add test for no-double-authentication processing (T-9).
4. Verify all existing tests still pass.

### Method

**Step 1: Add T-8 — Unified 401 response format: missing Authorization header**

```python
class TestUnified401ResponseFormat:
    """Tests for the unified HTTP 401 response format."""

    def test_missing_authorization_header_returns_unified_format(self) -> None:
        """REQ-009, REQ-010: Missing Authorization header returns standardized 401 response."""
        app, cfg = _make_test_app(
            Path("/tmp/test-unified-401"),
            token="test-shared-token",
            publisher_token=None,
            consumer_token=None,
            operator_token=None,
            admin_token=None,
        )
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/health")
        assert response.status_code == 401
        
        body = response.json()
        assert body["error"] == "Unauthorized"
        assert "detail" in body
        assert isinstance(body["detail"], str)
        assert len(body["detail"]) > 0
        
        # WWW-Authenticate header must be present
        assert "www-authenticate" in response.headers
        assert 'Bearer realm="eventbus"' in response.headers["www-authenticate"]
```

**Step 2: Add T-8 — Unified 401 response format: invalid Bearer token**

```python
    def test_invalid_bearer_token_returns_unified_format(self) -> None:
        """REQ-009, REQ-010: Invalid Bearer token returns standardized 401 response."""
        app, cfg = _make_test_app(
            Path("/tmp/test-unified-401-invalid"),
            token="test-shared-token",
            publisher_token=None,
            consumer_token=None,
            operator_token=None,
            admin_token=None,
        )
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get(
            "/health",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        
        body = response.json()
        assert body["error"] == "Unauthorized"
        assert "detail" in body
        assert isinstance(body["detail"], str)
        assert len(body["detail"]) > 0
        
        # WWW-Authenticate header must be present
        assert "www-authenticate" in response.headers
        assert 'Bearer realm="eventbus"' in response.headers["www-authenticate"]
```

**Step 3: Add T-9 — No double-authentication processing**

```python
    def test_no_double_authentication_processing(self) -> None:
        """REQ-008: Authentication failures are not processed twice."""
        app, cfg = _make_test_app(
            Path("/tmp/test-no-double-auth"),
            token="test-shared-token",
            publisher_token=None,
            consumer_token=None,
            operator_token=None,
            admin_token=None,
        )
        client = TestClient(app, raise_server_exceptions=False)
        
        # Make a request without authentication
        response = client.get("/health")
        assert response.status_code == 401
        
        # The response should come from ONE source only (middleware or handler),
        # not both. If it were processed twice, we might see duplicate error fields
        # or inconsistent behavior.
        body = response.json()
        assert body["error"] == "Unauthorized"
        # Only one "error" field — no duplication
        assert list(body.keys()) == ["error", "detail"]
```

**Step 4: Verify all existing tests still pass**

Run the full test suite:
```bash
uv run pytest tests/eventbus/test_eventbus_auth.py -v
```

All existing tests must pass without modification.

## Compatibility considerations

- **Breaking change**: All 401 responses now include a `"detail"` field and `WWW-Authenticate` header. Clients expecting only `{"error": "Unauthorized"}` will need to be updated.
- **Existing test compatibility**: Existing tests that check for 401 status code will continue to work, but they do not verify the response body format. The new tests fill this gap.

## Security considerations

- **Fail-closed on invalid security settings**: All authentication failures return consistent 401 responses with no information leakage about which specific token or endpoint failed.
- **WWW-Authenticate header**: Added for RFC compliance, enabling clients to understand the expected authentication scheme.

## Rollback considerations

- **Reverting centralized 401 response**: Restore individual `HTTPException(status_code=401, detail="Unauthorized")` calls at each failure point.

## Validation plan

- Run all new tests: `uv run pytest tests/eventbus/test_eventbus_auth.py -v -k "unified_401 or no_double"`
- Run full test suite: `uv run pytest tests/eventbus/test_eventbus_auth.py -v`
- Lint/format: `uv run ruff check tests/eventbus/test_eventbus_auth.py --fix && uv run ruff check tests/eventbus/test_eventbus_auth.py`
- Type checking: `uv run mypy tests/eventbus/test_eventbus_auth.py`

## Completion criteria

- All new tests (T-8, T-9) exist and pass.
- All existing tests still pass without modification.
- Every public endpoint returns consistent 401 response format.
- WWW-Authenticate header is present on all 401 responses.

## Out of scope

- Modifying `scripts/eventbus/config.py` (handled by its own procedure document).
- Modifying `scripts/eventbus/auth.py` (handled by its own procedure document).
- Adding tests for cross-field validation errors (handled by its own procedure document).
- Updating `config/eventbus.toml` example configuration (handled by its own procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-162407 | 20260915-162407 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-162407 | 20260915-162407 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-162407 | 20260915-162407 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-162407 | 20260915-162407 |  |

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
- **Requirement ID**: REQ-009, REQ-010, REQ-011
- **Source issue**: issues/20260914-102535_eventbus09_config-validation-role-token-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-175822_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-235154
- **Related target files**: tests/eventbus/test_eventbus_auth.py