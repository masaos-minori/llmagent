# Implementation: config_reload.py — Remove `deferred` field

## Goal

Remove the `deferred` field from `ConfigReloadOutcome` dataclass. The field is dead code since `auth_token`/`startup_mode` now classify as `needs_restart`.

## Scope

- `scripts/agent/services/config_reload.py` only.
- Remove one line.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

Delete the `deferred: list[str] = field(default_factory=list)` line from `ConfigReloadOutcome`.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Field removed | `grep -n "deferred" scripts/agent/services/config_reload.py` | no matches |
| Lint | `uv run ruff check scripts/agent/services/config_reload.py` | 0 errors |
