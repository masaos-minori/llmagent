# Implementation: remove plugin validators from `scripts/agent/services/config_validators.py`

Source plan: `plans/20260717-123416_plan.md` ("Remove plugin subsystem completely"), Implementation
step 3.

## Goal

Remove the two plugin-config validator functions `validate_tool_plugin_tool_override()` and
`validate_tool_plugin_strict()` from `scripts/agent/services/config_validators.py`, since the
`ToolConfig` fields they validate (`plugin_tool_override`, `plugin_strict`) are being deleted from
`scripts/agent/config_dataclasses.py` in a sibling (already covered/skipped) implementation item.

## Scope

**In scope**
- `scripts/agent/services/config_validators.py`: delete `validate_tool_plugin_tool_override(cfg:
  ToolConfig) -> None` (current lines 103-107) and `validate_tool_plugin_strict(cfg: ToolConfig) ->
  None` (current lines 110-114), including the blank line separating them from neighboring functions.

**Out of scope**
- `scripts/agent/config_dataclasses.py`'s own edit (removing the `plugin_tool_override`/`plugin_strict`
  fields and the `_v_tool_ps`/`_v_tool_pto` import aliases at lines 89/92/202/206/213-214) — that is a
  separate item already covered/skipped in this batch (matches existing
  `implementations/done/*config_dataclasses.py*` docs). This doc only covers the validator-function
  removal in `config_validators.py` itself.
- Any other validator function in this file (`validate_llm_*`, `validate_rag_*`, `validate_tool_dedup_max_repeats`,
  `validate_tool_cycle_detect_window`, `validate_tool_error_max_consecutive`, `validate_tool_cache_max_size`,
  `validate_tool_error_retry_max`, `validate_memory_*`, `validate_approval_risk_rules`,
  `validate_tool_safety_tiers`) — all unrelated to plugins, untouched.

## Assumptions

1. `config_dataclasses.py` imports these two functions under aliases `_v_tool_ps` (for
   `validate_tool_plugin_strict`) and `_v_tool_pto` (for `validate_tool_plugin_tool_override`) — confirmed
   by direct read of `scripts/agent/config_dataclasses.py`: line 89 (`validate_tool_plugin_strict as
   _v_tool_ps`), line 92 (`validate_tool_plugin_tool_override as _v_tool_pto`), and called at lines 213
   (`_v_tool_pto(self)`) / 214 (`_v_tool_ps(self)`) inside `ToolConfig.__post_init__`. Since that
   caller-side edit is a separate already-covered item, this item's own removal must not land *before*
   that one in a way that breaks the import at HEAD — per the plan's Design section ("delete consumers
   first"), the `config_dataclasses.py` import removal should land in the same commit as (or before)
   this file's function removal, or both in one commit.
2. No other module imports `validate_tool_plugin_tool_override` or `validate_tool_plugin_strict`
   directly — confirmed via `rg -n "validate_tool_plugin_tool_override\|validate_tool_plugin_strict"
   scripts/`, which returns only `config_validators.py` (definition) and `config_dataclasses.py`
   (import/call site).
3. `LLM_TEMPERATURE_MAX` (module-level constant, line 24) and all other validator functions are
   unrelated and must remain untouched.

## Implementation

### Target file

`scripts/agent/services/config_validators.py` (187 lines currently).

### Procedure

1. Confirm via `rg -n "plugin" scripts/agent/services/config_validators.py` that the only matches are
   the two target functions (`validate_tool_plugin_tool_override` at line 103, `validate_tool_plugin_strict`
   at line 110) and their docstring/body references to `cfg.plugin_tool_override` / `cfg.plugin_strict`.
2. Delete the function `validate_tool_plugin_tool_override` (current lines 103-107):
   ```
   def validate_tool_plugin_tool_override(cfg: ToolConfig) -> None: ...
   ```
   (signature only, shown for identification — not to be reproduced as production code in the commit
   message).
3. Delete the function `validate_tool_plugin_strict` (current lines 110-114):
   ```
   def validate_tool_plugin_strict(cfg: ToolConfig) -> None: ...
   ```
4. Remove the now-redundant blank line so exactly one blank line separates
   `validate_rag_refiner_max_chars_per_chunk` (ends at line 100) from `validate_tool_dedup_max_repeats`
   (currently starting at line 117) — ruff format will normalize spacing regardless, so this is a
   cosmetic-only concern.
5. Re-run `rg -n "plugin" scripts/agent/services/config_validators.py` to confirm 0 matches remain.

### Method

Straight deletion of two small, self-contained functions — no signature changes to any surviving
function, no new logic. `ToolConfig`'s `TYPE_CHECKING`-only import (line 20) stays, since other
`ToolConfig`-typed validators in this file remain.

### Details

- Current exact content of both functions being removed (for identification only):
  - `validate_tool_plugin_tool_override(cfg)`: raises `ValueError` if
    `not isinstance(cfg.plugin_tool_override, bool)`.
  - `validate_tool_plugin_strict(cfg)`: raises `ValueError` if `not isinstance(cfg.plugin_strict, bool)`.
- Both functions take a single positional `cfg: ToolConfig` argument and return `None`, matching the
  calling convention of every other validator in this module (`validate_llm_context_char_limit(cfg)`,
  etc.) — no other validator's signature needs to change as a result of this removal.
- After removal, `ToolConfig`'s surviving validators in this file (used by `config_dataclasses.py`) are:
  `validate_tool_dedup_max_repeats`, `validate_tool_cycle_detect_window`,
  `validate_tool_error_max_consecutive`, `validate_tool_cache_max_size`, `validate_tool_error_retry_max`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No remaining plugin validators | `rg -n "validate_tool_plugin_tool_override\|validate_tool_plugin_strict" scripts/` | 0 matches |
| No remaining plugin config keys anywhere | `rg -n "plugin_strict\|plugin_tool_override" scripts/ config/` | 0 matches (once sibling `config_dataclasses.py`/`config_builders.py`/`config_reload.py`/`production_config_validator.py`/`agent.toml` items also land) |
| Lint | `uv run ruff check scripts/agent/services/config_validators.py` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Targeted tests | `uv run pytest tests/test_config_dataclasses.py tests/test_config_builders.py -v` | all pass, no plugin-specific assertions remain |
| Full suite | `uv run pytest -v` | all pass |
