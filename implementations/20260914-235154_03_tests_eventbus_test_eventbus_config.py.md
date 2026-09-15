## Goal

Add focused tests for each validation error; cover all supported token combinations.

## Scope

- `tests/eventbus/test_eventbus_config.py`: Add tests for cross-field validation errors (T-1, T-2), per-role token validation (T-3), admin role existence (T-4), admin token handling (T-5), publisher-only deployment (T-6), monitoring-only deployment (T-7); verify all existing tests still pass (T-10).

## Assumptions

- A: The plan's decision to add ADMIN role means `admin_token` should be retained in the config schema.
- B: The plan's decision to allow publisher-only and monitoring-only deployments means these configurations must NOT raise validation errors.
- C: Existing tests already cover some cross-field validation scenarios (e.g., `test_slow_consumer_threshold_equal_to_maxsize_raises`, `test_backlog_health_threshold_exceeds_maxsize_raises`).

## Design decisions

- **Reuse existing test infrastructure**: Use `EventBusConfig` dataclass instantiation directly for unit-level tests; use `load_config()` for integration-level tests that require TOML parsing.
- **Test both positive and negative cases**: For each validation rule, test both the error case (should raise ValueError) and the success case (should not raise).
- **Separate cross-field from single-value tests**: Tests for threshold relationships belong in `__post_init__` testing; tests for token combination rules belong in `_validate_token_combinations` testing.

## Alternatives considered

- Using `pytest.fixture` for common config setup: rejected because the existing tests use inline config construction, and adding fixtures would change the test style unnecessarily.
- Testing via `load_config()` only: rejected because `EventBusConfig` instantiation provides more direct control over which validation path is exercised.

## Implementation

### Target file

`tests/eventbus/test_eventbus_config.py`

### Procedure

1. Add test for cross-field validation error: `slow_consumer_threshold >= subscriber_queue_maxsize` (T-1).
2. Add test for cross-field validation error: `backlog_health_threshold > subscriber_queue_maxsize` (T-2).
3. Add test for per-role token validation: at least one required when `auth_token` is empty (T-3).
4. Add test for admin role existence: Role.ADMIN exists in enum (T-4).
5. Add test for admin token handling: admin_token grants all roles (T-5).
6. Add test for publisher-only deployment: should succeed with only `publisher_token` + `auth_token` (T-6).
7. Add test for monitoring-only deployment: should succeed with only `monitoring_token` + `auth_token` (T-7).
8. Verify all existing tests still pass (T-10).

### Method

**Step 1: Add T-1 — Cross-field validation error for slow_consumer_threshold >= subscriber_queue_maxsize**

```python
def test_cross_field_slow_consumer_threshold_exceeds_maxsize() -> None:
    """REQ-001, REQ-002: slow_consumer_threshold must be strictly less than subscriber_queue_maxsize."""
    # This test verifies the cross-field validation in _validate_cross_field().
    # Note: EventBusConfig.__post_init__ also validates this constraint,
    # but the cross-field function will be called after __post_init__ in load_config().
    with pytest.raises(ValueError, match="slow_consumer_threshold"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            auth_token="test-token",
            slow_consumer_threshold=1000,
            subscriber_queue_maxsize=1000,
            backlog_health_threshold=500,
        )
```

**Step 2: Add T-2 — Cross-field validation error for backlog_health_threshold > subscriber_queue_maxsize**

```python
def test_cross_field_backlog_health_threshold_exceeds_maxsize() -> None:
    """REQ-001, REQ-002: backlog_health_threshold must be <= subscriber_queue_maxsize."""
    with pytest.raises(ValueError, match="backlog_health_threshold"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            auth_token="test-token",
            slow_consumer_threshold=100,
            subscriber_queue_maxsize=1000,
            backlog_health_threshold=1001,
        )
```

**Step 3: Add T-3 — Per-role token validation: at least one required**

```python
def test_load_config_requires_at_least_one_token() -> None:
    """REQ-006: At least one authentication token must be configured."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
host = "127.0.0.1"
""")
    with pytest.raises(ValueError, match="authentication token"):
        load_config(config_file)
```

**Step 4: Add T-4 — Admin role existence test**

```python
def test_admin_role_exists_in_enum() -> None:
    """REQ-004: Role.ADMIN must exist in the Role enum."""
    from eventbus.auth import Role
    
    assert hasattr(Role, "ADMIN"), "Role.ADMIN must exist"
    assert Role.ADMIN == "admin", f"Role.ADMIN value must be 'admin', got {Role.ADMIN!r}"
```

**Step 5: Add T-5 — Admin token handling test**

```python
def test_admin_token_grants_all_roles() -> None:
    """REQ-004, REQ-005: admin_token grants every role via _populate_token_maps()."""
    from eventbus.auth import Role, _populate_token_maps, _TOKEN_ROLE_MAP
    
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        auth_token="shared-token",
        admin_token="admin-token",
    )
    
    _populate_token_maps(cfg)
    
    assert "admin-token" in _TOKEN_ROLE_MAP
    assert set(_TOKEN_ROLE_MAP["admin-token"]) == set(Role)
```

**Step 6: Add T-6 — Publisher-only deployment test**

```python
def test_publisher_only_deployment_succeeds() -> None:
    """REQ-006: Publisher-only deployment (only publisher_token + auth_token) is allowed."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
host = "127.0.0.1"
auth_token = "test-auth-token"
publisher_token = "test-publisher-token"
""")
    cfg = load_config(config_file)
    assert cfg.publisher_token == "test-publisher-token"
    assert cfg.auth_token == "test-auth-token"
```

**Step 7: Add T-7 — Monitoring-only deployment test**

```python
def test_monitoring_only_deployment_succeeds() -> None:
    """REQ-006: Monitoring-only deployment (only monitoring_token + auth_token) is allowed."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
host = "127.0.0.1"
auth_token = "test-auth-token"
monitoring_token = "test-monitoring-token"
""")
    cfg = load_config(config_file)
    assert cfg.monitoring_token == "test-monitoring-token"
    assert cfg.auth_token == "test-auth-token"
```

**Step 8: Verify all existing tests still pass (T-10)**

Run the full test suite:
```bash
uv run pytest tests/eventbus/test_eventbus_config.py -v
```

All existing tests must pass without modification.

## Compatibility considerations

- **New validation rule**: The token combination rule changes from "at least one per-role token must be configured" to "either auth_token OR at least one per-role token". Tests for the old rule (e.g., `test_load_config_rejects_missing_per_role_token`) may need adjustment if they rely on the old behavior.
- **Existing test overlap**: `test_slow_consumer_threshold_equal_to_maxsize_raises` and `test_backlog_health_threshold_exceeds_maxsize_raises` already test threshold constraints. The new T-1/T-2 tests are redundant with these existing tests — consider removing the duplicates or keeping them as explicit documentation of the cross-field validation requirement.

## Security considerations

- **Fail-closed on invalid security settings**: All new tests verify that misconfigurations raise ValueError, preventing insecure deployments.
- **Publisher-only/monitoring-only safety**: These modes are safe because they still require `auth_token` (enforced by `__post_init__`), and the loopback host check prevents public binding.

## Rollback considerations

- **Reverting token combination rule**: If the new rule causes operational issues, revert to the old "at least one per-role token" check and remove the publisher-only/monitoring-only tests.

## Validation plan

- Run all new tests: `uv run pytest tests/eventbus/test_eventbus_config.py -v -k "cross_field or admin_role or admin_token or publisher_only or monitoring_only"`
- Run full test suite: `uv run pytest tests/eventbus/test_eventbus_config.py -v`
- Lint/format: `uv run ruff check tests/eventbus/test_eventbus_config.py --fix && uv run ruff check tests/eventbus/test_eventbus_config.py`
- Type checking: `uv run mypy tests/eventbus/test_eventbus_config.py`

## Completion criteria

- All new tests (T-1 through T-7) exist and pass.
- All existing tests (T-10) still pass without modification.
- No regression in test coverage for existing validation rules.
- New tests cover all supported token combinations.

## Out of scope

- Modifying `scripts/eventbus/config.py` (handled by its own procedure document).
- Adding tests for unified 401 response format (handled by its own procedure document).
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
- **Requirement ID**: REQ-003, REQ-007
- **Source issue**: issues/20260914-102535_eventbus09_config-validation-role-token-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-175822_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-235154
- **Related target files**: tests/eventbus/test_eventbus_config.py