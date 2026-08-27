## Goal

Remove the `tool_cache_ttl`/`tool_cache_max_size` TOML-to-`ToolConfig` loading
plumbing from `_build_tool_config()`, per `plans/20260827-121312_plan.md`'s
`REQ-002`.

## Scope

- In scope: `scripts/agent/config_builders.py::_build_tool_config()` — the two
  local-variable reads (verified at lines 277-278 as of 2026-08-27) and the two
  corresponding keyword arguments passed to `ToolConfig(...)` (verified at lines
  308-309).
- Out of scope: every other local variable / keyword argument in
  `_build_tool_config()`, and every other builder function in this file.

## Assumptions

- `REQ-001` (`config_dataclasses.py`) lands in the same commit — `ToolConfig` no
  longer accepts `tool_cache_ttl=`/`tool_cache_max_size=` keyword arguments after
  `REQ-001`, so this step's removal is required to avoid a `TypeError` at
  `ToolConfig(...)` construction.
- No other function in `config_builders.py` reads these two TOML keys — confirmed
  via `rg -n "tool_cache_ttl|tool_cache_max_size" scripts/agent/config_builders.py`
  showing only the four lines this step targets.

## Design decisions

- Remove the two local-variable assignments and the two keyword arguments as a
  single unit — leaving either half in place breaks the other (an orphaned local
  variable triggers a `ruff`/unused-variable failure if the keyword argument is
  removed first; an undefined-name error if the local is removed first).

## Alternatives considered

- Keep reading the TOML keys into local variables but stop passing them to
  `ToolConfig(...)`: rejected — leaves an unused local variable that `ruff check`
  (part of the standard validation sequence) will flag, and provides no value
  (the values are discarded).

## Implementation
### Target file
`scripts/agent/config_builders.py`

### Procedure
1. Re-run `rg -n "tool_cache_ttl|tool_cache_max_size"
   scripts/agent/config_builders.py` immediately before editing to confirm line
   numbers have not drifted since 2026-08-27.
2. Remove the two local-variable assignment lines in `_build_tool_config()`.
3. Remove the two corresponding keyword arguments from the `return
   ToolConfig(...)` call in the same function.
4. Run `ruff check scripts/agent/config_builders.py` to confirm no unused-name
   warning remains.

### Method
Direct text edit (Edit tool) — remove two lines and two keyword arguments.

### Details
Current text (verified 2026-08-27, lines 275-278):
```python
def _build_tool_config(cfg: dict[str, Any], system_prompt_tool: str) -> ToolConfig:
    """Build ToolConfig from a raw config dict and system prompt template."""
    tool_cache_ttl = _get_float_or_default(cfg, "tool_cache_ttl", 300)
    tool_cache_max_size = _get_int_or_default(cfg, "tool_cache_max_size", 200)
    serial_tool_calls = _get_bool_or_default(cfg, "serial_tool_calls", False)
```
Change to:
```python
def _build_tool_config(cfg: dict[str, Any], system_prompt_tool: str) -> ToolConfig:
    """Build ToolConfig from a raw config dict and system prompt template."""
    serial_tool_calls = _get_bool_or_default(cfg, "serial_tool_calls", False)
```

Current text (verified 2026-08-27, lines 307-309):
```python
    return ToolConfig(
        tool_cache_ttl=tool_cache_ttl,
        tool_cache_max_size=tool_cache_max_size,
        serial_tool_calls=serial_tool_calls,
```
Change to:
```python
    return ToolConfig(
        serial_tool_calls=serial_tool_calls,
```

## Compatibility considerations

- A TOML config file's `[tool]` section may still contain `tool_cache_ttl =` /
  `tool_cache_max_size =` keys; after this change they are silently ignored
  (never read) rather than erroring — the same "config key with no effect"
  concern raised in the source Plan's Reason for change, now fully resolved on
  both the read side (this file) and the schema side (`REQ-001`).

## Security considerations

- N/A: dead-code removal, no security-relevant behavior change.

## Rollback considerations

- Single-file revert via `git diff` / `git checkout -- scripts/agent/config_builders.py`.
- Must be rolled back together with `REQ-001`/`REQ-003` if any of the three is
  reverted, per Design.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/config_builders.py` | Static | `rg -n "tool_cache_ttl\|tool_cache_max_size" scripts/agent/config_builders.py` | No matches |
| `scripts/agent/config_builders.py` | Lint | `ruff check scripts/agent/config_builders.py` | No unused-variable warning |
| `tests/agent/` | Regression | `uv run pytest tests/agent/ -k "config_builders" -v` | No new failures |

## Completion criteria

- `rg -n "tool_cache_ttl|tool_cache_max_size" scripts/agent/config_builders.py`
  returns no matches.

## Out of scope

- Any other local variable / keyword argument in `_build_tool_config()` or any
  other builder function in this file.
- `config_dataclasses.py` (`REQ-001`, separate implementation procedure) and
  `config_validators.py` (`REQ-003`, separate implementation procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm current line numbers | Pending | — | — | |
| 2 | Remove local-variable assignments | Pending | — | — | |
| 3 | Remove keyword arguments | Pending | — | — | |
| 4 | Run `ruff check` | Pending | — | — | Coordinate with REQ-001/REQ-003 commits |

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/done/20260827_toolexecutor_cache_removal_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260827-121312_plan.md`
- **Source implementation procedure**: N/A: no prior implementation procedure
  targeted this file's `tool_cache_ttl`/`tool_cache_max_size` plumbing directly
  (the pre-existing superseded docs for this Plan's scope only covered
  `config_dataclasses.py`/`config_validators.py`)
- **Generated at**: 20260827-134500
- **Related target files**: `scripts/agent/config_builders.py`
