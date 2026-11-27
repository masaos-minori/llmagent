# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_index_serialization.py

## Goal

Run the serialization proof against the single caller-owned transaction and add the case that a
mid-operation failure in one call leaves no partial state for the other (REQ-001, AC-1).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001. Acceptance criterion: AC-1.

## Assumptions
- Full form: this row changes what the tests observe, not only fixture data, and it is the only
  coverage of the concurrency boundary.
- This row gets its own document because no other row names it in `Related Tests`, so it is not a
  companion under `SKILL.md`'s companion rule.
- The existing proof records start and end only inside the section protected by `_index_lock`
  (`test_concurrent_refresh_calls_are_serialized`, line 44); that mechanism is kept, not rewritten.

## Design decisions
- Keep the three serialization tests as behavior locks and add one failure case; the tests assert the
  observable order and row counts, not the internal commit call.

## Alternatives considered
- Move the failure case into `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` instead:
  rejected, because the point here is what a second concurrent call observes, which only this file's
  fixtures can produce.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_index_serialization.py`

### Procedure
- Keep `test_concurrent_refresh_calls_are_serialized` (line 44),
  `test_concurrent_index_paths_calls_are_serialized` (line 82), and
  `test_index_paths_and_refresh_index_are_serialized` (line 116) passing against the caller-owned
  transaction.
- Add one test that fails the first call inside its transaction and asserts the second call sees the
  pre-operation state (no partial document, chunk, FTS5, or `index_state` rows).

### Method
- The failure is injected through the existing monkeypatch pattern in this file; the assertion is on
  row counts read through a separate connection, so it does not depend on the transaction internals.

### Details
- `test_is_indexing_warning_visible_during_active_index` (line 175) is unaffected and stays as is.

## Compatibility considerations
- This file is also targeted by plans 008 and 010; compatible ordering overlap, this Plan executes
  first.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_index_serialization.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The three serialization tests pass against the caller-owned transaction and the new failure case
  shows no partial state (AC-1).

## Out of Scope
- The transaction ownership change itself (row 3); the fault-injection suite (row 9).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation in scope |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_index_serialization.py`
