## Goal

Add the loopback-bind regression test (REQ-007) and stricter config-loading tests (REQ-005) to `tests/eventbus/test_eventbus_config.py`.

## Scope

- Modify `tests/eventbus/test_eventbus_config.py`:
  - Add regression test confirming `EventBusConfig(host="0.0.0.0", ...)` raises `ValueError`
  - Add test confirming `load_config()` raises `ValueError` for unknown TOML key
  - Add test confirming `load_config()` raises `ValueError` for wrong-type key (e.g., `port` as string)
  - Add test confirming `load_config()` raises `ValueError` for empty `auth_token`
- No other test file modifications beyond what's listed in the Plan's Implementation Target Files.

## Assumptions

- The existing tests (`test_invalid_port_too_low`, `test_load_config_rejects_stray_poll_interval_ms`, etc.) cover port/max_retry/removed-key validation but no test exercises `EventBusConfig(host=...)` raising for a non-loopback host, nor an unknown/incorrectly-typed key beyond the fixed removed-key list.
- `auth_token` will be added to `config/eventbus.toml` by `REQ-005`'s `load_config()` hardening.
- The test fixture for `config/eventbus.toml` will need to include `auth_token` for positive tests.

## Design decisions

- **Regression test**: Test `EventBusConfig(host="0.0.0.0", ...)` raises `ValueError` — confirms `_is_public_host()`'s existing behavior is unchanged.
- **Unknown-key test**: Test `load_config()` raises `ValueError` for an unrecognized TOML key — confirms fail-closed validation.
- **Wrong-type test**: Test `load_config()` raises `ValueError` for a required key with an incorrect type (e.g., `port` as a string) — confirms type checking.
- **Empty auth_token test**: Test `load_config()` raises `ValueError` for empty `auth_token` — confirms fail-closed validation for authentication.

## Alternatives considered

- Testing all edge cases in a single parametrized test: Would reduce readability; separate tests more maintainable.
- Using a shared test fixture for config files: Would simplify setup; inline fixtures sufficient for these tests.

## Implementation

### Target file

`tests/eventbus/test_eventbus_config.py`

### Procedure

Modify `tests/eventbus/test_eventbus_config.py` to add regression tests for loopback binding, unknown keys, wrong types, and empty `auth_token`.

### Method

1. Add `test_non_loopback_host_raises_value_error()` — confirms `_is_public_host()`'s existing behavior is unchanged.
2. Add `test_load_config_rejects_unknown_key()` — confirms fail-closed validation for unknown TOML keys.
3. Add `test_load_config_rejects_wrong_type()` — confirms type checking for required keys.
4. Add `test_load_config_rejects_empty_auth_token()` — confirms fail-closed validation for empty `auth_token`.

### Details

```python
# scripts/eventbus/test_eventbus_config.py — additions only

import pytest
from pathlib import Path
import tempfile

from eventbus.config import EventBusConfig, load_config, _is_public_host

def test_non_loopback_host_raises_value_error() -> None:
    """REQ-007: Regression test confirming EventBusConfig rejects non-loopback hosts."""
    # IPv4 non-loopback
    with pytest.raises(ValueError, match="non-loopback"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/test.db",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="0.0.0.0",
        )
    
    # IPv6 non-loopback
    with pytest.raises(ValueError, match="non-loopback"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/test.db",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="::ffff:192.168.1.1",
        )

def test_load_config_rejects_unknown_key(tmp_path: Path) -> None:
    """REQ-005: load_config() raises ValueError for unknown TOML keys."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
auth_token = "test-token"
unknown_key = "should-be-rejected"
""")
    with pytest.raises(ValueError, match="unknown key"):
        load_config(config_file)

def test_load_config_rejects_wrong_type(tmp_path: Path) -> None:
    """REQ-005: load_config() raises ValueError for wrong-type keys."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = "not-an-int"
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
auth_token = "test-token"
""")
    with pytest.raises(ValueError, match="type"):
        load_config(config_file)

def test_load_config_rejects_empty_auth_token(tmp_path: Path) -> None:
    """REQ-005: load_config() raises ValueError for empty auth_token."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
auth_token = ""
""")
    with pytest.raises(ValueError, match="auth_token"):
        load_config(config_file)
```

## Compatibility considerations

- The test fixture for `config/eventbus.toml` must include `auth_token` for positive tests to pass.
- The `tmp_path` fixture from pytest provides temporary directories for test isolation.

## Security considerations

- **Test data isolation**: All test configs use temporary directories/files — no real config files are modified.
- **No secret leakage**: Test tokens are short-lived and not committed to version control.

## Rollback considerations

- Rolling back these tests means removing them; the original behavior would still be tested by the existing tests.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_config.py -v` — all new tests should pass.
- Run full EventBus suite: `uv run pytest tests/eventbus/ -q` (baseline: 169 passed + 1 pre-existing unrelated failure).

## Completion criteria

- [ ] `test_non_loopback_host_raises_value_error()` added
- [ ] `test_load_config_rejects_unknown_key()` added
- [ ] `test_load_config_rejects_wrong_type()` added
- [ ] `test_load_config_rejects_empty_auth_token()` added
- [ ] All new tests passing
- [ ] Full EventBus suite passes at baseline (no regressions)

## Out of scope

- Adding authorization tests (covered by `tests/eventbus/test_eventbus_auth.py`).
- Token rotation infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add loopback-bind regression test | Pending | — | — | |
| 2 | Add unknown-key rejection test | Pending | — | — | |
| 3 | Add wrong-type rejection test | Pending | — | — | |
| 4 | Add empty auth_token rejection test | Pending | — | — | |
| 5 | Validate tests pass | Pending | — | — | |

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
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: tests/eventbus/test_eventbus_config.py
