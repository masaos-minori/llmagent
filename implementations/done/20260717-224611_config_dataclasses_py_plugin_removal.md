# Implementation: scripts/agent/config_dataclasses.py (remove plugin_tool_override/plugin_strict fields)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 3, item 1)

Gap-filling note: matches the granularity of the existing `config_validators.py`
doc for this same plan step (already done). Order relative to other step-3
docs (`config_builders.py`, `config_reload.py`, `production_config_validator.py`,
`config/agent.toml`) does not matter among themselves (no file in step 3
imports another), but ideally lands in the same commit-sized unit as those
siblings, and can run independently of steps 1/2/4/5 (this step only touches
config plumbing, no plugin-runtime files).

## Goal

`ToolConfig` no longer has `plugin_tool_override`/`plugin_strict` fields or
validator imports for them.

## Scope

**In scope**
- `scripts/agent/config_dataclasses.py`: delete the two `from agent.services.config_validators import (validate_tool_plugin_strict as _v_tool_ps,)` / `(validate_tool_plugin_tool_override as _v_tool_pto,)` import blocks (lines 85-93), the `plugin_tool_override: bool = False` and `plugin_strict: bool = False` fields with their comments (lines 198-205), and the `_v_tool_pto(self)` / `_v_tool_ps(self)` calls in `ToolConfig.__post_init__` (lines 213-214).

**Out of scope**
- `agent/services/config_validators.py`'s `validate_tool_plugin_tool_override()`/`validate_tool_plugin_strict()` function bodies — already removed (existing `config_validators.py` doc, done).
- `config_builders.py`'s field reads, `config_reload.py`'s reload-diff branch, `production_config_validator.py`'s required-keys entry, `config/agent.toml`'s keys — sibling docs in this same step.

## Assumptions

1. Confirmed by direct read (2026-07-17): the two validator imports are separate `from agent.services.config_validators import (...)` blocks at lines 85-90 and 91-93 (this file's style gives each validator its own import statement); the two fields are at lines 201 and 205 inside `ToolConfig`, each preceded by a 1-3 line comment; the two `__post_init__` calls are at lines 213-214, the last two lines of that method.
2. The referenced functions `validate_tool_plugin_tool_override`/`validate_tool_plugin_strict` no longer exist in `agent/services/config_validators.py` (removed by the already-completed sibling doc) — re-verify this is still true at implementation time (if it somehow isn't, that doc may need re-checking before this one proceeds, since this file's imports would otherwise become a genuine `ImportError`).
3. No other `ToolConfig` field or method references `plugin_tool_override`/`plugin_strict` — confirmed via `grep -n "plugin" scripts/agent/config_dataclasses.py` returning exactly the 5 line-groups above.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. Delete the import block:
   ```python
   from agent.services.config_validators import (
       validate_tool_plugin_strict as _v_tool_ps,
   )
   from agent.services.config_validators import (
       validate_tool_plugin_tool_override as _v_tool_pto,
   )
   ```
2. Delete the two fields and their comments:
   ```python
   # Tools that shadow MCP tool names are rejected by default.
   # true = allow shadowing with warning; false = reject (default)
   # Recommended for production: False (fail-closed)
   plugin_tool_override: bool = False
   # Fail startup on first plugin import error.
   # true = fail-fast (CI/production); false = fail-open (log and continue, dev)
   # Recommended for production: True
   plugin_strict: bool = False
   ```
3. Delete the two `__post_init__` calls: `_v_tool_pto(self)` and `_v_tool_ps(self)`, leaving `_v_tool_erm(self)` as the last statement in `ToolConfig.__post_init__`.

### Method

Direct deletions only.

### Details

- Confirm at implementation time whether `validate_tool_plugin_tool_override`/`validate_tool_plugin_strict` have actually been removed from `config_validators.py` already (per the `implementations/done/` doc for that file) — if this doc is somehow implemented before that one, importing a now-nonexistent function would be a genuine `ImportError`; the recommended order is config_validators.py first (already done), then this doc.
- Do not touch any other `ToolConfig` field.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin references remain in this file | `grep -n "plugin" scripts/agent/config_dataclasses.py` | 0 matches |
| Syntax/lint | `uv run ruff check scripts/agent/config_dataclasses.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/config_dataclasses.py` | no new errors |
| Targeted tests (expect failures until sibling config docs + test-removal doc also land) | `uv run pytest tests/test_config_dataclasses.py -v` | pass once plugin-specific test cases are also removed |
