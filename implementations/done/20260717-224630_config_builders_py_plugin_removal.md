# Implementation: scripts/agent/config_builders.py (remove plugin field reads)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 3, item 2)

Gap-filling note: matches the granularity of the existing `config_validators.py`
doc for this same plan step. Should land alongside its step-3 siblings
(`config_dataclasses.py`, `config_reload.py`, `production_config_validator.py`,
`config/agent.toml`); recommended after `config_dataclasses_py_plugin_removal.md`
so `ToolConfig(...)`'s constructor no longer has `plugin_tool_override`/
`plugin_strict` parameters to pass by the time this file stops passing them.

## Goal

The `ToolConfig(...)` construction in `config_builders.py` no longer reads or
passes `plugin_tool_override`/`plugin_strict`.

## Scope

**In scope**: `scripts/agent/config_builders.py` — delete the two kwarg lines
`plugin_tool_override=bool(cfg.get("plugin_tool_override", False)),` and
`plugin_strict=bool(cfg.get("plugin_strict", os.getenv("CI") is not None)),`
(lines 189-190) from the `ToolConfig(...)` call.

**Out of scope**: `config_dataclasses.py`'s field definitions (sibling doc);
`config/agent.toml`'s keys (sibling doc).

## Assumptions

1. Confirmed by direct read (2026-07-17): both lines sit at the end of a `ToolConfig(...)` constructor call, immediately after `allowed_tools=list(cfg.get("allowed_tools", [])),` (line 188) and immediately before the call's closing `)` (line 191).
2. `os.getenv("CI")` (used only in the `plugin_strict` default) — confirm whether `os` is still used elsewhere in this file before considering removing the `import os` line; do not remove the import speculatively.
3. This function's return type (`ToolConfig`) and all its OTHER kwargs are unaffected — this is a pure two-line subtraction from one constructor call.

## Implementation

### Target file

`scripts/agent/config_builders.py`

### Procedure

1. Delete:
   ```python
   plugin_tool_override=bool(cfg.get("plugin_tool_override", False)),
   plugin_strict=bool(cfg.get("plugin_strict", os.getenv("CI") is not None)),
   ```
   leaving `allowed_tools=list(cfg.get("allowed_tools", [])),` as the last kwarg before the closing `)`.
2. Run `uv run ruff check scripts/agent/config_builders.py --select F401` to check whether `import os` becomes unused — remove it ONLY if ruff flags it (this file may use `os` elsewhere for other env-var reads; do not assume).

### Method

Direct deletion of two kwarg lines from one constructor call.

### Details

- Do not touch any other `_build_*_config()` function in this file — only the `ToolConfig(...)` call is affected.
- This edit must land no earlier than `config_dataclasses_py_plugin_removal.md` conceptually (both fields must still exist on `ToolConfig` or be removed together) — in practice either order works within the same commit-sized unit since Python doesn't type-check kwargs against a dataclass at import time, but running the two together avoids a transient state where a valid field is dropped from the constructor while still declared (harmless) or vice versa (a `TypeError: unexpected keyword argument` if this file still passes a field `config_dataclasses.py` already removed) — so land `config_dataclasses.py`'s doc first, or in the same commit.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin references remain in this file | `grep -n "plugin" scripts/agent/config_builders.py` | 0 matches |
| Syntax/lint | `uv run ruff check scripts/agent/config_builders.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/config_builders.py` | no new errors |
| Targeted tests (expect failures until sibling config docs + test-removal doc also land) | `uv run pytest tests/test_config_builders.py -v` | pass once plugin-specific test cases are also removed |
