## Goal
Correct the statement that the unavailable-repeat bound reuses the empty-result configuration (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit
- The single sentence at line 87 of `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`.

## Assumptions
- Adversarial finding: the Plan originally named `agent_06_03` line 87; that file has 79 lines and its line 41 remains accurate. The coupling sentence is in `agent_06_01` (corrected in the Plan).

## Design decisions
- Replace the "bounded by the existing empty-result repeat configuration (`tool_empty_result_max_repeats`)" clause with its own knob; keep the remainder (off at 0, observable hint, recovery clears the count).

## Alternatives considered
N/A: docs-only.

## Implementation
### Target file
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure
1. In the paragraph beginning "Repeated selection of tools returning the same server-unavailable hint", change the bound to its own configuration `tool_unavailable_repeat_max_repeats`, and say the bound is off when it is 0 (the repository default) and independent of `tool_empty_result_max_repeats`.

### Method
Edit that sentence only.

### Details
- Leave the "unavailable-repeat bound" list item further down unchanged.

## Compatibility considerations
N/A: docs-only.

## Security considerations
N/A: docs-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Documentation checkers selected by `tools/run_validation_gates.py` for `docs/` changes.

## Completion criteria
- No sentence in `docs/` claims the unavailable-repeat bound uses `tool_empty_result_max_repeats`: `rg -n "unavailable.*empty-result|empty-result.*unavailable" docs` shows none.

## Out of Scope
Other docs; code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the coupling sentence | Completed | 2026-11-09 | 2026-11-09 |  |
| 2 | Run the documentation checkers (`routing.md` Tools) | Completed | 2026-11-09 | 2026-11-09 |  |

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
- **Requirement ID**: `REQ-002` (coupling statement corrected)
- **Source issue**: `issues/20261107-191650_loopguard02_unavailable-repeat-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_loopguard02_unavailable-repeat-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195023
- **Related target files**: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`