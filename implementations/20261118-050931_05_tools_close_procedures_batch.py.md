## Goal
Build `TERMINAL_STATUSES` in `tools/close_procedures_batch.py` from the shared vocabulary constants instead of the local literal, so the batch-close tool and the vocabulary source can no longer diverge.

## Scope
**Release unit**: N/A: not part of a release unit
**Companion test file**: `tests/tools/test_close_procedures_batch.py` (covered by this document; it has no procedure document of its own)

## Assumptions
- The vocabulary constants exist after `implementations/20261118-050931_01_tools__workitem_status_table.py.md` lands; the shared TERMINAL_STATUSES holds exactly Completed and N/A, the same two values the local literal holds today.
- The module is 21498 B of the 24576 B gate; replacing a literal with an import keeps it under the gate.

## Design decisions
- Import TERMINAL_STATUSES from `tools/_workitem_status_table.py` (directly or through the `tools/manage_workitem_stage.py` re-exports the module already uses) and delete the local frozenset definition; no behavior change (REQ-002: "without a behavior change").
- If a name collision with the local constant is awkward for readers, alias on import; the constant's meaning is identical.

## Alternatives considered
- Keeping the local set and asserting equality to the shared one in the test only: rejected — the Plan row's responsibility is to build the set from the shared constants, and a passing equality test on two literals would not prevent divergence of the source value.
- Removing `N/A` from the terminal set: rejected by Decision 1 (UNK-01, accepted option).

## Implementation
### Target file
`tools/close_procedures_batch.py`

### Procedure
1. Add the import of the shared TERMINAL_STATUSES from `tools/_workitem_status_table.py`.
2. Delete the local frozenset literal and let every read site use the imported name.

### Method
One import line replaces one constant definition; all read sites keep the same name.

### Details
- The module already imports status helpers through `tools/manage_workitem_stage.py`; prefer the direct import of the shared module for the constant (the checker and the sync tool import the status module directly too), and keep the existing re-export imports untouched.

### Companion test files
- `tests/tools/test_close_procedures_batch.py`
  - Procedure: add the terminal-set equality case — the terminal set used by the tool equals the shared constants of `tools/_workitem_status_table.py` (REQ-002 / AC-2); write it first (Plan Phase 1) — it fails until the import lands.
  - Validation: `uv run pytest tests/tools/test_close_procedures_batch.py -q` — the equality case passes and the existing behavior tests pass unchanged.

## Compatibility considerations
- Behavior is identical: the same two strings remain terminal, so close, supersede, and plan-step marking decisions do not change.

## Security considerations
No new I/O or configuration surface.

## Rollback considerations
Restore the literal and remove the import; revert the companion test addition in the same commit.

## Validation plan
- Companion test in `tests/tools/test_close_procedures_batch.py`: the terminal set used by the tool equals the shared constants (REQ-002 / AC-2).
- `uv run pytest tests/tools/test_close_procedures_batch.py -q` plus the Plan's importer regression row; lint, mypy, bandit, size gate.

## Completion criteria
- The tool has no local terminal literal left; the equality test passes; existing behavior tests pass unchanged.

## Out of Scope
- Any change to close, supersede, or archive behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261117-132201_wftoolfu001_workitem-status-vocabulary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-050931
- **Related target files**: `tools/close_procedures_batch.py`, `tests/tools/test_close_procedures_batch.py`
