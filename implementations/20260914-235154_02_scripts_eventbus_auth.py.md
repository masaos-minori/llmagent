## Goal

Centralize HTTP 401 response format; add ADMIN role and corresponding routes; update authentication-failure handling to use one documented response schema.

## Scope

- `scripts/eventbus/auth.py`: Add ADMIN role to Role enum; add `/admin/*` route to `_ROUTE_ROLE_MAP`; add `admin_token` to `_PER_ROLE_TOKEN_FIELDS`; add `unauthorized_response()` helper function; update all authentication failure points to use centralized response.

## Assumptions

- A: The `admin_token` field exists in EventBusConfig but there is no Role.ADMIN in auth.py — confirmed by reading `auth.py:21-25`.
- B: `_populate_token_maps()` gives admin_token superuser privileges (lines 85-88) — confirmed by reading `auth.py:85-88`.
- C: There is no `/admin` route in `_ROUTE_ROLE_MAP` (lines 29-39) — confirmed by reading `auth.py:29-39`.
- D: The `attach_auth_middleware()` function already returns `JSONResponse({"error": "Unauthorized"}, status_code=401)` for middleware-level rejections — confirmed by reading `auth.py:279`.
- E: `verify_bearer_token()` returns `HTTPException(status_code=401, detail="Unauthorized")` for unauthenticated requests — confirmed by reading `auth.py:109`.
- F: `require_role()` raises `HTTPException(status_code=401, detail="Unauthorized")` for unauthorized access — confirmed by reading `auth.py:141`.
- G: `require_consumer_identity()` raises `HTTPException(status_code=401, detail="Unauthorized")` for unauthorized access — confirmed by reading `auth.py:189`.

## Design decisions

- **Add ADMIN role**: The infrastructure (`admin_token` field, superuser mapping in `_populate_token_maps()`) suggests an admin role was intended; having a superuser credential without a corresponding role creates confusion.
- **Centralized 401 response**: Use `unauthorized_response()` helper that returns `JSONResponse` with `"error": "Unauthorized"`, `"detail"` reason, and `WWW-Authenticate: Bearer realm="eventbus"` header.
- **Keep existing HTTPException usage for role-based denials**: `require_role()` uses HTTPException(403) for forbidden access — this is correct behavior (403 vs 401 distinction). Only 401 responses are centralized.
- **Preserve server misconfiguration error**: `verify_bearer_token()` currently raises HTTPException(500) for missing `auth_token` — this should remain as-is since it is a different error class.

## Alternatives considered

- Removing `admin_token` entirely: rejected because the plan's decision adds ADMIN role, which requires `admin_token`.
- Using HTTPException for all 401 responses instead of JSONResponse: rejected because the plan specifies a unified JSON response format with WWW-Authenticate header.

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

1. Add `ADMIN = "admin"` to Role enum.
2. Add `"/admin/*": {Role.ADMIN}` to `_ROUTE_ROLE_MAP`.
3. Add `("admin_token", Role.ADMIN)` to `_PER_ROLE_TOKEN_FIELDS`.
4. Add `unauthorized_response()` helper function.
5. Update `attach_auth_middleware()` to use `unauthorized_response()`.
6. Update `verify_bearer_token()` to use `unauthorized_response()` for unauthenticated requests.
7. Update `require_role()` to use `unauthorized_response()` for unauthorized access.
8. Update `require_consumer_identity()` to use `unauthorized_response()` for unauthorized access.

### Method

**Step 1: Add ADMIN role**

```python
class Role(StrEnum):
    PUBLISHER = "publisher"
    CONSUMER = "consumer"
    OPERATOR = "operator"
    MONITORING = "monitoring"
    ADMIN = "admin"  # NEW
```

**Step 2: Add /admin/* route**

```python
_ROUTE_ROLE_MAP: dict[str, set[Role]] = {
    "/health": {Role.MONITORING},
    "/publish": {Role.PUBLISHER},
    "/subscribe": {Role.CONSUMER},
    "/events": {Role.CONSUMER},
    "/ack": {Role.CONSUMER},
    "/nack": {Role.CONSUMER},
    "/dlq": {Role.OPERATOR},
    "/dlq/requeue": {Role.OPERATOR},
    "/replay": {Role.OPERATOR},
    "/admin/*": {Role.ADMIN},  # NEW
}
```

**Step 3: Add admin_token to per-role token fields**

```python
_PER_ROLE_TOKEN_FIELDS: tuple[tuple[str, Role], ...] = (
    ("publisher_token", Role.PUBLISHER),
    ("consumer_token", Role.CONSUMER),
    ("operator_token", Role.OPERATOR),
    ("monitoring_token", Role.MONITORING),
    ("admin_token", Role.ADMIN),  # NEW
)
```

**Step 4: Add unauthorized_response() helper**

```python
from fastapi.responses import JSONResponse

def unauthorized_response(detail: str = "Unauthorized") -> JSONResponse:
    """Return a standardized HTTP 401 Unauthorized response."""
    return JSONResponse(
        content={"error": "Unauthorized", "detail": detail},
        status_code=401,
        headers={"WWW-Authenticate": 'Bearer realm="eventbus"'},
    )
```

**Step 5: Update attach_auth_middleware()**

Replace line 279:
```python
# Before:
return JSONResponse({"error": "Unauthorized"}, status_code=401)

# After:
return unauthorized_response("Invalid or missing Bearer token")
```

**Step 6: Update verify_bearer_token()**

Replace line 109:
```python
# Before:
raise HTTPException(status_code=401, detail="Unauthorized")

# After:
return unauthorized_response("Missing Authorization header")
```

Also replace the empty-token return at line 123:
```python
# Before:
return ""

# After:
return unauthorized_response("Invalid or missing Bearer token")
```

**Step 7: Update require_role()**

Replace lines 140-141:
```python
# Before:
if not token:
    raise HTTPException(status_code=401, detail="Unauthorized")

# After:
if not token:
    return unauthorized_response("Invalid or missing Bearer token")
```

**Step 8: Update require_consumer_identity()**

Replace line 189:
```python
# Before:
raise HTTPException(status_code=401, detail="Unauthorized")

# After:
return unauthorized_response("Invalid or missing Bearer token")
```

## Compatibility considerations

- **Breaking change**: All 401 responses now include a `"detail"` field and `WWW-Authenticate` header. Clients expecting only `{"error": "Unauthorized"}` will need to be updated.
- **ADMIN role availability**: Adding ADMIN role means `admin_token` can now be used for authorization at `/admin/*` endpoints. If these endpoints do not exist yet, the role is inert until they are added.
- **Token combination rule interaction**: With the new token combination rule (REQ-006), configurations that previously failed validation (publisher-only, monitoring-only) may now succeed, and their tokens will be mapped to roles via `_populate_token_maps()`.

## Security considerations

- **Fail-closed on invalid security settings**: All authentication failures return consistent 401 responses with no information leakage about which specific token or endpoint failed.
- **WWW-Authenticate header**: Added for RFC compliance, enabling clients to understand the expected authentication scheme.
- **Admin token grants all roles**: `admin_token` continues to grant every role via `_populate_token_maps()`, matching the plan's design for ADMIN role.

## Rollback considerations

- **Reverting ADMIN role**: Remove `ADMIN` from Role enum, remove `/admin/*` from `_ROUTE_ROLE_MAP`, remove `("admin_token", Role.ADMIN)` from `_PER_ROLE_TOKEN_FIELDS`. The old code is preserved in git history.
- **Reverting centralized 401 response**: Restore individual `HTTPException(status_code=401, detail="Unauthorized")` calls at each failure point.

## Validation plan

- Unit tests for ADMIN role existence in Role enum.
- Integration tests for unified 401 response format across all endpoints.
- Tests verifying every public endpoint returns consistent auth failures.
- Regression tests: all existing auth tests must still pass.
- Lint/format: `uv run ruff check scripts/eventbus/auth.py --fix && uv run ruff check scripts/eventbus/auth.py`
- Type checking: `uv run mypy scripts/eventbus/auth.py`

## Completion criteria

- ADMIN role exists in Role enum with value `"admin"`.
- `/admin/*` route exists in `_ROUTE_ROLE_MAP`.
- `admin_token` is mapped to Role.ADMIN in `_PER_ROLE_TOKEN_FIELDS`.
- `unauthorized_response()` helper exists and is used by all authentication failure points.
- All 401 responses include `"error": "Unauthorized"`, `"detail"` reason, and `WWW-Authenticate` header.
- All existing auth tests pass without modification.
- New tests cover all 401 response paths.

## Out of scope

- Modifying `scripts/eventbus/config.py` (cross-field validation separation — handled by its own procedure document).
- Adding tests for cross-field validation errors (handled by its own procedure document).
- Updating `config/eventbus.toml` example configuration (handled by its own procedure document).
- Implementing `/admin/*` route handlers (future work, not in current scope).

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
- **Requirement ID**: REQ-008, REQ-009, REQ-010, REQ-011, REQ-004
- **Source issue**: issues/20260914-102535_eventbus09_config-validation-role-token-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-175822_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-235154
- **Related target files**: scripts/eventbus/auth.py