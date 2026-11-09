## Goal
Document the two independent knobs in the tool configuration reference (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit
- One paragraph in `docs/23_agent/agent_08_03_configuration-tools-memory.md` section "Execution Control and Context Bloat".

## Assumptions
- Verified: that section lists loop limits but does not mention either empty-result or unavailable-repeat knobs; the Plan's cited line 39 is that paragraph.
- `AGENTS.md` Global Rule 9 doc checkers run on this change.

## Design decisions
- Add a sentence stating that both guards are off at 0, each is enabled by its own field, and `tool_empty_result_max_repeats` does not affect unavailable-repeat detection.

## Alternatives considered
N/A: docs-only.

## Implementation
### Target file
`docs/23_agent/agent_08_03_configuration-tools-memory.md`

### Procedure
1. After the "Loop limits ..." sentence in "Execution Control and Context Bloat", add: `Two repeat guards have independent thresholds, both default 0 (disabled): tool_empty_result_max_repeats (consecutive empty results of one tool) and tool_unavailable_repeat_max_repeats (consecutive server-unavailable hints for one server). A value above 0 enables only its own guard.`

### Method
Edit the doc text only; no code.

### Details
- Keep the field names in backticks as elsewhere in the file.

## Compatibility considerations
N/A: docs-only.

## Security considerations
N/A: docs-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py` or the doc checkers `tools/run_validation_gates.py` selects for `docs/` changes.

## Completion criteria
- The section names both fields, their defaults and their independence.

## Out of Scope
`agent_06_01` and `agent_03_02` wording; code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the two-knob paragraph | Completed | 2026-11-09 | 2026-11-09 |  |
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
- **Requirement ID**: `REQ-001` (document the new knob)
- **Source issue**: `issues/20261107-191650_loopguard02_unavailable-repeat-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_loopguard02_unavailable-repeat-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195023
- **Related target files**: `docs/23_agent/agent_08_03_configuration-tools-memory.md`