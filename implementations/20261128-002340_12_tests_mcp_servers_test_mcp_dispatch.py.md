# Implementation Procedure — tests/mcp_servers/test_mcp_dispatch.py

## Goal

Move the injected mdq policies to `never` and add the store-failure refusal cases for both MDQ write
tools, so the overlay path mirrors the new class (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-005. Acceptance criterion: AC-3.

## Assumptions
- Lightweight fill: the change is confined to one fixture and two added cases, with no production
  behavior change in this file.
- The fixture injects `index_paths` and `refresh_index` as `same_logical_call_only` (lines 161-162) to
  mirror the real declarations, so the fixture must move with row 4.
- This row gets its own document because no other row names it in `Related Tests`.
- The fail-closed path is already proven generically by
  `test_store_error_retryable_proceeds_non_retryable_fails_closed` (line 974); the new cases run the
  same boundary for the mdq tools.

## Design decisions
- Use the existing `durable` fixture and the existing refusal assertions; no new fixture or helper.

## Alternatives considered
- Rely on the generic case and change only the fixture: rejected by the Plan's Tests section, which
  names store-failure refusal for both write tools.

## Implementation
### Target file
`tests/mcp_servers/test_mcp_dispatch.py`

### Procedure
- Change the injected values at lines 161-162 to `never`.
- Add one case per mdq write tool asserting refusal with the non-retryable error type when the store
  is unavailable.

### Method
- Assert `error_type == "dedup_store_error"` as the existing cases do.

### Details
- No change to the other injected policies in the fixture.

## Compatibility considerations
- `tests/agent/test_tool_approval_paths.py`, `tests/agent/test_tool_approval_repos.py`, and
  `tests/agent/test_tool_runner.py` build their own fixtures and do not read the mdq declarations, so
  they are unaffected.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- Both mdq write tools are refused when the dedup store is unavailable (AC-3).

## Out of Scope
- The declarations (row 4); the reference data (row 5); the drift check (row 11).

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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `tests/mcp_servers/test_mcp_dispatch.py`
