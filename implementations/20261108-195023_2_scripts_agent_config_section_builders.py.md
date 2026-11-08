## Goal
Wire `tool_unavailable_repeat_max_repeats` (new) through `_build_tool_config` so a raw config key reaches `ToolConfig` (REQ-001, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit
- One keyword argument in `_build_tool_config`.

## Assumptions
- The existing `tool_empty_result_max_repeats` is not wired in this builder (stays 0); that pre-existing condition is out of scope (Plan Risks) and is not changed here.
- `_get_or_default(cfg, key, _get_int, 0)` returns 0 when the key is absent, so absent keys load unchanged.
- Depends on the `config_dataclasses.py` procedure (seq 1) having added the field.

## Design decisions
- Use the sibling pattern `_get_or_default(cfg, "…", _get_int, 0)` next to `tool_error_retry_max`.

## Alternatives considered
N/A: follows the existing builder pattern.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`

### Procedure
1. In `_build_tool_config`, after the `tool_error_retry_max=` argument, add `tool_unavailable_repeat_max_repeats=_get_or_default(cfg, "tool_unavailable_repeat_max_repeats", _get_int, 0),`.

### Method
Single added keyword argument in the `_build_model(ToolConfig, ...)` call; keep argument order otherwise unchanged.

### Details
- Verified by reading: the call already enumerates sibling knobs (`tool_dedup_max_repeats`, `tool_cycle_detect_window`, `tool_error_max_consecutive`, `tool_error_retry_max`).
- A non-int value is handled by `_get_int` as for siblings.

## Compatibility considerations
Additive; absent key yields 0 (REQ-006).

## Security considerations
N/A: a numeric threshold.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_loop_guard.py tests/agent/services/test_config_reload.py -q`

## Completion criteria
- `build_agent_config({... "tool_unavailable_repeat_max_repeats": 2})` yields `cfg.tool.tool_unavailable_repeat_max_repeats == 2`; absent key yields 0.

## Out of Scope
Wiring `tool_empty_result_max_repeats`; validators; registry entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the builder argument | Pending | — | — |  |
| 2 | Builder-level tests (done by the `test_tool_loop_guard.py` procedure) | Pending | — | — | Uses `_cfg(tool_unavailable_repeat_max_repeats=…)` |
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
- **Requirement ID**: `REQ-001` (knob reaches `ToolConfig`), `REQ-006` (absent key loads as 0)
- **Source issue**: `issues/20261107-191650_loopguard02_unavailable-repeat-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_loopguard02_unavailable-repeat-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195023
- **Related target files**: `scripts/agent/config_section_builders.py`
