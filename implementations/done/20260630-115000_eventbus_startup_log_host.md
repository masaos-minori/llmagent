## Goal
- Add host to startup log to show effective bind address (host:port) instead of port only

## Findings

### Current state
- `scripts/eventbus/app.py:L77`: startup log shows only port — `"eventbus starting on port=%d"`
- `scripts/eventbus/config.py:L44,96`: `host` field exists in EventBusConfig with TOML support
- `docs/06_eventbus_06_reference_api.md:L35,36`: `host` and `allow_public_bind` fields documented in EventBusConfig
- `tests/test_eventbus_config.py:L76`: `test_valid_config_with_host_field` tests host field

### Gap
Startup log does not show the bind address (host), only the port. Users cannot verify which address Event Bus is bound to without checking config separately.

## Changes
- `scripts/eventbus/app.py:L77`: Changed `"eventbus starting on port=%d"` to `"eventbus starting on %s:%d"` with `app.state.config.host` and `app.state.config.port` arguments
