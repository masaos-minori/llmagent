## Goal
Remove all `workflow_mode` and `workflow_require_approval` test cases from the test suite; replace removed tests with new tests asserting these fields are absent and config rejection works.

## Scope
**In**: `tests/test_config_dataclasses.py` (lines 195–204), `tests/test_config_reload_classification.py` (all `workflow_mode`/`workflow_require_approval` parametrize entries), `tests/test_agent_cmd_context.py` (workflow_mode display tests, lines ~452–498), `tests/test_agent_cmd_config.py` (line ~37 `ctx.cfg.workflow_mode = ""`), `tests/test_workflow_execution_policy.py` (delete entire file).
**Out**: Tests for other config fields; test infrastructure (fixtures, conftest).

## Assumptions
- All removed test functions test behavior that no longer exists after req01.
- New tests are added to verify: (a) config with `workflow_mode` key raises, (b) `AgentConfig` has no `workflow_mode` attribute.
- `tests/test_workflow_execution_policy.py` is deleted entirely (see deletion doc).

## Implementation

**Target files**: Multiple test files (listed above)

**Procedure**:
1. `tests/test_config_dataclasses.py`:
   - Remove `test_workflow_mode_default`, `test_invalid_workflow_mode_raises`, `test_all_valid_workflow_modes` functions
   - Add: `test_agent_config_has_no_workflow_mode_field` — `assert not hasattr(AgentConfig(), "workflow_mode")`
   - Add: `test_agent_config_has_no_workflow_require_approval_field`

2. `tests/test_config_reload_classification.py`:
   - Remove parametrize entries `("workflow_mode", "required")` and `("workflow_require_approval", True)` from the parametrized list
   - Remove `test_apply_config_dict_workflow_mode_in_startup_only` function
   - Remove `test_apply_config_dict_workflow_require_approval_in_startup_only` function
   - Remove `test_apply_config_dict_unchanged_workflow_mode_not_in_startup_only` function
   - Remove any fixture setup lines `ctx.cfg.workflow_mode = "auto"`, `ctx.cfg.workflow_require_approval = False`

3. `tests/test_agent_cmd_context.py`:
   - Remove `test_cmd_context_shows_workflow_mode`, `test_collect_context_state_workflow_mode` and related tests
   - Remove any `ctx.cfg.workflow_mode = ...` setup lines

4. `tests/test_agent_cmd_config.py`:
   - Fix line ~37: remove `ctx.cfg.workflow_mode = ""` (attribute no longer exists)

5. Add to `tests/test_config_builders.py` (or new file):
   - `test_config_with_workflow_mode_key_raises_config_load_error`
   - `test_config_with_workflow_require_approval_key_raises_config_load_error`

**Method**: Targeted function/line deletion across multiple files. Run pytest after each file edit.

**Details**:
- Use `grep -n "workflow_mode\|workflow_require_approval" tests/*.py` to find all occurrences before starting.
- Do not remove any test infrastructure (fixtures, conftest, imports) unless solely used by the deleted tests.

## Validation plan
- `uv run pytest tests/ -x -q` — all pass
- `rg "workflow_mode\|workflow_require_approval" tests/ | grep -v "test_check_no_compat\|test_workflow_execution_policy"` → 0

---
*Plan: 20260707-095938 (req01) Phase 5*
