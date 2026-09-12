# Implementation: tests/agent/test_tool_policy_comprehensive.py

## Goal

Add 3 missing configuration keys (`tool_definitions_strict=True`, `routing_drift_strict=True`, and a non-empty `allowed_tools`) to `_cfg()`'s `defaults` dict so that this file's tests can pass after cfgval001's fix lands.

## Scope

- Modify `tests/agent/test_tool_policy_comprehensive.py` only.
- Add `tool_definitions_strict=True` to `_cfg()`'s `defaults` dict.
- Add `routing_drift_strict=True` to `_cfg()`'s `defaults` dict.
- Replace `allowed_tools=[]` with a non-empty representative list (e.g., `["shell_execute"]`).
- Confirm each of this file's individual tests still passes with these 3 values fixed.

## Assumptions

- cfgval001's fix (removal of 12 obsolete legacy flat keys) will land separately and is assumed to have been applied before this fix is validated against zero failures.
- The `ProductionConfigValidator`'s strict-mode/allowlist requirements are intentional and confirmed by cfgval001's Background section.
- No test currently depends on the old permissive defaults.

## Design decisions

- Since this is a Path A task (affects ≤ 3 files, no public/runtime interface changes, no database schema changes), the design is straightforward: add the 3 missing keys directly to the existing `defaults` dict in `_cfg()`.
- Use `["shell_execute"]` as the representative value for `allowed_tools`, matching `test_agent_negative_paths.py`'s pattern.

## Alternatives considered

- **Keep both liveness methods**: Would preserve backward compatibility but perpetuates the inconsistency bug where callers cannot know which liveness model applies.
- **Deprecate rather than remove**: Would allow gradual migration but adds maintenance burden for deprecated methods.

## Implementation

### Target file

`tests/agent/test_tool_policy_comprehensive.py`

### Procedure

1. Read `tests/agent/test_agent_negative_paths.py`'s `_cfg()` to confirm the pattern for setting `tool_definitions_strict`, `routing_drift_strict`, and `allowed_tools`.
2. Add `tool_definitions_strict=True` to `_cfg()`'s `defaults` dict.
3. Add `routing_drift_strict=True` to `_cfg()`'s `defaults` dict.
4. Replace `allowed_tools=[]` with `allowed_tools=["shell_execute"]` in `_cfg()`'s `defaults` dict.
5. Run `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q` to verify all tests pass with the new defaults.

### Method

```python
# Step 1: Read test_agent_negative_paths.py's _cfg() to confirm the pattern
# In test_agent_negative_paths.py (around line 35-63):
#     def _cfg(**overrides: Any) -> AgentConfig:
#         return AgentConfig(
#             ...
#             tool_definitions_strict=True,
#             routing_drift_strict=True,
#             allowed_tools=["shell_execute"],
#             ...
#         )

# Step 2-4: Update _cfg()'s defaults dict in test_tool_policy_comprehensive.py
# In test_tool_policy_comprehensive.py (around line 35-63):
# Before:
#     def _cfg(**overrides: Any) -> AgentConfig:
#         return AgentConfig(
#             ...
#             # Missing: tool_definitions_strict, routing_drift_strict
#             allowed_tools=[],
#             ...
#         )
# After:
#     def _cfg(**overrides: Any) -> AgentConfig:
#         return AgentConfig(
#             ...
#             tool_definitions_strict=True,
#             routing_drift_strict=True,
#             allowed_tools=["shell_execute"],
#             ...
#         )

# Step 5: Verify all tests pass
# Command: uv run pytest tests/agent/test_tool_policy_comprehensive.py -q
# Expected: Zero failures citing tool_definitions_strict, routing_drift_strict, or allowed_tools=[]
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- Need to carefully reconcile the behavioral differences between the old and new implementations — the plan explicitly notes these differences must be reconciled during migration.
- The SIGINT handler logic moved to `ShutdownCoordinator` must be verified to work correctly with the new architecture.

## Compatibility considerations

- **Breaking change** for consumers of `get_process_info()` that expect only `pid`, `pgid`, and `running` fields. New fields (`last_exit_code`, `runtime_seconds`) will be present in the output.
- **No breaking change** for existing callers of `verify_running()` — the method signature remains compatible (new parameter has default value).

## Security considerations

- No new security surface introduced. Adding component delegation does not introduce new attack vectors.
- The SIGINT handling logic moved to `ShutdownCoordinator` maintains the same security properties.

## Rollback considerations

- Revert the component initialization and delegation updates.
- If the new fields cause unexpected behavior, remove them and investigate further.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| Test execution | Unit test | `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q` | Zero failures citing `tool_definitions_strict`, `routing_drift_strict`, or `allowed_tools=[]` |

## Completion criteria

- [ ] `tool_definitions_strict=True` added to `_cfg()`'s `defaults` dict.
- [ ] `routing_drift_strict=True` added to `_cfg()`'s `defaults` dict.
- [ ] `allowed_tools=["shell_execute"]` replaces `allowed_tools=[]` in `_cfg()`'s `defaults` dict.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/shared/production_config_validator.py` — handled by a separate implementation procedure document.
- Modifying `tests/agent/test_agent_negative_paths.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read test_agent_negative_paths.py's _cfg() | Completed | — | — | NOTE: confirmed pattern matches; added tool_definitions_strict=True, routing_drift_strict=True, allowed_tools=["shell_execute"] |
| 2 | Add tool_definitions_strict=True | Completed | — | — | Applied: added to defaults dict |
| 3 | Add routing_drift_strict=True | Completed | — | — | Applied: added to defaults dict |
| 4 | Replace allowed_tools=[] | Completed | — | — | Applied: replaced with ["shell_execute"]; also fixed test_none_values_in_args by adding allowed_tools=["write_file"] override |
| 5 | Run validation sequence (rules/toolchain.md) | Completed | — | — | ruff/mypy/bandit clean; all 38 tests pass |

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
- **Requirement ID**: REQ-001 through REQ-004
- **Source issue**: issues/20260909-183320_toolpolicy01_test-tool-policy-comprehensive-cfg-missing-strict-mode-keys.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-001221_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-010045
- **Related target files**: tests/agent/test_tool_policy_comprehensive.py
