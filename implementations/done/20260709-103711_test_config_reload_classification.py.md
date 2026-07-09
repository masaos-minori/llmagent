# Implementation: H-1 — test_config_reload_classification.py patch rename

Source plan: `plans/20260709-094640_plan.md` (H-1, Implementation step 4).

## Goal

Update the two `patch.object(svc, "_apply_mcp_url_reload", ...)` call sites
so they target the renamed method, avoiding an `AttributeError` once
`implementations/20260709-103709_config_reload.py.md` lands.

## Scope

**Target**: `tests/test_config_reload_classification.py`, lines 90 and 99.

## Assumptions

1. These two `patch.object` calls exist solely to short-circuit the MCP
   classification path while testing unrelated `startup_only` field
   detection — verified by reading
   `test_apply_config_dict_use_memory_layer_in_startup_only` and
   `test_apply_config_dict_plugin_strict_in_startup_only`, neither of which
   asserts anything about the MCP-related outcome fields.

## Implementation

### Target file

`tests/test_config_reload_classification.py`

### Procedure

#### Step 1: Rename both patch targets

Line 90:
```python
with patch.object(svc, "_apply_mcp_url_reload", return_value=ConfigReloadOutcome()):
```
→
```python
with patch.object(svc, "_classify_mcp_server_changes", return_value=ConfigReloadOutcome()):
```

Line 99: identical change.

### Method

- Pure find-and-replace of the string `_apply_mcp_url_reload` →
  `_classify_mcp_server_changes` at these two exact lines only — do not
  touch anything else in the file.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Old name gone | `grep -n "_apply_mcp_url_reload" tests/test_config_reload_classification.py` | no matches |
| Test run | `uv run pytest tests/test_config_reload_classification.py -v` | all pass |
