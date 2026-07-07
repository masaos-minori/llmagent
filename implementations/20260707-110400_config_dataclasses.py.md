## Goal
Remove `workflow_mode` and `workflow_require_approval` fields from `AgentConfig`, eliminating `_validate_workflow_mode()` so the dataclass enforces no workflow mode — workflow is always required.

## Scope
**In**: Remove `workflow_mode: str`, `workflow_require_approval: bool`, `_validate_workflow_mode()`, and the `__post_init__` call to it in `scripts/agent/config_dataclasses.py`.
**Out**: Any other field changes; `_validate_cross_field()` and its sub-methods remain untouched.

## Assumptions
- `workflow_mode` is at line 528, `workflow_require_approval` at line 530, `_validate_workflow_mode` at line 536.
- `__post_init__` calls `self._validate_workflow_mode()` first — remove only that call; leave `self._validate_cross_field()`.
- No other field in `AgentConfig` references `workflow_mode` or `workflow_require_approval`.

## Implementation

**Target file**: `scripts/agent/config_dataclasses.py`

**Procedure**:
1. Remove line 528: `workflow_mode: str = "auto"`
2. Remove line 530: `workflow_require_approval: bool = False`
3. Remove line 533: `self._validate_workflow_mode()` from `__post_init__`
4. Remove lines 536–540: `_validate_workflow_mode()` method entirely
5. Update class docstring: remove `workflow_mode` and `workflow_require_approval` descriptions

**Method**: Surgical line deletion. No refactoring of surrounding code.

**Details**:
```python
# REMOVE these lines:
workflow_mode: str = "auto"
workflow_require_approval: bool = False

# In __post_init__, REMOVE:
self._validate_workflow_mode()

# REMOVE entire method:
def _validate_workflow_mode(self) -> None:
    valid = {"auto", "required", "disabled"}
    if self.workflow_mode not in valid:
        raise ValueError(...)
```

**Unknown key rejection** (add to `_validate_cross_field` or a new validator):
```python
# This is handled in config_builders.py, not here.
```

## Validation plan
- `uv run mypy scripts/agent/config_dataclasses.py` — no new errors
- `uv run pytest tests/test_config_dataclasses.py -x -q` — workflow_mode tests removed/passing
- `rg "workflow_mode\|workflow_require_approval" scripts/agent/config_dataclasses.py` → 0 matches

---
*Plan: 20260707-095938 (req01) Phase 1 / Plan: 20260707-095942 (req05) Phase 2*
