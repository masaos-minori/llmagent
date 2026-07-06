# Implementation: agent/config_dataclasses.py — Add routing_drift_strict field to ToolConfig

## Goal

Add `routing_drift_strict: bool = False` to `ToolConfig` so that startup routing drift validation can optionally be treated as fatal.

## Scope

**In**: Add one boolean field to `ToolConfig` dataclass. Update `_sync_services()` in `config_reload.py` if needed.

**Out**: Implementing the strict mode behavior itself (done in `repl_health.py` and `startup.py`).

## Assumptions

1. `ToolConfig` is in `scripts/agent/config_dataclasses.py`.
2. The field default is `False` — new environments do not fail on drift by default.
3. Config TOML key: `routing_drift_strict` in `[tool]` section.
4. `config_reload.py` hot-reload handling: this is a startup-only field (cannot be applied without restart) — do NOT add to `_sync_services()`.

## Implementation

### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. Find `ToolConfig` dataclass definition.
2. Add `routing_drift_strict: bool = False` field alongside existing bool fields.

### Method

```python
@dataclass
class ToolConfig:
    ...
    tool_definitions_strict: bool = False
    routing_drift_strict: bool = False  # NEW: treat routing drift as fatal at startup
    ...
```

### Details

- Place after `tool_definitions_strict` for logical grouping.
- No `__post_init__` validation needed — it's a simple bool.
- `config_reload.py:_detect_startup_only()` should detect changes to `routing_drift_strict` (same as `tool_definitions_strict`).

## Validation plan

- `uv run pytest tests/ -v -k "config_dataclasses or tool_config"` — all pass.
- `mypy scripts/agent/config_dataclasses.py` — no new errors.
- `ruff check scripts/agent/config_dataclasses.py` — 0 errors.
