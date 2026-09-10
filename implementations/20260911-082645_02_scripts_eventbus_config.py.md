## Goal

Add replay batch size, subscriber count, retained-event count, publish rate fields.

## Scope

Modify `scripts/eventbus/config.py`:
- Add `replay_batch_size` field to `EventBusConfig` (REQ-002; `scripts/eventbus/config.py`).
- Add `subscriber_count` field to `EventBusConfig` (REQ-001; `scripts/eventbus/config.py`).
- Add `retained_event_count` field to `EventBusConfig` (REQ-001; `scripts/eventbus/config.py`).
- Add `publish_rate` field to `EventBusConfig` (REQ-001; `scripts/eventbus/config.py`).
- Update `_KNOWN_CONFIG_KEYS` and `_CONFIG_KEY_TYPES` to include new fields (REQ-001; `scripts/eventbus/config.py`).

## Assumptions

- The replay batch size should be configurable via `EventBusConfig` — default value TBD from load testing.
- The register-before-replay ordering must be preserved exactly — batching the SQLite fetch must not change when the broker subscription is registered relative to the replay query.
- Separate read connections or a connection-pool/manager should only be decided after load-test results are available — do not implement speculatively.
- Database-lock instrumentation should use Python's `time.monotonic()` for accurate timing.

## Design decisions

1. **New capacity-related fields (REQ-001)**: Add the following fields to `EventBusConfig`:
   - `replay_batch_size`: int — default TBD from load testing. Controls how many rows are fetched per batch during initial replay.
   - `subscriber_count`: int — default TBD from load testing. Maximum number of concurrent subscribers before capacity limits apply.
   - `retained_event_count`: int — default TBD from load testing. Number of events retained in SQLite for replay.
   - `publish_rate`: float — default TBD from load testing. Maximum publish rate (events/sec) before backpressure applies.

2. **Update config key registry**: Add new fields to `_KNOWN_CONFIG_KEYS` and `_CONFIG_KEY_TYPES` to ensure they're recognized as valid configuration keys.

3. **Validation logic**: Add post-init validation for new fields (e.g., `replay_batch_size >= 1`, `subscriber_count >= 1`, etc.).

## Alternatives considered

- Using a single `capacity_limits` dict field instead of separate fields: would reduce field count but makes individual validation harder.
- Adding a separate `CapacityConfig` class: overkill for current needs; keep capacity fields in `EventBusConfig` for simplicity.
- Making all capacity fields optional with None defaults: would require null checks throughout the codebase; prefer sensible defaults.

## Implementation
### Target file
`samples/eventbus/config.py`

### Procedure
Add capacity-related fields to `EventBusConfig`; update config key registry and validation logic.

### Method
1. Add four new fields to `EventBusConfig` dataclass: `replay_batch_size`, `subscriber_count`, `retained_event_count`, `publish_rate`.
2. Update `_KNOWN_CONFIG_KEYS` to include new field names.
3. Update `_CONFIG_KEY_TYPES` to map new field names to their types.
4. Add post-init validation for new fields (e.g., `replay_batch_size >= 1`, `subscriber_count >= 1`, etc.).

### Details
```python
# In EventBusConfig (config.py):
replay_batch_size: int = 1000  # default TBD from load testing
subscriber_count: int = 10     # default TBD from load testing
retained_event_count: int = 10000  # default TBD from load testing
publish_rate: float = 100.0    # default TBD from load testing

def __post_init__(self) -> None:
    """Validate configuration values after initialization."""
    # ... existing validation ...
    
    # New validation for capacity fields
    if self.replay_batch_size < 1:
        raise ValueError(f"replay_batch_size must be >= 1, got {self.replay_batch_size}")
    if self.subscriber_count < 1:
        raise ValueError(f"subscriber_count must be >= 1, got {self.subscriber_count}")
    if self.retained_event_count < 1:
        raise ValueError(f"retained_event_count must be >= 1, got {self.retained_event_count}")
    if self.publish_rate <= 0:
        raise ValueError(f"publish_rate must be > 0, got {self.publish_rate}")

# Update _KNOWN_CONFIG_KEYS:
_KNOWN_CONFIG_KEYS = frozenset((
    "port",
    "db_path",
    "storage_dir",
    "offsets_dir",
    "deadletter_dir",
    "max_retry",
    "host",
    "auth_token",
    "replay_batch_size",
    "subscriber_count",
    "retained_event_count",
    "publish_rate",
))

# Update _CONFIG_KEY_TYPES:
_CONFIG_KEY_TYPES: dict[str, type] = {
    "port": int,
    "db_path": str,
    "storage_dir": str,
    "offsets_dir": str,
    "deadletter_dir": str,
    "max_retry": int,
    "host": str,
    "auth_token": str,
    "replay_batch_size": int,
    "subscriber_count": int,
    "retained_event_count": int,
    "publish_rate": float,
}
```

## Compatibility considerations

- Existing deployments that don't provide values for the new fields will need to either:
  1. Use the default values (if defaults are provided), or
  2. Be updated to include the new fields in their configuration files.
- The new fields should have sensible defaults to avoid breaking existing deployments.
- Configuration migration: if existing configs don't include the new fields, the system should fall back to defaults rather than failing.

## Security considerations

- No security impact — this change is purely about resource management and observability.
- The new capacity fields don't affect authentication or authorization logic.

## Rollback considerations

- If the new capacity fields cause issues (e.g., incorrect defaults, validation failures), revert to the original `EventBusConfig` without these fields.
- The `_KNOWN_CONFIG_KEYS` and `_CONFIG_KEY_TYPES` updates can be reverted without affecting functionality if reverted.
- Default values can be adjusted without requiring a full rollback.

## Validation plan

- Configuration loading test: verify new fields are accepted and validated correctly.
- Default value test: verify defaults are used when new fields are not provided.
- Backward compatibility test: verify existing configurations without new fields still work with defaults.
- Capacity limit enforcement test: verify capacity limits are enforced based on new fields.

## Completion criteria

- [ ] Define supported publish rate, subscriber count, retained-event count, replay size, and latency objectives based on representative load testing — REQ-001
- [ ] Read initial replay in bounded, configurable batches — REQ-002
- [ ] Capacity limits and their test methodology are documented — REQ-006

## Out of scope

- `/replay` endpoint's own pagination/snapshot-consistency issue (EB-M04).
- Centralizing the currently-hardcoded operational thresholds (`_SLOW_CONSUMER_THRESHOLD`, queue `maxsize`, health's `500` backlog threshold) into validated configuration — tracked separately in this batch.
- Deciding on separate read connections or connection manager — defer until load-test results justify it.

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
- **Requirement ID**: {the Requirement ID(s) from the Plan's Implementation Target Files row this document implements, e.g. `REQ-003`}
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {exact repository-relative path of the target plan file}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file_path}
