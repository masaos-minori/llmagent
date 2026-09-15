## Goal

Update example configuration if admin_token is retained or new fields are added.

## Scope

- `config/eventbus.toml`: Update example configuration to include all per-role token fields; add comments documenting valid token combinations.

## Assumptions

- A: The plan's decision to add ADMIN role means `admin_token` should be retained in the config schema.
- B: The plan's decision to allow publisher-only and monitoring-only deployments means these token fields must be documented as optional.
- C: The current example only shows `consumer_token`, `operator_token`, and `admin_token` — `publisher_token` and `monitoring_token` are missing.

## Design decisions

- **Keep admin_token**: Since ADMIN role is being added, `admin_token` remains in the config schema.
- **Add missing per-role tokens**: Include `publisher_token` and `monitoring_token` in the example to match the full set of per-role tokens defined in `_PER_ROLE_TOKEN_FIELDS`.
- **Document token combinations**: Add comments explaining which token combinations are valid.

## Alternatives considered

- Removing `admin_token` from the example: rejected because the plan's decision adds ADMIN role, which requires `admin_token`.

## Implementation

### Target file

`config/eventbus.toml`

### Procedure

1. Add `publisher_token` and `monitoring_token` fields to the per-role token section.
2. Add comments documenting valid token combinations.
3. Retain `admin_token` field (ADMIN role is being added).

### Method

**Step 1: Update per-role token section**

Replace the existing per-role token section (lines 10-14):
```toml
# REQ-004: Per-role tokens for authorization
# If not set, the system falls back to the shared token mechanism
consumer_token = ""
operator_token = ""
admin_token = ""
```

With:
```toml
# REQ-004: Per-role tokens for authorization
# At least one of: auth_token OR any per-role token must be configured.
# Valid combinations:
#   - auth_token alone (shared token mode, grants all roles)
#   - auth_token + one or more per-role tokens (role-based mode)
#   - publisher_token + auth_token (publisher-only deployment)
#   - monitoring_token + auth_token (monitoring-only deployment)
#   - Any combination of per-role tokens + auth_token
publisher_token = ""
consumer_token = ""
operator_token = ""
monitoring_token = ""
admin_token = ""
```

**Step 2: Verify all per-role tokens are present**

The following per-role tokens must exist in the config:
- `publisher_token` — NEW (was missing)
- `consumer_token` — already exists
- `operator_token` — already exists
- `monitoring_token` — NEW (was missing)
- `admin_token` — already exists

## Compatibility considerations

- **Breaking change**: Adding `publisher_token` and `monitoring_token` to the example may cause confusion if users expect these to be required. They remain optional — the validation rule allows configurations without them.
- **admin_token retention**: Keeping `admin_token` aligns with the plan's decision to add ADMIN role.

## Security considerations

- **Fail-closed on invalid security settings**: The comment documentation helps operators understand that at least one authentication token must be configured.

## Rollback considerations

- **Reverting token additions**: Remove `publisher_token` and `monitoring_token` from the example if they are not needed.

## Validation plan

- Manual review: verify all per-role tokens are present in the example.
- Run config loading tests against the updated example to ensure it parses correctly.

## Completion criteria

- All five per-role tokens (`publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`, `admin_token`) are present in the example.
- Comments document valid token combinations.
- The example configuration loads successfully via `load_config()`.

## Out of scope

- Modifying `scripts/eventbus/config.py` (handled by its own procedure document).
- Modifying `scripts/eventbus/auth.py` (handled by its own procedure document).
- Adding tests for token combinations (handled by its own procedure document).

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
- **Requirement ID**: REQ-005, REQ-007
- **Source issue**: issues/20260914-102535_eventbus09_config-validation-role-token-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-175822_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-235154
- **Related target files**: config/eventbus.toml
