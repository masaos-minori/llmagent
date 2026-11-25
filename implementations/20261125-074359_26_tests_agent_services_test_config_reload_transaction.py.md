## Goal

Prove the rollback contract: commit failure at each stage restores every reversible service in reverse
order, a failing rollback yields `degraded`, a later `/reload` after `degraded` is refused, and restore
writes into the same section objects (REQ-005, stage reporting; REQ-006, service snapshot and restore;
REQ-007, no live lifecycle call; REQ-012, degraded guard).

## Scope
**Release unit**: R4-transaction-and-restore

## Assumptions
- The transaction is created by row 7; this file is written before it, per the Plan's Phase 4 order
  (tests first).
- The three services expose snapshot and restore through rows 16, 17, 18; the tests use those APIs rather
  than reaching into private attributes.

## Design decisions
- A commit-failure matrix: one test per failure point (after the first, second, and final applied step),
  so AC-3 cannot be satisfied by a single happy-path rollback test.
- Section identity is asserted with `is`, not equality, because the live services hold references to the
  same section instances (Plan `Assumptions`).

## Alternatives considered
- Testing rollback through the reload service only — rejected: it would not show the order of restore.

## Implementation
### Target file
`tests/agent/services/test_config_reload_transaction.py` (new)

### Procedure

### Method
- Commit-failure cases at each applied step, asserting reverse-order restore of the three services.
- A rollback-failure case asserting `degraded` and the service names left inconsistent.
- A guard case asserting a later `/reload` is refused after `degraded`.
- A case asserting the irreversible MCP path is gated before any live mutation (REQ-007).

### Details
- No test here asserts a specific message wording; the message content is asserted in row 38.

## Compatibility considerations
- New file; no rollback test exists in `tests/agent/services/` today.

## Security considerations
- N/A: the tests assert structure, not output.

## Rollback considerations
- Revert the Phase 4 commit.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload_transaction.py -q`

## Completion criteria
- Every commit-failure point has a test that shows all reversible services restored in reverse order, and
  the degraded path has both a reporting test and a guard test.

## Out of Scope
- The CLI reporting (row 19).
- Per-service snapshot tests (rows 16, 17, 18 companions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | tests written before row 7 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (reload transaction and stage), REQ-006 (service snapshot and restore), REQ-007 (no live lifecycle call), REQ-012 (degraded guard); AC-3, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `tests/agent/services/test_config_reload_transaction.py`
