## Goal

Add the compensation status field to `TurnResult` so the caller can read it from the turn result, not only from the error.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-003 (compensation status on the turn result). Acceptance criterion: AC-2.

## Assumptions
- The field is additive with a default, so existing construction sites compile unchanged.

## Design decisions
- D1: the field type is `CompensationStatus` defined in `scripts/agent/turn_persistence.py`; this module imports it from there. `turn_persistence.py` does not import this module, so no cycle is introduced.

## Alternatives considered
- A plain `str` field: rejected, the Plan fixes the status vocabulary as an enum.

## Implementation
### Target file
`scripts/agent/turn_result.py`

### Procedure
- Add `compensation: CompensationStatus = CompensationStatus.NOT_NEEDED` to the frozen dataclass at line 19.

### Method
- Import `CompensationStatus` from `scripts/agent/turn_persistence.py` under the existing `TYPE_CHECKING`-free import style used by this module.

### Details
- The dataclass stays frozen; the default keeps positional construction sites unchanged.

### Companion test files
- `tests/agent/test_llm_turn_executor.py`
  - Procedure: assert the default value and the recorded value on a compensated turn.
  - Validation: `uv run pytest tests/agent/test_llm_turn_executor.py`.

## Compatibility considerations
- Consumers `scripts/agent/llm_turn_runner.py` and `scripts/agent/llm_turn_executor.py` are unaffected: additive field with default.
- Frozen-dataclass equality tests that pin construction use defaults and stay valid.

## Security considerations
- N/A: no security-sensitive behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit test: the default is `not_needed`; a compensated turn records the status from the error.
- Static gates: `uv run ruff check`, `uv run mypy`, `uv run lint-imports`.

## Completion criteria
- The caller can read the compensation status from the turn result (AC-2).

## Out of Scope
- Recording the status into the result (done in `scripts/agent/orchestrator.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-113439 | 20261127-113513 | stale check clean; CompensationStatus resolved from sibling procedure 01 (landed) files changed: scripts/agent/turn_result.py |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-113521 | default + recorded-status + equality tests added; 6 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-113521 | 20261127-151312 | gates passed (ruff, mypy, lint-imports, bandit); full-suite run deferred to end of batch; docs row covered by procedure 13 end-of-batch full suite: 16009 passed, 5 skipped; diff-cover 93% >= 90% |

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
- **Requirement ID**: REQ-003 (compensation status on the turn result)
- **Source issue**: `issues/20261119-145308_cliplc010_strict-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-211240_cliplc010_strict-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-103439
- **Related target files**: `scripts/agent/turn_result.py`, `tests/agent/test_llm_turn_executor.py`