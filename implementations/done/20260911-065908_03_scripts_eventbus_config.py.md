## Goal

Add configurable SSE heartbeat interval to `EventBusConfig` so idle connections stay alive through heartbeats without changing the existing `since_seq`/`consumer_id` resume mechanism. Preserve today's hardcoded value as default so behavior is unchanged unless an operator explicitly reconfigures it.

## Scope

Modify `scripts/eventbus/config.py`:
- Add `sse_heartbeat_interval: float = 30.0` field to `EventBusConfig` dataclass (REQ-001; `scripts/eventbus/config.py`).
- Update `load_config()` to read `sse_heartbeat_interval` from TOML data, defaulting to 30.0 if absent (REQ-001; `scripts/eventbus/config.py`).

## Assumptions

- The heartbeat interval should be configurable via `EventBusConfig` (defaulting to a reasonable value like 30 seconds if absent from TOML).
- The `Last-Event-ID` header should be parsed as an integer representing the last received `seq` value.
- The `id:` field should contain the event's `seq` number, which is monotonic across all events regardless of topic.
- The heartbeat should be an SSE comment line (`: heartbeat\n\n`), not a `data:` event, so it does not appear as a delivered event to `EventSource`-based clients.
- The `replay_ceil`-based duplicate-discard logic in `subscribe_route.py` should remain unchanged when adding the `id:` field.

## Design decisions

1. **Heartbeat implementation (REQ-001)**: Spawn an `asyncio.Task` in `_sse_gen()` that periodically yields `: heartbeat\n\n` during the live phase. The task is cancelled in the `finally` block alongside subscriber unregistration. Default interval: 30 seconds (documented as half of common 60s proxy timeout).

2. **Event ID emission (REQ-002)**: In both `_sse_gen()` functions, yield `f"id:{row['seq']}\ndata:{data}\n\n"` instead of just `f"data:{data}\n\n"`. This preserves backward compatibility — `EventSource`-based clients will use the `id:` field for auto-reconnect, while other clients can ignore it.

3. **Last-Event-ID parsing (REQ-003)**: In `subscribe_route.subscribe()`, read `request.headers.get("last-event-id", "")` and parse as int. Used only when `since_seq == 0` AND no persisted consumer offset exists. Precedence: `since_seq` > consumer offset > `Last-Event-ID`.

4. **Precedence definition (REQ-004)**: Define explicitly in documentation:
    - Priority 1: Explicit `since_seq` query parameter (highest)
    - Priority 2: Persisted consumer offset (from `consumer_id`)
    - Priority 3: `Last-Event-ID` header (lowest — fallback for `EventSource` clients)

5. **Task lifecycle (REQ-005)**: The heartbeat task is created in the `try` block before entering the live phase and cancelled in the `finally` block. This follows the existing pattern of `broker.unsubscribe(sub)` in the `finally` block.

6. **Stale reconnect rejection (UNK-02 decision)**: Reject `Last-Event-ID` reconnects where the requested `seq` exceeds the current max seq in SQLite. Return HTTP 412 Precondition Failed with the current max seq in the response body. This prevents clients from requesting events that have already been garbage-collected.

## Alternatives considered

- Using `time.sleep()` instead of `asyncio.sleep()` for heartbeat intervals: would block the event loop; `asyncio.sleep()` is non-blocking.
- Adding heartbeat as a separate endpoint rather than embedding in the generator: adds unnecessary complexity for a simple keepalive mechanism.
- Accepting all `Last-Event-ID` values without validation: risks returning stale or non-existent events.
- Raising `ValueError` for invalid `Last-Event-ID` values: less user-friendly than silently ignoring them.

## Implementation
### Target file
`scripts/eventbus/config.py`

### Procedure
1. Phase 1: Preparation — Add new fields to EventBusConfig dataclass
2. Phase 2: Core Logic — Update load_config() to handle new fields

### Method
#### Phase 1: Preparation
- [ ] Add `sse_heartbeat_interval: float = 30.0` field to `EventBusConfig` dataclass (REQ-001; `scripts/eventbus/config.py`)

#### Phase 2: Core Logic
- [ ] Update `load_config()` to read `sse_heartbeat_interval` from TOML data, using defaults if absent (REQ-001; `scripts/eventbus/config.py`)

### Details

**Phase 1: Preparation**

Add the new threshold field to `EventBusConfig` dataclass after the existing `auth_token` field:

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
    # New SSE heartbeat field
    sse_heartbeat_interval: float = 30.0
```

**Phase 2: Core Logic**

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

    # REQ-001: Read new SSE heartbeat interval with default for backward compatibility
    return EventBusConfig(
        port=data["port"],
        db_path=data["db_path"],
        storage_dir=data["storage_dir"],
        offsets_dir=data["offsets_dir"],
        deadletter_dir=data["deadletter_dir"],
        max_retry=data["max_retry"],
        host=data.get("host", "127.0.0.1"),
        auth_token=data["auth_token"],
        sse_heartbeat_interval=data.get("sse_heartbeat_interval", 30.0),
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
