## Goal

Update `tests/eventbus/test_eventbus_subscribe.py` to use per-role tokens instead of the shared token mechanism (REQ-004).

## Scope

- **In-Scope**: Modifying `tests/eventbus/test_eventbus_subscribe.py` to use per-role tokens
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- The EventBusConfig class will be updated to include `consumer_token`, `operator_token`, and `admin_token` fields
- The existing single-shared-token deployment model must not break unless a migration path is designed (REQ-005)
- Per-role tokens will be added as optional fields that default to None when not configured

## Design decisions

- Update the test fixture to accept per-role tokens
- Update the test cases to use the appropriate per-role token for each route category
- Ensure backward compatibility by allowing the shared token mechanism to work alongside per-role tokens

## Alternatives considered

- Adding per-role tokens as required fields — would break existing deployments that don't configure them
- Adding per-role tokens as environment variables — would require changes to deployment infrastructure
- Adding per-role tokens as command-line arguments — would require changes to startup scripts

## Implementation

### Target file

`tests/eventbus/test_eventbus_subscribe.py`

### Procedure

1. Update the test fixture to accept per-role tokens
2. Update the test cases to use the appropriate per-role token for each route category
3. Ensure backward compatibility by allowing the shared token mechanism to work alongside per-role tokens

### Method

For each test case:
- Update the test fixture to pass per-role tokens
- Update the test cases to use the appropriate per-role token for each route category

### Details

#### Step 1: Update test fixture

```python
# Before:
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
        max_retry=3,
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

# After:
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
        max_retry=3,
        auth_token=None,  # No shared token — using per-role tokens only
        consumer_token="consumer-token",
        operator_token="operator-token",
        admin_token="admin-token",
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer consumer-token"
        yield c
```

## Compatibility considerations

- The new fields are optional and default to None, ensuring backward compatibility with existing deployments
- If no per-role tokens are configured, the system falls back to the shared token mechanism
- The validation logic ensures that at least one token type is configured before starting the service

## Security considerations

- Per-role tokens provide finer-grained access control than the shared token mechanism
- Each role can have its own token, allowing for independent rotation of credentials
- The fallback to shared token mechanism ensures backward compatibility while maintaining security

## Rollback considerations

- If the authorization wiring breaks, roll back to the previous state where authorization was bypassed (security regression)
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/app.py | Integration: verify role-gated access for each endpoint | pytest tests/eventbus/test_eventbus_auth.py | Wrong-role requests get 403 |
| scripts/eventbus/auth.py::require_role | Unit: verify token→role mapping logic | pytest tests/eventbus/test_eventbus_auth.py | All auth tests pass with per-role tokens |

## Completion criteria

- [ ] Test fixture updated to accept per-role tokens
- [ ] Test cases updated to use per-role tokens for each route category
- [ ] Tests pass with the new authorization model

## Out of scope

- Changes to `scripts/eventbus/app.py` (handled in separate procedure document)
- Changes to `scripts/eventbus/auth.py` (handled in separate procedure document)
- Changes to config files (handled in separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test fixture | Pending | — | — | |
| 2 | Update test cases | Pending | — | — | |
| 3 | Run validation tests | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-111042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-144827
- **Related target files**: tests/eventbus/test_eventbus_subscribe.py
