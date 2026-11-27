# Implementation Procedure — scripts/mcp_servers/mdq/mdq_tools.py

## Goal

Declare `retry_policy = never` for `index_paths` and `refresh_index`, so the two MDQ write tools
are refused when the durable dedup store is unavailable instead of dispatched with the fail-open
marker (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-005. Acceptance criterion: AC-3.

## Assumptions
- Full form: `retry_policy` is the authority for the retry class (`scripts/agent/tool_call_identity.py::_classify_retry_class`
  reads the declared field), so this row changes a contract other consumers read.
- `never` is already a member of `RETRY_POLICY_VALUES` (`scripts/shared/tool_metadata.py` lines 38-40);
  no new vocabulary value is introduced.
- No field-consistency rule couples `retry_policy` with `reconciliation_policy` or
  `idempotency_required` (`scripts/shared/resource_scope.py` only checks presence and type), so those
  fields stay as they are; the Plan's scope changes only the declared policy.
- The classification is temporary: it is reconsidered only after operation-specific reconciliation is
  proven, and no reconciliation mechanism is designed here.
- Overlap: this file is also targeted by plans 007, 008, 010; compatible ordering overlap, and plan
  001 changes `config_dependent` on the same entries, an independent field.

## Design decisions
- Change only the two declarations; the existing non-retryable refusal path in
  `scripts/mcp_servers/dispatch.py` and the `store_error` branch in `scripts/mcp_servers/dedup_gate.py`
  (line 273) are reused, nothing is reimplemented.
- No ADR change: the declared field is already the authority (ADR-002.02 Decision Detail 18), so the
  ADR wording stays as is (the Plan's UNK-03 default).

## Alternatives considered
- Keep the declared value and change only the reference data: rejected, because the reference set is
  not the owner and the drift check would then report the contradiction.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_tools.py`

### Procedure
- Change `"retry_policy"` from `"same_logical_call_only"` to `"never"` for `index_paths` (line 172) and
  `refresh_index` (line 205).

### Method
- The declared value is read at dispatch time, so the change takes effect without any dispatcher edit.

### Details
- No other tool field changes; `policy_version` stays `TOOL_FIELD_SET_VERSION`.

## Compatibility considerations
- `tests/shared/test_tool_constants.py` (this Plan's row 11) compares the declarations with the
  reference set, so the reference data must move in the same phase.
- `tests/mcp_servers/test_mcp_dispatch.py` (row 12) injects the mdq values as expected data.
- No mdq test asserts the declared `retry_policy` today (`grep` over `tests/mcp_servers/mdq/`), so no
  existing pin breaks.

## Security considerations
- N/A: classification only; the fail-closed behavior already exists in the dispatcher.

## Rollback considerations
- N/A: revert the commit; rows 4 and 5 must roll back together to keep the drift check consistent.

## Validation plan
- `uv run pytest tests/shared/test_tool_constants.py tests/mcp_servers/test_mcp_dispatch.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- Both tools declare `never`, are refused on store unavailability, and the declarations agree with the
  reference data (AC-3).

## Out of Scope
- The reference data set (row 5); the drift and dispatch tests (rows 11, 12); the doc statement of the
  temporary classification (row 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Rows 11, 12 have their own documents |
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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `scripts/mcp_servers/mdq/mdq_tools.py`
