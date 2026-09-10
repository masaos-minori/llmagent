## Goal

Centralize three operational thresholds into `EventBusConfig` with validated relationships between them, so tuning requires editing one source rather than three separate modules. Preserve today's hardcoded values as defaults so behavior is unchanged unless an operator explicitly reconfigures them.

## Scope

Modify `scripts/eventbus/config.py`:
- Add three new fields to `EventBusConfig` dataclass: `slow_consumer_threshold: int = 100`, `subscriber_queue_maxsize: int = 1000`, `backlog_health_threshold: int = 500` (REQ-001).
- Add relationship validation in `__post_init__`: `slow_consumer_threshold < subscriber_queue_maxsize` and `backlog_health_threshold <= subscriber_queue_maxsize` (REQ-002).
- Update `load_config()` to read new fields from TOML data, using defaults if absent (REQ-001).

## Assumptions

- The three thresholds should remain as integer fields in `EventBusConfig` (matching their current types: `_SLOW_CONSUMER_THRESHOLD = 100` is int, `maxsize=1000` is int, `>= 500` is int comparison).
- The validation order in `__post_init__` should follow the existing pattern: validate port range first, then retry count, then host constraint, then the new threshold relationships.
- The TOML configuration file will need new entries for these fields, but they will have defaults so existing configs without these fields continue to work.

## Design decisions

1. **Config field addition (REQ-001)**: Add three new fields to `EventBusConfig`:
    - `slow_consumer_threshold: int = 100`
    - `subscriber_queue_maxsize: int = 1000`
    - `backlog_health_threshold: int = 500`
    
    These match today's hardcoded values exactly. The dataclass is frozen=True, so defaults are settable only through `__post_init__` or field defaults.

2. **Relationship validation (REQ-002)**: In `__post_init__`, after existing validations:
    - `slow_consumer_threshold < subscriber_queue_maxsize` (strictly less — a consumer at exactly the queue capacity is not yet "slow")
    - `backlog_health_threshold <= subscriber_queue_maxsize` (at most equal — a backlog equal to queue capacity is the worst case)
    
    Raise `ValueError` with actionable messages naming both conflicting values.

3. **TOML backward compatibility**: Use `data.get("field", default_value)` pattern in `load_config()` so missing fields fall back to safe defaults. This prevents startup failures for existing configs that lack the new fields.

## Alternatives considered

- Adding the fields via `__post_init__` instead of dataclass defaults: would require setting `object.__setattr__(self, ...)` since the dataclass is frozen=True; using field defaults is cleaner.
- Raising `RuntimeError` for invalid combinations instead of `ValueError`: `ValueError` is more semantically correct for config validation errors.
- Using `typing.Literal` for the threshold types: unnecessary complexity; plain `int` is sufficient.

## Implementation
### Target file
`scripts/eventbus/config.py`

### Procedure
1. Phase 1: Preparation — Add new fields to EventBusConfig dataclass
2. Phase 2: Core Logic — Add relationship validation in __post_init__
3. Phase 3: Core Logic — Update load_config() to handle new fields

### Method
#### Phase 1: Preparation
- [ ] Add `slow_consumer_threshold: int = 100`, `subscriber_queue_maxsize: int = 1000`, `backlog_health_threshold: int = 500` fields to `EventBusConfig` dataclass (REQ-001; `scripts/eventbus/config.py`)

#### Phase 2: Core Logic
- [ ] Add relationship validation in `__post_init__`: `slow_consumer_threshold < subscriber_queue_maxsize` and `backlog_health_threshold <= subscriber_queue_maxsize` (REQ-002; `scripts/eventbus/config.py`)

#### Phase 3: Core Logic
- [ ] Update `load_config()` to read new fields from TOML data, using defaults if absent (REQ-001; `scripts/eventbus/config.py`)

### Details

**Phase 1: Preparation**

Add three new fields to `EventBusConfig` dataclass after the existing `auth_token` field:

```python
@dataclass(frozen=True)
class EventBusConfig:
    """Immutable configuration for the Event Bus service.

    Validates port range, retry count, and enforces loopback-only binding.
    """

    port: int
    db_path: str
    storage_dir: str
    offsets_dir: str
    deadletter_dir: str
    max_retry: int
    host: str = "127.0.0.1"
    auth_token: str = ""
    # New threshold fields
    slow_consumer_threshold: int = 100
    subscriber_queue_maxsize: int = 1000
    backlog_health_threshold: int = 500
```

**Phase 2: Core Logic**

Add relationship validation in `__post_init__` after existing validations:

```python
def __post_init__(self) -> None:
    """Validate configuration values after initialization."""
    if not 1024 <= self.port <= 65535:
        raise ValueError(f"port must be 1024-65535, got {self.port}")
    if self.max_retry < 1:
        raise ValueError(f"max_retry must be >= 1, got {self.max_retry}")
    if _is_public_host(self.host):
        raise ValueError(
            f"Event Bus bound to non-loopback address {self.host}. "
            "The API has no authentication — this is a security risk."
        )
    if not self.auth_token:
        raise ValueError("auth_token is required but not configured")
    
    # REQ-002: Validate threshold relationships
    if self.slow_consumer_threshold >= self.subscriber_queue_maxsize:
        raise ValueError(
            f"slow_consumer_threshold ({self.slow_consumer_threshold}) must be less than "
            f"subscriber_queue_maxsize ({self.subscriber_queue_maxsize})"
        )
    if self.backlog_health_threshold > self.subscriber_queue_maxsize:
        raise ValueError(
            f"backlog_health_threshold ({self.backlog_health_threshold}) must be <= "
            f"subscriber_queue_maxsize ({self.subscriber_queue_maxsize})"
        )
```

**Phase 3: Core Logic**

Update `load_config()` to read new fields from TOML data, using defaults if absent:

```python
def load_config(path: Path | None = None) -> EventBusConfig:
    """Load and validate the EventBus TOML configuration file. Callers must always pass get_config_path()'s return value — this function does not itself restrict which path is read; see tests/eventbus/test_eventbus_config.py for the call-site regression test that locks this invariant."""
    p = path or _DEFAULT_CONFIG_PATH
    with p.open("rb") as f:
        data = tomllib.load(f)

    # Reject unknown keys
    unknown_keys = set(data.keys()) - _KNOWN_CONFIG_KEYS
    if unknown_keys:
        raise ValueError(
            f"eventbus config contains unknown key(s): {', '.join(sorted(unknown_keys))}. "
            f"Known keys are: {', '.join(sorted(_KNOWN_CONFIG_KEYS))}."
        )

    # Validate required keys exist
    missing_keys = _KNOWN_CONFIG_KEYS - set(data.keys())
    if missing_keys:
        raise ValueError(
            f"eventbus config missing required key(s): {', '.join(sorted(missing_keys))}."
        )

    # Validate types
    for key, expected_type in _CONFIG_KEY_TYPES.items():
        value = data[key]
        if not isinstance(value, expected_type):
            raise ValueError(
                f"eventbus config key '{key}' has type {type(value).__name__}, "
                f"expected {expected_type.__name__}."
            )

    # Validate auth_token is non-empty
    if not data["auth_token"]:
        raise ValueError("eventbus config 'auth_token' must not be empty.")

    # REQ-001: Read new threshold fields with defaults for backward compatibility
    return EventBusConfig(
        port=data["port"],
        db_path=data["db_path"],
        storage_dir=data["storage_dir"],
        offsets_dir=data["offsets_dir"],
        deadletter_dir=data["deadletter_dir"],
        max_retry=data["max_retry"],
        host=data.get("host", "127.0.0.1"),
        auth_token=data["auth_token"],
        slow_consumer_threshold=data.get("slow_consumer_threshold", 100),
        subscriber_queue_maxsize=data.get("subscriber_queue_maxsize", 1000),
        backlog_health_threshold=data.get("backlog_health_threshold", 500),
    )
```

## Compatibility considerations

- Existing TOML configs that lack the new threshold fields will use defaults (backward compatible).
- The dataclass defaults (`= 100`, `= 1000`, `= 500`) provide additional fallback safety.
- No changes needed to callers — `EventBusConfig` construction remains the same.

## Security considerations

- The validation rules prevent misconfiguration that could hide operational issues (e.g., slow-consumer threshold above queue capacity would make health check unreachable).
- Invalid combinations fail startup with actionable errors rather than silently producing misleading health status.

## Rollback considerations

- Reverting the threshold fields requires reverting the validation logic and `load_config()` updates simultaneously.
- If reverted during runtime, the dataclass defaults ensure behavior reverts to original hardcoded values.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/config.py` | Unit — config validation | `uv run pytest tests/eventbus/test_eventbus_config.py -k "threshold" -v` | New validation tests pass |
| `scripts/eventbus/config.py` | Unit — default preservation | `uv run pytest tests/eventbus/test_eventbus_config.py -v` | All config tests pass |
| `scripts/eventbus/config.py` | Lint | `uv run ruff check scripts/eventbus/config.py` | Clean |
| `scripts/eventbus/config.py` | Type check | `uv run mypy scripts/eventbus/config.py` | Pass |

## Completion criteria

- Three new threshold fields added to `EventBusConfig` with defaults matching today's hardcoded values (100, 1000, 500) — REQ-001
- Relationship validation enforced in `__post_init__` (slow-consumer threshold < queue capacity, backlog threshold <= queue capacity) — REQ-002
- `load_config()` reads new fields from TOML with defaults for backward compatibility — REQ-001
- All existing `test_eventbus_config.py` tests still pass — REQ-001

## Out of scope

- Deriving threshold values from load-test measurement (EB-M05).
- Backpressure disconnect behavior itself (EB-H02).
- Changing the DLQ sweep interval (`_DLQ_INTERVAL = 60.0` in `app.py`).
- Updating broker.py, health_route.py, or documentation (covered by other implementation procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add three threshold fields to EventBusConfig dataclass | Pending | — | — | |
| 2 | Add relationship validation in __post_init__ | Pending | — | — | |
| 3 | Update load_config() to handle new fields | Pending | — | — | |
| 4 | Add or update tests per Validation plan | Pending | — | — | |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260907-125042_eb_l02_centralize_operational_thresholds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260910-072350_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-065129
- **Related target files**: scripts/eventbus/config.py
