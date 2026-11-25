## Goal
Move the hand-written fake engine in this file to the `TurnControl` contract.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The stub at line 4101 returns `None` and performs no state work, so only its declared return type changes.

## Design decisions
N/A: stub signature update.

## Alternatives considered
N/A: test-only change.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure
Change the fake engine's `build_turn_control_message` annotation to the contract type.

### Method
Annotate the return as `TurnControl` (resolved from sibling procedure seq 07) or `None` and keep the `None` return.

### Details
- The docstring line that cites the contract (toolexec001 row 08) stays; no behavior change is expected because
  the orchestrator tests do not assert control text.

## Compatibility considerations
Only the fake engines that the adapter calls are affected; files that import the engine without calling the
method are not.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_orchestrator.py` (REQ-007).

## Completion criteria
The fake matches the engine contract and the orchestrator tests still pass.

## Out of Scope
No change to the turn-boundary tests in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the fake engine stub to the `TurnControl` contract | Completed | — | 20261125-132424 | fake engine annotation is now 'TurnControl | None'; TurnControl added to the existing workflow_engine import (same layer, no contract change); the stub still returns None |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 2026-11-25 | 149 passed; ruff format/check pass; check_mock_patch_targets clean; mypy shows the 61 pre-existing errors of this file unchanged (none on the changed lines, tests/agent is outside the CI mypy scope); end-of-batch run: full suite 14240 passed, diff-cover 100% on changed lines, pre-commit all hooks pass, cited ADR tests 75 passed |

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
- **Related target files**: `tests/agent/test_orchestrator.py`