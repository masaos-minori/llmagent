# Implementation: cmd_config.py — Remove `[DEFER]` rendering branches

## Goal

Remove all `result.deferred` / `[DEFER]` / "deferred (next connection)" output handling from `_cmd_reload()`.

## Scope

- `scripts/agent/commands/cmd_config.py` only.
- Remove the `not result.deferred` from the first `if`, the entire `elif result.deferred:` branch, and the `if result.deferred:` `[DEFER]` rendering block.

## Implementation

### Target file

`scripts/agent/commands/cmd_config.py`

### Procedure

1. Change `if not result.applied and not result.needs_restart and not result.deferred:` to `if not result.applied and not result.needs_restart:`.
2. Remove the entire `elif result.deferred:` branch (the "Config reloaded — some changes deferred to next connection" block).
3. Remove the entire `if result.deferred:` block (the `[DEFER]` item rendering).
4. Remove `deferred=%s` and `result.deferred` from the trailing `logger.info()` call.

### Method

In-place edits.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Rendering removed | `grep -n "DEFER\|deferred" scripts/agent/commands/cmd_config.py` | no matches |
| Lint | `uv run ruff check scripts/agent/commands/cmd_config.py` | 0 errors |
