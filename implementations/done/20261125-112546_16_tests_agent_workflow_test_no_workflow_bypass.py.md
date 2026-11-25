## Goal
Move the hand-written fake engine in this file to the `TurnControl` contract.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The stub at line 75 returns an empty string and no test in this file asserts control text, so returning `None`
  keeps the bypass behavior the tests check.

## Design decisions
N/A: stub signature update.

## Alternatives considered
N/A: test-only change.

## Implementation
### Target file
`tests/agent/workflow/test_no_workflow_bypass.py`

### Procedure
Change the fake engine's `build_turn_control_message` to the contract type.

### Method
Annotate the return as `TurnControl` (resolved from sibling procedure seq 07) or `None` and return `None`.

### Details
- If a guard in this file later asserts that the adapter received control text, return a `TurnControl` with the
  same text and no directives instead of `None`.

## Compatibility considerations
The adapter calls this stub through the same contract as the real engine, so the stub must not return a plain
string after the contract change.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_no_workflow_bypass.py` (REQ-007).

## Completion criteria
The bypass guard still proves no workflow-layer bypass exists, and the stub matches the engine contract.

## Out of Scope
No change to the bypass detection itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the fake engine stub to the `TurnControl` contract | Completed | — | 20261125-132507 | stub now annotated 'TurnControl | None' and returns None; TurnControl added to the existing workflow_engine import; no test in the file asserts control text, so the bypass guard is unaffected |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 2026-11-25 | 3 passed; ruff format/check pass; mypy clean on this file; end-of-batch run: full suite 14240 passed, diff-cover 100% on changed lines, pre-commit all hooks pass, cited ADR tests 75 passed |

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
- **Requirement ID**: `REQ-007` (every intermediate type and test of the replay path in the same change set)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tests/agent/workflow/test_no_workflow_bypass.py`