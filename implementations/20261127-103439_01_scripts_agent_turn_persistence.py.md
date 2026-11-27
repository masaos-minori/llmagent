## Goal

Make the turn boundary validate each phase group before writing, compare the inserted-row count, report the compensation status on the error, mark the session degraded when compensation fails, and keep the public error string free of raw SQLite detail.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-001 (pre-write phase-group validation on the turn path), REQ-002 (inserted-count comparison), REQ-003 (compensation status on the error), REQ-004 (degraded-session marking), REQ-005 (safe public error format). Acceptance criteria: AC-1, AC-2, AC-3, AC-4.

## Assumptions
- The repository's skip-and-warn contract stays for non-turn callers (Plan decision D2); this document adds pre-write validation only on the turn path.
- Clearing the degraded state is not implemented here: UNK-01 was resolved by user decision on 2026-11-27 as a defined seam, so this document only marks the state.
- `CompensationStatus` (new) is defined in this file and imported by `scripts/agent/turn_result.py`; this file does not import `turn_result.py`, so no import cycle is introduced.

## Design decisions
- D1: `CompensationStatus` (new) StrEnum with statuses completed, failed, and `not_needed` (new), exposed as `ConversationPersistenceError.compensation` (new).
- D5: the public string carries the message plus the masked exception type name through `scripts/agent/secrets_masker.py`; the raw cause stays on `__cause__` and the `cause` attribute for internal logs only.

## Alternatives considered
- Status on the error only: rejected, REQ-003 requires it on `TurnResult` as well.
- Flipping `strict_mode` to `True` globally: rejected per Plan decision D2 — it would change behavior for non-turn repository callers and break the pinned skip-and-warn tests.

## Implementation
### Target file
`scripts/agent/turn_persistence.py`

### Procedure
- Define `CompensationStatus` (new) StrEnum with `not_needed` (new) as the default status.
- Add a `compensation` (new) keyword to `ConversationPersistenceError.__init__` and expose it as an attribute.
- Change the public error string to the message plus the masked exception type name.
- Add a pre-write phase-group validation step that rejects the whole group when any role is invalid or the session id is missing, before the repository call.
- Compare the inserted-row count returned by the repository write methods with the expected count; a non-empty group with a zero or mismatched count fails through the existing failure path.
- In `_fail_from_error`, set the status and mark the session degraded when compensation fails.

### Method
- Replace `f"{message}: {cause}"` at line 50 with the message plus the masked exception type name.
- Validate roles against the repository's `_valid_roles` (from `MessageRoleConfig`, `scripts/agent/config_dataclasses.py` line 337) and the session id before each `asyncio.to_thread` repository call.
- Set `_write_committed` only when the count returned by the repository equals the expected count.
- Call the session's marking method defined in `scripts/agent/session.py` when the compensation delete raises.

### Details
- `_write_committed` sites are lines 110, 125, 143, 163; all four move behind the count comparison.
- The compensation failure branch is lines 223-226; the status is recorded there before the error is raised at lines 230-232.
- `not_needed` (new) applies when no write had committed (`_compensate` returns False, line 242).

### Companion test files
- `tests/agent/test_turn_persistence.py`
  - Procedure: fault-injection tests first — compensation success and failure, inserted-count mismatch, zero-row write, invalid role mixed with valid roles, missing session id.
  - Validation: `uv run pytest tests/agent/test_turn_persistence.py`.

## Compatibility considerations
- Display consumers `scripts/agent/cli_view.py` and `scripts/agent/commands/output_port.py` keep their interface; only the message content may cite the status.
- `TurnResult` consumers `scripts/agent/llm_turn_runner.py` and `scripts/agent/llm_turn_executor.py` are unaffected (additive defaulted field).

## Security considerations
- The masked public error string keeps raw SQLite and secret detail out of the console (REQ-005); the unmasked cause stays internal.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit and fault-injection tests in `tests/agent/test_turn_persistence.py`: status distinguishes clean rollback from failed compensation; count mismatch and zero-row write are rejected.
- Static gates: `uv run ruff check`, `uv run mypy`, `uv run lint-imports` (the status enum stays inside `agent/`).

## Completion criteria
- An invalid or incomplete phase group is rejected before any write (AC-1).
- A zero-row write from a non-empty group is never marked committed (AC-1).
- The caller can read completed, failed, or `not_needed` (new) from the error (AC-2).
- A compensation failure marks the session degraded through the session (AC-3).
- No raw SQLite detail appears in the public error string (AC-4).

## Out of Scope
- The degraded-state clearing criteria (UNK-01 seam).
- Non-turn repository callers such as `scripts/agent/tool_runner.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (pre-write phase-group validation), REQ-002 (inserted-count comparison), REQ-003 (compensation status on the error), REQ-004 (degraded-session marking), REQ-005 (safe public error format)
- **Source issue**: `issues/20261119-145308_cliplc010_strict-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-211240_cliplc010_strict-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-103439
- **Related target files**: `scripts/agent/turn_persistence.py`, `tests/agent/test_turn_persistence.py`
