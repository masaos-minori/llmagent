## Goal
Prove the two guards toggle independently and the new knob defaults off and loads additively (REQ-005, REQ-004, REQ-003, REQ-006); repoint the existing unavailable-repeat tests to the new knob (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit
- `tests/agent/test_tool_loop_guard.py` only.

## Assumptions
- `_cfg(**overrides)` passes keys through `build_agent_config`, so `_cfg(tool_unavailable_repeat_max_repeats=2)` exercises the builder; `tool_empty_result_max_repeats` is not mapped by the builder, so it is set on `cfg.tool` directly (existing tests do this).
- Depends on seq 1-3 of this Plan.

## Design decisions
- Extend, do not replace: change `TestUnavailableRepeat._guard` to set `tool_unavailable_repeat_max_repeats` (new), then add one new test class for the four-combination matrix.

## Alternatives considered
N/A: follows the file's existing class-per-guard layout.

## Implementation
### Target file
`tests/agent/test_tool_loop_guard.py`

### Procedure
1. In `TestUnavailableRepeat._guard`, replace `ctx.cfg.tool.tool_empty_result_max_repeats = limit` with `ctx.cfg.tool.tool_unavailable_repeat_max_repeats = limit`; the existing assertions then still hold.
2. In `TestReportEffectiveState::test_defaults_unchanged` add `assert cfg.tool_unavailable_repeat_max_repeats == 0` (REQ-004).
3. Add class `TestGuardsToggleIndependently` (new): a parametrized test over (`empty_limit` (new), `unavail_limit` (new)) in `{0, 2} x {0, 2}` that feeds two empty results via `record_tool_result` and two hinted results via `observe_availability` and asserts `scan_empty_result_repeat() is not None` iff `empty_limit > 0`, and `scan_unavailable_repeat() is not None` iff `unavail_limit > 0` (REQ-003, REQ-004, REQ-005).
4. Add a builder test (new): `_cfg(tool_unavailable_repeat_max_repeats=3).tool.tool_unavailable_repeat_max_repeats == 3` and `_cfg().tool.tool_unavailable_repeat_max_repeats == 0` (REQ-006).

### Method
Reuse `_make_ctx`, `_hinted_result` and `_plain_result`; build empty results with a tool name and `""` output. Set both knobs on `ctx.cfg.tool` directly in the matrix test.

### Details
- The health-lifecycle test that sets `tool_empty_result_max_repeats = 2` only calls `observe_availability`; it needs no edit.
- Confirm no pinned `ToolConfig` field-count assertion exists: `rg "fields\(ToolConfig\)|len\(.*ToolConfig" tests` (Plan Tests item).

## Compatibility considerations
Tests only.

## Security considerations
N/A: tests only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_loop_guard.py -q`; the matrix test must fail if step 1 of the `tool_loop_guard.py` procedure is reverted.

## Completion criteria
- All four knob combinations asserted; default-off and additive-load asserted; the former unavailable-repeat tests pass against the new knob.

## Out of Scope
Production code, docs, `test_llm_turn_runner.py` (own procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Repoint `TestUnavailableRepeat._guard` and extend the default test | Completed | 2026-11-09 | 2026-11-09 |  |
| 2 | Add the independence matrix test and the builder test | Completed | 2026-11-09 | 2026-11-09 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-09 | 2026-11-09 |  |

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
- **Requirement ID**: `REQ-002` (repointed tests), `REQ-003`, `REQ-004`, `REQ-005` (independence), `REQ-006` (additive load)
- **Source issue**: `issues/20261107-191650_loopguard02_unavailable-repeat-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_loopguard02_unavailable-repeat-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195023
- **Related target files**: `tests/agent/test_tool_loop_guard.py`