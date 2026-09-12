## Goal

Add per-role token fields to `config/eventbus.toml` and update `EventBusConfig` class to support them (REQ-004).

## Scope

- **In-Scope**: Modifying `config/eventbus.toml` to add per-role token fields
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- The EventBusConfig class will be updated to include `consumer_token`, `operator_token`, and `admin_token` fields
- The existing single-shared-token deployment model must not break unless a migration path is designed (REQ-005)
- Per-role tokens will be added as optional fields that default to None when not configured

## Design decisions

- Add three new optional fields to EventBusConfig: `consumer_token`, `operator_token`, `admin_token`
- These fields will be populated from the TOML config file during initialization
- If any field is None, the corresponding role check will fall back to the shared token mechanism
- This ensures backward compatibility with existing deployments that don't configure per-role tokens

## Alternatives considered

- Adding per-role tokens as required fields — would break existing deployments that don't configure them
- Adding per-role tokens as environment variables — would require changes to deployment infrastructure
- Adding per-role tokens as command-line arguments — would require changes to startup scripts

## Implementation

### Target file

`config/eventbus.toml`

### Procedure

1. Add `consumer_token` field to EventBusConfig class
2. Add `operator_token` field to EventBusConfig class
3. Add `admin_token` field to EventBusConfig class
4. Update the config file to include these fields

### Method

For each field:
- Add a new optional field to the EventBusConfig dataclass
- Initialize the field to None by default
- Populate the field from the TOML config file during initialization

### Details

#### Step 1: Update EventBusConfig class

```python
# Before:
@dataclass
class EventBusConfig:
    """Configuration for the EventBus service."""
    
    port: int = 8015
    db_path: str = "/opt/llm/db/eventbus.sqlite"
    storage_dir: str = "/opt/llm/storage"
    offsets_dir: str = "/opt/llm/offsets"
    deadletter_dir: str = "/opt/llm/deadletter"
    max_retry: int = 3
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure directories exist
        for dir_path in [self.storage_dir, self.offsets_dir, self.deadletter_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

# After:
@dataclass
class EventBusConfig:
    """Configuration for the EventBus service."""
    
    port: int = 8015
    db_path: str = "/opt/llm/db/eventbus.sqlite"
    storage_dir: str = "/opt/llm/storage"
    offsets_dir: str = "/opt/llm/offsets"
    deadletter_dir: str = "/opt/llm/deadletter"
    max_retry: int = 3
    
    # REQ-004: Per-role tokens for authorization
    consumer_token: str | None = None
    operator_token: str | None = None
    admin_token: str | None = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure directories exist
        for dir_path in [self.storage_dir, self.offsets_dir, self.deadletter_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Validate that at least one token type is configured
        if not any([self.consumer_token, self.operator_token, self.admin_token]):
            raise ValueError("At least one token type must be configured")
```

#### Step 2: Update config file

```toml
# Before:
# eventbus configuration

port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3

# After:
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

- [ ] `consumer_token` field added to EventBusConfig class
- [ ] `operator_token` field added to EventBusConfig class
- [ ] `admin_token` field added to EventBusConfig class
- [ ] Config file updated with per-role token fields
- [ ] Tests pass with the new authorization model

## Out of scope

- Changes to `scripts/eventbus/app.py` (handled in separate procedure document)
- Changes to `scripts/eventbus/auth.py` (handled in separate procedure document)
- Changes to test files (handled in separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add consumer_token field | Pending | — | — | |
| 2 | Add operator_token field | Pending | — | — | |
| 3 | Add admin_token field | Pending | — | — | |
| 4 | Update config file | Pending | — | — | |
| 5 | Run validation tests | Pending | — | — | |

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
- **Related target files**: config/eventbus.toml
