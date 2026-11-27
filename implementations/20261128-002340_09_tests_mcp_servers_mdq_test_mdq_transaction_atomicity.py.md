# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py

## Goal

Create the fault-injection suite that proves a failed file operation leaves no partial state and that
postconditions are checked before success (REQ-001, REQ-002, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-002, REQ-006. Acceptance criteria: AC-1, AC-4.

## Assumptions
- Full form: this is a new file and the only proof of the atomicity contract, so the injection points
  have to be defined here.
- The file does not exist; `tests/mcp_servers/mdq/` holds 35 test files and none injects a failure
  inside a transaction (`side_effect` appears only in `test_db_schema.py`, `test_mdq_config.py`,
  `test_mdq_config_error_degradation.py`, `test_mdq_error_taxonomy.py`,
  `test_mdq_exception_handlers.py`, at schema-creation or handler boundaries, not mid-transaction).
- This row gets its own document although it is named in `Related Tests` by rows 1 and 3, because a
  companion may be named by exactly one row (`SKILL.md` companion rule).
- Phase 1 runs before any behavior change: the first tests characterize partial state on the current
  code, then the same assertions are flipped after rows 1 and 3 land.

## Design decisions
- Inject at three points: the commit, the `chunks_ad` trigger, and the `index_state` write, so each
  boundary that could leave partial rows is covered independently.
- Assert observable row counts for `documents`, `chunks`, the FTS5 table, and `index_state` rather
  than the transaction state, so the proof does not depend on which module commits.

## Alternatives considered
- Inject only at the commit: rejected, because a trigger or state-write failure can leave rows behind
  even when the commit path is clean.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` (new)

### Procedure
- New file with the shared fixture pattern used by the other mdq tests (`tmp_path` service fixture).
- Characterization tests first: show that the current code leaves partial state when the commit, the
  trigger, or the state write fails.
- After rows 1 and 3 land, the same cases assert zero rows in all four stores and no success reported.

### Method
- Failure is injected through `monkeypatch` on the connection's execute path at the named statement,
  and the postcondition helper is asserted to run before the commit by recording statement order.

### Details
- One test per injection point plus one that a failed postcondition check prevents the state write.

## Compatibility considerations
- `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` pins the transaction shape through a
  recording connection; that pin moves with rows 1 and 3 (row 7's companion document).

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: delete the new file (single file, no confirmation needed).

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- A failed file operation leaves no partial state at all three injection points, and postconditions
  are checked before success is reported (AC-1, AC-4).

## Out of Scope
- The exact-key delete cases (row 10); the transaction ownership implementation (rows 1, 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/22_mcp/mcp_04_04_mdq.md` (row 13) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-006
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py`
