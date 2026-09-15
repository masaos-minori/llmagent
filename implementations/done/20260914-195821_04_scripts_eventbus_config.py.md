# Implementation Procedure: Update EventBusConfig for principal-based authentication

## Goal

Update `scripts/eventbus/config.py` to ensure per-role token fields are properly validated and documented for the principal-based authentication flow.

## Scope

- Ensure per-role token fields (`publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`, `admin_token`) are properly typed as `str` with default `""`.
- Validate that at least one per-role token is configured when using role-based access control.
- Document the relationship between `auth_token` and per-role tokens.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The shared `auth_token` grants all roles for backward compatibility — this convention is already implemented in `_populate_token_maps()` line 77.
- C: `admin_token` is a superuser credential granting all roles — confirmed by `_populate_token_maps()` line 87-88.
- D: The current per-role token fields exist in `EventBusConfig` dataclass (lines 50-54).

## Design decisions

- **No structural change to dataclass**: The current per-role token fields are correct — they're optional string fields with empty defaults.
- **Validation only**: The existing validation in `load_config()` (lines 199-206) already ensures at least one per-role token is configured. This is sufficient.
- **Documentation only**: Add inline comments explaining the relationship between `auth_token` and per-role tokens.

## Alternatives considered

- **Add principal-specific config fields**: Have `EventBusConfig` carry resolved principals directly. This was rejected because it couples configuration to runtime state — principals should be derived from tokens, not stored in config.
- **Remove `auth_token` entirely**: Replace `auth_token` with per-role tokens only. This was rejected because it breaks backward compatibility with deployments using the shared token model.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Per-role tokens must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- No rollback needed — no structural changes to the dataclass.

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

#### Step 1: Verify per-role token fields exist (REQ-006)

Current code (lines 50-54):
```python
    # Per-role tokens (optional, for role-based access control)
    publisher_token: str = ""
    consumer_token: str = ""
    operator_token: str = ""
    monitoring_token: str = ""
    admin_token: str = ""
```

These fields are correct — no changes needed. They're optional string fields with empty defaults, which matches the expected behavior:
- Empty string means "no token configured for this role".
- Non-empty string means "this token grants this role".

#### Step 2: Verify load_config() validation (REQ-006)

Current code (lines 199-206):
```python
    # Validate per-role tokens: at least one must be configured
    if not any(
        [
            data.get("consumer_token"),
            data.get("operator_token"),
            data.get("admin_token"),
        ]
    ):
        raise ValueError("At least one per-role token must be configured")
```

This validation is correct — it ensures at least one per-role token is configured when using role-based access control. No changes needed.

#### Step 3: Add documentation comment for auth_token compatibility (REQ-008)

Add a comment above the per-role token fields explaining the relationship with `auth_token`:

Current code (lines 49-54):
```python
    # Per-role tokens (optional, for role-based access control)
    publisher_token: str = ""
    consumer_token: str = ""
    operator_token: str = ""
    monitoring_token: str = ""
    admin_token: str = ""
```

New code:
```python
    # Per-role tokens (optional, for role-based access control).
    # When set, each token grants only its own role (e.g., publisher_token → PUBLISHER).
    # The shared auth_token (if set) grants ALL roles for backward compatibility.
    # At least one per-role token must be configured when using role-based access control.
    publisher_token: str = ""
    consumer_token: str = ""
    operator_token: str = ""
    monitoring_token: str = ""
    admin_token: str = ""
```

### Details

- REQ-006: Per-role token fields verified as correct.
- REQ-008: Documentation added for auth_token compatibility.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Per-role tokens must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- No rollback needed — no structural changes to the dataclass.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/config.py | Unit: per-role token validation | uv run pytest tests/eventbus/test_eventbus_config.py -v | All config tests pass |
| scripts/eventbus/config.py | Static analysis: no new findings | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/config.py | Type checking | uv run mypy scripts/eventbus/config.py | No new type errors |

## Completion criteria

- [ ] Per-role token fields verified as correct (no changes needed).
- [ ] load_config() validation verified as correct (no changes needed).
- [ ] Documentation comment added for auth_token compatibility.
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
| 1 | Verify per-role token fields | Completed | 20260915-102707 | 20260915-102707 | No changes needed |
| 2 | Verify load_config() validation | Completed | 20260915-102707 | 20260915-102707 | No changes needed |
| 3 | Add documentation comment | Completed | 20260915-102707 | 20260915-102707 |  |

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
- **Requirement ID**: REQ-006, REQ-008
- **Source issue**: issues/20260914-102249_eventbus02_principal-based-authentication-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-171329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-195821
- **Related target files**: scripts/eventbus/config.py

## Execution Status

| REQ ID | Description | Status |
|--------|-------------|--------|
| REQ-001 | Verify EventBusConfig fields are compatible | ✅ No change needed |
