## Goal

Harden `load_config()` in `scripts/eventbus/config.py` to reject unknown keys, validate each required key's type, and add the new `auth_token` key — fail-closed, without importing `ConfigLoader` or `get_typed` (both cross-layer imports the isolation contract forbids).

## Scope

- Modify `scripts/eventbus/config.py`:
  - Extend `_REMOVED_CONFIG_KEYS` to include `auth_token` as a new required key
  - Add an allow-list of known keys: `port`, `db_path`, `storage_dir`, `offsets_dir`, `deadletter_dir`, `max_retry`, `host`, `auth_token`
  - Reject any TOML key outside the allow-list
  - Validate each required key's type using `isinstance` checks
  - Add startup validation for `auth_token` presence

## Assumptions

- The `.importlinter` `eventbus-is-isolated` contract forbids importing `shared`/`mcp_servers`; `get_typed()` lives in `scripts/shared/config_utils.py`, off-limits.
- `rules/coding.md`'s Type-coercion policy (mandatory `get_typed`-style validation for `*_models.py` config loaders) is honored in intent, not by direct reuse.
- `auth_token` is a new required key following the existing `auth_token = "${ENV:...}"` convention used by MCP server configs.

## Design decisions

- **Allow-list approach**: Explicit allow-list of 8 known keys (7 existing + `auth_token`) rather than rejecting only removed keys.
- **Type validation**: Per-key `isinstance` checks matching the expected types:
  - `port`: `int`
  - `db_path`, `storage_dir`, `offsets_dir`, `deadletter_dir`: `str`
  - `max_retry`: `int`
  - `host`: `str`
  - `auth_token`: `str` (non-empty)
- **Fail-closed**: Unknown keys raise `ValueError`; missing required keys raise `ValueError`; wrong-type keys raise `ValueError`.

## Alternatives considered

- Migrating to `ConfigLoader`: Architecturally prohibited by `.importlinter` `eventbus-is-isolated` contract; ADR-002 already accepted this exception.
- Using `get_typed()` from `scripts/shared/config_utils.py`: Cannot import per isolation contract.
- Schema-based validation: Overkill for simple TOML config; explicit allow-list sufficient.

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

Modify `scripts/eventbus/config.py` to harden `load_config()` with fail-closed validation for unknown keys, type checking, and `auth_token` support.

### Method

1. Define `_KNOWN_CONFIG_KEYS` as a frozenset of allowed TOML keys.
2. Define `_CONFIG_KEY_TYPES` as a dict mapping key names to their expected Python types.
3. Replace `_REMOVED_CONFIG_KEYS` check with unknown-key rejection.
4. Add per-key type validation before constructing `EventBusConfig`.
5. Add `auth_token` as a new required field to `EventBusConfig`.
6. Add startup validation for `auth_token` presence.

### Details

```python
# scripts/eventbus/config.py — changes only

# After existing constants, add:
_KNOWN_CONFIG_KEYS = frozenset((
    "port",
    "db_path",
    "storage_dir",
    "offsets_dir",
    "deadletter_dir",
    "max_retry",
    "host",
    "auth_token",
))

_CONFIG_KEY_TYPES: dict[str, type] = {
    "port": int,
    "db_path": str,
    "storage_dir": str,
    "offsets_dir": str,
    "deadletter_dir": str,
    "max_retry": int,
    "host": str,
    "auth_token": str,
}

# In EventBusConfig dataclass, add auth_token field:
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
    auth_token: str = ""  # NEW: required for authentication

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
        # NEW: Validate auth_token is present and non-empty
        if not self.auth_token:
            raise ValueError("auth_token is required but not configured")

# Remove _REMOVED_CONFIG_KEYS constant entirely (no longer needed)

def load_config(path: Path | None = None) -> EventBusConfig:
    """Load and validate the EventBus TOML configuration file. Callers must always pass get_config_path()'s return value — this function does not itself restrict which path is read; see tests/eventbus/test_eventbus_config.py for the call-site regression test that locks this invariant."""
    p = path or _DEFAULT_CONFIG_PATH
    with p.open("rb") as f:
        data = tomllib.load(f)
    
    # NEW: Reject unknown keys
    unknown_keys = set(data.keys()) - _KNOWN_CONFIG_KEYS
    if unknown_keys:
        raise ValueError(
            f"eventbus config contains unknown key(s): {', '.join(sorted(unknown_keys))}. "
            f"Known keys are: {', '.join(sorted(_KNOWN_CONFIG_KEYS))}."
        )
    
    # NEW: Validate required keys exist
    missing_keys = _KNOWN_CONFIG_KEYS - set(data.keys())
    if missing_keys:
        raise ValueError(
            f"eventbus config missing required key(s): {', '.join(sorted(missing_keys))}."
        )
    
    # NEW: Validate types
    for key, expected_type in _CONFIG_KEY_TYPES.items():
        value = data[key]
        if not isinstance(value, expected_type):
            raise ValueError(
                f"eventbus config key '{key}' has type {type(value).__name__}, "
                f"expected {expected_type.__name__}."
            )
    
    # NEW: Validate auth_token is non-empty
    if not data["auth_token"]:
        raise ValueError("eventbus config 'auth_token' must not be empty.")
    
    return EventBusConfig(
        port=data["port"],
        db_path=data["db_path"],
        storage_dir=data["storage_dir"],
        offsets_dir=data["offsets_dir"],
        deadletter_dir=data["deadletter_dir"],
        max_retry=data["max_retry"],
        host=data.get("host", "127.0.0.1"),
        auth_token=data["auth_token"],
    )
```

## Compatibility considerations

- Adding `auth_token` to `EventBusConfig` requires updating `config/eventbus.toml` with a valid token before deployment.
- An empty/missing `auth_token` will cause `ValueError` at startup, preventing silent unauthenticated operation.

## Security considerations

- **Fail-closed**: Unknown keys, missing keys, wrong-type keys, and empty `auth_token` all raise `ValueError` — no silent acceptance.
- **No secret logging**: Error messages do not include the actual token value; only log that authentication failed.
- **Startup validation**: `auth_token` must be validated at startup (before the middleware runs) — an empty/missing token must cause `sys.exit(1)`, not silently start unauthenticated.

## Rollback considerations

- Rolling back this change means reverting `load_config()` to its original behavior (rejecting only removed keys, no type checking).
- Removing `auth_token` from `EventBusConfig` would require removing it from `config/eventbus.toml` as well.

## Validation plan

- Unit test: `load_config()` raises `ValueError` for unknown TOML key.
- Unit test: `load_config()` raises `ValueError` for wrong-type key (e.g., `port` as string).
- Unit test: `load_config()` raises `ValueError` for missing required key.
- Unit test: `load_config()` raises `ValueError` for empty `auth_token`.
- Unit test: Existing valid config still loads successfully.
- Run `uv run pytest tests/eventbus/test_eventbus_config.py -v`.

## Completion criteria

- [ ] `_KNOWN_CONFIG_KEYS` allow-list defined
- [ ] `_CONFIG_KEY_TYPES` type mapping defined
- [ ] Unknown-key rejection implemented
- [ ] Missing-key rejection implemented
- [ ] Per-key type validation implemented
- [ ] `auth_token` added to `EventBusConfig` with non-empty validation
- [ ] All config tests passing (positive/negative cases)
- [ ] No cross-layer imports (verified via `PYTHONPATH=scripts uv run lint-imports`)

## Out of scope

- Migrating to `ConfigLoader` (architecturally prohibited).
- Schema-based validation infrastructure.
- Token rotation infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define _KNOWN_CONFIG_KEYS and _CONFIG_KEY_TYPES | Completed | — | — | |
| 2 | Add unknown-key rejection | Completed | — | — | |
| 3 | Add missing-key rejection | Completed | — | — | |
| 4 | Add per-key type validation | Completed | — | — | |
| 5 | Add auth_token to EventBusConfig | Completed | — | — | |
| 6 | Add or update tests per Validation plan | Completed | — | — | |
| 7 | Run the validation sequence (rules/toolchain.md) | Completed | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: scripts/eventbus/config.py
