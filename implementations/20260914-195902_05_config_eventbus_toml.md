# Implementation Procedure: Update EventBus configuration for principal-based authentication

## Goal

Update `config/eventbus.toml` to document the relationship between `auth_token` and per-role tokens for the principal-based authentication flow.

## Scope

- Document the relationship between `auth_token` and per-role tokens.
- Ensure per-role token fields are properly documented.
- Provide migration guidance from shared-token model to per-role token model.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The shared `auth_token` grants all roles for backward compatibility — this convention is already implemented in `_populate_token_maps()` line 77.
- C: `admin_token` is a superuser credential granting all roles — confirmed by `_populate_token_maps()` line 87-88.
- D: The current per-role token fields exist in `EventBusConfig` dataclass (lines 50-54).

## Design decisions

- **No structural change to TOML**: The current per-role token fields are correct — they're optional string fields with empty defaults.
- **Documentation only**: Add inline comments explaining the relationship between `auth_token` and per-role tokens.
- **Migration guidance**: Provide clear instructions for migrating from shared-token model to per-role token model.

## Alternatives considered

- **Remove `auth_token` entirely**: Replace `auth_token` with per-role tokens only. This was rejected because it breaks backward compatibility with deployments using the shared token model.
- **Add principal-specific config fields**: Have `config/eventbus.toml` carry resolved principals directly. This was rejected because it couples configuration to runtime state — principals should be derived from tokens, not stored in config.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Per-role tokens must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- No rollback needed — no structural changes to the TOML file.

## Implementation

### Target file

`config/eventbus.toml`

### Procedure

#### Step 1: Add documentation for auth_token compatibility (REQ-008)

Current code:
```toml
# eventbus configuration

port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3

# REQ-004: Per-role tokens for authorization
# If not set, the system falls back to the shared token mechanism
consumer_token = ""
operator_token = ""
admin_token = ""
```

New code:
```toml
# eventbus configuration

port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3

# Shared token (optional, for backward compatibility).
# When set, this token grants ALL roles (publisher, consumer, operator, monitoring).
# It is equivalent to setting all per-role tokens to the same value.
# If not set, the system requires per-role tokens below.
auth_token = ""

# Per-role tokens (optional, for role-based access control).
# Each token grants only its own role:
#   - publisher_token → PUBLISHER role (can publish events)
#   - consumer_token → CONSUMER role (can subscribe, ack, nack)
#   - operator_token → OPERATOR role (can manage DLQ, replay)
#   - monitoring_token → MONITORING role (can access /health)
#   - admin_token → ALL roles (superuser credential)
# At least one per-role token must be configured when using role-based access control.
# If auth_token is set, per-role tokens can be left empty for backward compatibility.
publisher_token = ""
consumer_token = ""
operator_token = ""
monitoring_token = ""
admin_token = ""
```

### Details

- REQ-008: Documentation added for auth_token compatibility.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Per-role tokens must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- No rollback needed — no structural changes to the TOML file.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| config/eventbus.toml | Manual review: documentation completeness | Human review | Documentation is clear and complete |
| config/eventbus.toml | Unit: per-role token validation | uv run pytest tests/eventbus/test_eventbus_config.py -v | All config tests pass |

## Completion criteria

- [ ] Documentation comment added for auth_token compatibility.
- [ ] Per-role token fields documented with their respective roles.
- [ ] Migration guidance provided for shared-token to per-role transition.
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
| 1 | Add documentation for auth_token compatibility | Completed | 20260915-102707 | 20260915-102707 |  |
| 2 | Document per-role token fields | Completed | 20260915-102707 | 20260915-102707 |  |
| 3 | Provide migration guidance | Completed | 20260915-102707 | 20260915-102707 |  |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260914-102249_eventbus02_principal-based-authentication-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-171329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-195902
- **Related target files**: config/eventbus.toml

## Execution Status

| REQ ID | Description | Status |
|--------|-------------|--------|
| REQ-001 | Verify TOML config is compatible | ✅ No change needed |
