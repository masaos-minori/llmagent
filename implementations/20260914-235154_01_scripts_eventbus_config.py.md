## Goal

Separate cross-field validation from per-key type validation in EventBus configuration; define administrator role semantics; normalize required-token logic based on enabled capabilities.

## Scope

- `scripts/eventbus/config.py`: Separate validation into three phases (key presence, per-key type/value, cross-field policy); add `_validate_cross_field()`, `_validate_token_combinations()`, `_validate_deployment_mode()` functions; update `load_config()` to call Phase 3 after Phase 2; keep `admin_token` field since ADMIN role is being added.

## Assumptions

- A: Cross-field validation in `load_config()` at lines 198-206 is mixed with per-key type validation — confirmed by reading `config.py:198-206`.
- B: The `admin_token` field exists in EventBusConfig (line 54) — confirmed by reading `config.py:54`.
- C: `__post_init__()` contains cross-field validation for threshold relationships (lines 73-80) — confirmed by reading `config.py:73-80`.
- D: The plan's decision to add ADMIN role means `admin_token` should be retained, not removed.

## Design decisions

- **Three-phase validation**: Split validation into distinct phases (key presence → per-key type/value → cross-field policy) for clearer control flow and testability.
- **Keep admin_token**: Since the plan decides to add ADMIN role, `admin_token` remains in the config schema and is populated in `_populate_token_maps()`.
- **Token combination rule change**: Instead of requiring "at least one per-role token", require either `auth_token` OR at least one per-role token, allowing publisher-only and monitoring-only deployments.
- **Threshold validation stays in `__post_init__`**: Single-value threshold constraints (`slow_consumer_threshold < subscriber_queue_maxsize`, etc.) remain in `__post_init__` as they are single-value checks, not cross-field policy checks.

## Alternatives considered

- Moving ALL threshold validation out of `__post_init__` into a separate function: rejected because threshold checks are single-value validations that belong naturally in `__post_init__`.
- Removing `admin_token` entirely: rejected because the plan's decision adds ADMIN role, which requires `admin_token`.

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

1. Add `_validate_cross_field()` function that calls `_validate_token_combinations()` and `_validate_deployment_mode()`.
2. Add `_validate_token_combinations()` function that allows publisher-only and monitoring-only deployments.
3. Add `_validate_deployment_mode()` function that validates loopback binding and non-empty `auth_token`.
4. Remove cross-field validation from `load_config()` (the per-role token check at lines 198-206).
5. Call `_validate_cross_field(cfg)` after `EventBusConfig(...)` instantiation in `load_config()`.
6. Keep `admin_token` field in EventBusConfig dataclass (it is needed for ADMIN role).
7. Keep `admin_token` in `_KNOWN_CONFIG_KEYS`, `_CONFIG_KEY_TYPES`, and `_REQUIRED_CONFIG_KEYS` (no changes needed here — it is already present).

### Method

**Phase 1: Key presence validation** (already in place in `load_config()`)
- Reject unknown keys (existing, no change needed)
- Validate required keys exist (existing, no change needed)

**Phase 2: Per-key type/value validation** (already in place in `load_config()`)
- Type checking for each key (existing, no change needed)
- Single-value constraints in `__post_init__` (existing, no change needed)

**Phase 3: Cross-field policy validation** (new)
- Add `_validate_cross_field(cfg)` called after `EventBusConfig(...)` creation
- Add `_validate_token_combinations(cfg)` — new function
- Add `_validate_deployment_mode(cfg)` — new function

### Details

**New function: `_validate_cross_field()`**

```python
def _validate_cross_field(cfg: EventBusConfig) -> None:
    """Validate cross-field relationships after per-key validation passes."""
    # Threshold relationships
    if cfg.slow_consumer_threshold >= cfg.subscriber_queue_maxsize:
        raise ValueError(
            "slow_consumer_threshold must be less than subscriber_queue_maxsize"
        )
    if cfg.backlog_health_threshold > cfg.subscriber_queue_maxsize:
        raise ValueError(
            "backlog_health_threshold must be less than or equal to subscriber_queue_maxsize"
        )
    
    # Token combination rules
    _validate_token_combinations(cfg)
    
    # Deployment mode validation
    _validate_deployment_mode(cfg)
```

**New function: `_validate_token_combinations()`**

```python
def _validate_token_combinations(cfg: EventBusConfig) -> None:
    """Validate that required tokens are present based on enabled capabilities."""
    has_any_token = bool(cfg.auth_token) or any([
        cfg.publisher_token,
        cfg.consumer_token,
        cfg.operator_token,
        cfg.monitoring_token,
        cfg.admin_token,
    ])
    
    if not has_any_token:
        raise ValueError("At least one authentication token must be configured")
```

**New function: `_validate_deployment_mode()`**

```python
def _validate_deployment_mode(cfg: EventBusConfig) -> None:
    """Validate deployment mode consistency."""
    if _is_public_host(cfg.host):
        raise ValueError(
            f"Event Bus bound to non-loopback address {cfg.host}. "
            "The API has no authentication — this is a security risk."
        )
    if not cfg.auth_token:
        raise ValueError("auth_token is required but not configured")
```

**Update `load_config()`**: Replace the existing cross-field validation block (lines 198-206) with a call to `_validate_cross_field(cfg)`:

```python
# Before (lines 198-206):
if not any(
    [
        data.get("consumer_token"),
        data.get("operator_token"),
        data.get("admin_token"),
    ]
):
    raise ValueError("At least one per-role token must be configured")

# After:
_validate_cross_field(cfg)
```

**Note**: The threshold validation currently in `__post_init__()` (lines 73-80) will remain there as-is. It is single-value constraint validation, not cross-field policy validation. If desired, these could be moved to `_validate_cross_field()` later, but that is outside this scope.

## Compatibility considerations

- **Breaking change**: The token combination rule changes from "at least one per-role token must be configured" to "either auth_token OR at least one per-role token". This allows configurations that previously failed validation (publisher-only, monitoring-only). Existing configurations with `auth_token` set will continue to work.
- **admin_token retention**: Keeping `admin_token` in the config schema aligns with the plan's decision to add ADMIN role. If the plan had decided to remove `admin_token`, this would have been a breaking change removing a known config key.

## Security considerations

- **Fail-closed on invalid security settings**: All cross-field validation errors raise `ValueError`, preventing misconfigured deployments from running.
- **Non-loopback host rejection**: `_validate_deployment_mode()` enforces loopback-only binding when `auth_token` is empty, consistent with existing behavior in `__post_init__`.
- **Admin token grants all roles**: `admin_token` continues to grant every role via `_populate_token_maps()` in `auth.py`, matching the plan's design for ADMIN role.

## Rollback considerations

- **Reverting token combination rule**: If the new rule causes operational issues, revert to the old "at least one per-role token" check. The old code is preserved in git history.
- **admin_token removal**: If the plan's decision to add ADMIN role is reversed, `admin_token` can be removed from the config schema without affecting other functionality.

## Validation plan

- Unit tests for `_validate_cross_field()` covering threshold relationship violations.
- Unit tests for `_validate_token_combinations()` covering all supported combinations (publisher-only, monitoring-only, consumer+operator, etc.).
- Unit tests for `_validate_deployment_mode()` covering public host rejection and missing `auth_token`.
- Regression tests: all existing config tests must still pass.
- Lint/format: `uv run ruff check scripts/eventbus/config.py --fix && uv run ruff check scripts/eventbus/config.py`
- Type checking: `uv run mypy scripts/eventbus/config.py`

## Completion criteria

- `_validate_cross_field()`, `_validate_token_combinations()`, and `_validate_deployment_mode()` functions exist and are called from `load_config()`.
- Cross-field validation is no longer performed inline in `load_config()`.
- Threshold validation remains in `__post_init__()` (unchanged).
- `admin_token` field is retained in EventBusConfig dataclass.
- All existing config tests pass without modification.
- New tests cover all validation error paths.

## Out of scope

- Modifying `scripts/eventbus/auth.py` (ADMIN role addition — handled by its own procedure document).
- Adding tests for unified 401 response format (handled by its own procedure document).
- Updating `config/eventbus.toml` example configuration (handled by its own procedure document).
- Moving threshold validation from `__post_init__` to `_validate_cross_field()` (future improvement, not in current scope).

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260914-102535_eventbus09_config-validation-role-token-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-175822_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-235154
- **Related target files**: scripts/eventbus/config.py
