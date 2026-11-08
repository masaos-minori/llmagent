## Goal
Repoint the unavailable-repeat guard to its own knob (REQ-002) with `<= 0` disabling it (REQ-004) while the empty-result guard keeps its knob (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit
- `ToolLoopGuard.scan_unavailable_repeat` and the `check_unavailable_repeat` docstring only.

## Assumptions
- Verified: the only runtime caller is `scripts/agent/llm_turn_runner.py` (`check_unavailable_repeat`), and it does not read the knob itself.
- Depends on the `config_dataclasses.py` procedure (seq 1).
- Adversarial finding recorded in the Plan: `report_effective_state()` logs only retry suppression and empty-result state; adding the new guard there is deferred (Plan UNK-01).

## Design decisions
- Change only the config attribute read; keep the method contract (`tuple[str, int] | None`, non-recording scan).
- Rewrite the `check_unavailable_repeat` docstring to name the new knob and drop the "reuses the empty-result bound" claim.

## Alternatives considered
N/A: a one-attribute repoint.

## Implementation
### Target file
`scripts/agent/tool_loop_guard.py`

### Procedure
1. In `scan_unavailable_repeat`, change `limit = self._ctx.cfg.tool.tool_empty_result_max_repeats` to `limit = self._ctx.cfg.tool.tool_unavailable_repeat_max_repeats`.
2. In the `check_unavailable_repeat` docstring replace the "Reuses the empty-result repeat bound (``tool_empty_result_max_repeats``)" sentence with one naming ``tool_unavailable_repeat_max_repeats` (new)`; keep "limit <= 0 disables the check entirely (default-off)".

### Method
Two edits inside the "Unavailable repeat guard helpers" section. Do not edit `record_tool_result`, `scan_empty_result_repeat`, `check_empty_result_repeat` or `report_effective_state`.

### Details
- After the edit `rg tool_empty_result_max_repeats scripts/agent/tool_loop_guard.py` must show only the empty-result guard's reads and `report_effective_state`.
- Existing tests that arm the unavailable guard through the old knob must be repointed in the `test_tool_loop_guard.py` and `test_llm_turn_runner.py` procedures; this file's change alone breaks them.

## Compatibility considerations
Behavior change by design: configs that relied on `tool_empty_result_max_repeats > 0` to also arm the unavailable-repeat guard no longer do. The repository default is 0 for both and the builder never wires the old knob, so no shipped config is affected (production use: 不明).

## Security considerations
N/A: the guard summary stays the fixed string; no server free text is introduced.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_loop_guard.py tests/agent/test_llm_turn_runner.py tests/agent/test_tool_runner.py -q`
- `uv run python tools/check_docstrings.py`

## Completion criteria
- `scan_unavailable_repeat` reads only the new field; the empty-result methods read only the old one.
- Docstring no longer claims the shared bound.

## Out of Scope
`observe_availability` accumulation, `availability_hint` channel, dedup and retry-suppression guards, startup diagnostic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Repoint `scan_unavailable_repeat` and update the docstring | Pending | — | — |  |
| 2 | Update dependent tests (`test_tool_loop_guard.py`, `test_llm_turn_runner.py` procedures) | Pending | — | — | Must land together with step 1 |
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
- **Requirement ID**: `REQ-002` (read the new knob), `REQ-003` (empty-result guard unchanged), `REQ-004` (`<= 0` disables)
- **Source issue**: `issues/20261107-191650_loopguard02_unavailable-repeat-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_loopguard02_unavailable-repeat-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195023
- **Related target files**: `scripts/agent/tool_loop_guard.py`
