## Goal
- Add WARNING log when Event Bus binds to public address without authentication
- Add startup guard reference in system overview docs

## Findings

### Current state
- `scripts/eventbus/config.py:L22-68`: `_is_public_host()` and `allow_public_bind` validation exist — fail-fast on public bind
- `scripts/eventbus/app.py:L77`: startup log only shows port (now shows host:port after previous change) — no "no authentication" warning
- `docs/06_eventbus_05_configuration_deploy_and_operations.md:L27,46-61`: startup guard documented in config docs
- `docs/06_eventbus_01_system-overview.md:L30-34`: security model mentions "no authentication or ACL" but doesn't reference the startup guard
- `tests/test_eventbus_startup.py:L15-28,75,88`: `_is_public_host()` and public bind fail-fast tests exist

### Gap 1: Startup log missing "no authentication" warning
When Event Bus binds to a public address (0.0.0.0, ::), the startup log should emit a WARNING about lack of authentication. Currently no such warning exists.

### Gap 2: System overview doesn't reference startup guard
`06_eventbus_01_system-overview.md` mentions "no authentication or ACL" but doesn't reference the startup guard that prevents accidental public binding.

## Changes

### Gap 1: Add WARNING log for public bind without auth
- `scripts/eventbus/app.py:L77`: Added conditional WARNING log when Event Bus binds to public address without authentication
- Added `_is_public_host` import from `eventbus.config`

### Gap 2: Add startup guard reference in system overview
- `docs/06_eventbus_01_system-overview.md:L34`: Added bullet point describing the startup guard that rejects public/wildcard address binding unless `allow_public_bind=true`
