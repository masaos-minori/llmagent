## Goal
Give `ToolConfig` its own unavailable-repeat threshold field (REQ-001: new default-0 knob; REQ-006: additive-only).

## Scope
**Release unit**: N/A: not part of a release unit
- Add one dataclass field. No behavior change by itself; the guard is repointed in the `tool_loop_guard.py` procedure.

## Assumptions
- `ToolConfig` is built with keyword args only (`_build_tool_config` uses `_build_model`), so a defaulted field is additive.
- No `CONFIG_FIELD_REGISTRY` entry or validator is needed; siblings `tool_dedup_max_repeats` and `tool_cycle_detect_window` have none (Plan Assumptions).
- Overlap check (`check_plan_target_overlaps.py`): no finding names this Plan.

## Design decisions
- Place the field directly after `tool_empty_result_max_repeats` with the same comment convention (`> 0` enables, `<= 0` disables, default 0).

## Alternatives considered
N/A: a single defaulted int field; the alternative of reusing the existing knob is the defect being fixed.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. In `class ToolConfig`, immediately after the `tool_empty_result_max_repeats: int = 0` line, add `tool_unavailable_repeat_max_repeats: int = 0` (new) with a preceding comment.

### Method
Insert the comment `# Max consecutive server-unavailable hints for one server within a turn; > 0 enables unavailable-repeat detection, <= 0 disables it. Default 0 (disabled). Independent of tool_empty_result_max_repeats.` and the field.

### Details
- Do not touch `tool_empty_result_max_repeats` (REQ-003).
- `tests/agent/test_tool_loop_guard.py::TestReportEffectiveState::test_defaults_unchanged` pins other defaults; it needs no edit.

## Compatibility considerations
Additive; `ToolConfig()` and configs without the key load unchanged (REQ-006). No serialized-config version exists.

## Security considerations
N/A: a numeric threshold, no trust boundary.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_loop_guard.py tests/agent/services/test_config_reload.py -q`
- `uv run python tools/check_module_size.py`

## Completion criteria
- `ToolConfig().tool_unavailable_repeat_max_repeats == 0`.
- No other `ToolConfig` default changed.

## Out of Scope
Wiring in the builder, guard repointing, tests, docs, any startup-diagnostic change (Plan UNK-01 deferred).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the field to `ToolConfig` | Pending | — | — |  |
| 2 | Cover the default in tests (done by the `test_tool_loop_guard.py` procedure) | Pending | — | — | No test edit in this file's procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001` (new default-0 knob), `REQ-006` (additive-only)
- **Source issue**: `issues/20261107-191650_loopguard02_unavailable-repeat-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_loopguard02_unavailable-repeat-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195023
- **Related target files**: `scripts/agent/config_dataclasses.py`
