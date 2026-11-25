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
Write the transaction tests before the transaction module exists, per the Plan's Phase 4 step 1: the
commit-failure matrix, the `degraded` reporting case, the post-`degraded` guard, and the section-identity
assertions.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-194130 | 20261125-194130 | tests written before row 7 R4-transaction-and-restore 20261125: implemented as recorded in this procedure's Blocker Log |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-194130 | 20261125-194130 | R4 20261125: targeted run tests/agent/services tests/agent/commands tests/shared tests/agent/test_history_manager.py = 2821 passed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | R4 execution (2026-11-25): 40 cases. The commit-failure matrix parametrizes a failure at each of the five phases and asserts the apply and restore call log is the applied prefix followed by that prefix in reverse, with stage `rolled_back`; the degraded case makes one restore fail and asserts the remaining restores still run, the stage is `degraded`, and the error names the service; refusal after `degraded` is asserted at both the transaction and the `ConfigReloadService` level | Yes | 2026-11-25 |
| 2 | R4 execution (2026-11-25): the companion restore-pair cases run inside this file (row 16, 17, 18 live services) and the per-service unit cases also live in `tests/shared/test_llm_hot_config.py`, `tests/agent/test_history_manager.py`, and `tests/shared/test_runtime_tool_registry.py`. The MCP non-commit case asserts `ctx.cfg.mcp` is the same object, no lifecycle call happens, and the stage stays `prepared` | Yes | 2026-11-25 |

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