# Implementation: scripts/agent/services/config_reload.py (remove plugin_strict reload-diff branch)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 3, item 3)

Gap-filling note: matches the granularity of the existing `config_validators.py`
doc for this same plan step. Independent of the other step-3 siblings'
internal ordering (no import relationship), but conceptually should land
alongside `config_dataclasses_py_plugin_removal.md` since this file reads
`ctx.cfg.tool.plugin_strict`, a field that doc removes.

## Goal

`ConfigReloadService._detect_startup_only()` no longer checks `plugin_strict`
for reload-time changes.

## Scope

**In scope**: `scripts/agent/services/config_reload.py` — delete the
`plugin_strict` reload-diff block (lines 432-434) inside
`_detect_startup_only()`.

**Out of scope**: the `routing_drift_strict` block immediately after it (lines 435-437) — unrelated, unaffected; `config_dataclasses.py`'s field removal (sibling doc).

## Assumptions

1. Confirmed by direct read (2026-07-17): the block is:
   ```python
   v = _get_bool(new_cfg, "plugin_strict")
   if v is not None and v != ctx.cfg.tool.plugin_strict:
       changed.append("plugin_strict")
   ```
   at lines 432-434, immediately preceded by three `# REMOVED: ...` comment
   lines documenting a PRIOR removal (`use_memory_layer`), and immediately
   followed by the analogous `routing_drift_strict` block (lines 435-437).
2. **This repo has an established convention for this exact file**: a previously-removed reload-diff key (`use_memory_layer`) was left as commented-out `# REMOVED: <original line>` trace rather than being silently deleted with no record (lines 428-431, immediately above the plugin_strict block). Follow the same convention here — replace the plugin_strict block with equivalent `# REMOVED:` comments — rather than deleting it with no trace, for consistency with this file's own established style.
3. The local variable `v` is reused sequentially for each key check in this method (reassigned per-block, not scoped) — removing the plugin_strict block's `v = _get_bool(...)` line does not affect the `routing_drift_strict` block's own `v = _get_bool(new_cfg, "routing_drift_strict")` reassignment immediately after; the two blocks are independent despite sharing the variable name.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. Replace:
   ```python
   v = _get_bool(new_cfg, "plugin_strict")
   if v is not None and v != ctx.cfg.tool.plugin_strict:
       changed.append("plugin_strict")
   ```
   with (matching this file's own established convention immediately above, for the already-removed `use_memory_layer` key):
   ```python
   # REMOVED: plugin_strict tracking — key removed from schema
   # REMOVED: v = _get_bool(new_cfg, "plugin_strict")
   # REMOVED: if v is not None and v != ctx.cfg.tool.plugin_strict:
   # REMOVED:     changed.append("plugin_strict")
   ```

### Method

Direct replacement matching an established in-file precedent (comment-preserving removal), not a bare deletion.

### Details

- Do not touch the `routing_drift_strict` block or any other reload-diff check in `_detect_startup_only()`.
- Do not touch any other method in `config_reload.py`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No live plugin_strict reference remains (only `# REMOVED:` comment trace) | `grep -n "plugin_strict" scripts/agent/services/config_reload.py` | only comment-prefixed `# REMOVED:` lines match |
| Syntax/lint | `uv run ruff check scripts/agent/services/config_reload.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/services/config_reload.py` | no new errors |
| Targeted tests (expect failures until sibling config docs + test-removal doc also land) | `uv run pytest tests/test_config_reload.py tests/test_config_reload_classification.py -v` | pass once plugin-specific test cases are also removed |
