## Goal

Re-export the new result type, classification helper, and contract vocabularies through the `shared.mcp_dedup` facade, and correct the docstring that states the store version.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the import block from the split modules, `__all__`, and the version sentence in the module docstring. The file is about 20.4 KB of 24.6 KB.

## Assumptions

- Verified: the facade imports from `shared.mcp_dedup_schema` and the split row/ledger modules and lists the public names in `__all__`; the docstring at line 12 states `user_version = 1`.

## Design decisions

- Re-export `CallStateView`, `StoredResult`, `classify_result` from the rows module and `RESULT_CLASSES`, `RECONCILE_OUTCOMES`, `CONTROL_ERROR_CODES` from the contract module; `call_state_view` is reachable as a `DedupStore` method with no extra name.

## Alternatives considered

Rejected: having consumers import the split modules directly (the facade is the consumer-facing surface per the module size-gate split note).

## Implementation
### Target file
`scripts/shared/mcp_dedup.py`

### Procedure
1. Add the names to the imports and keep `__all__` sorted.
2. Change the docstring version sentence to version 2.

### Method
Edit imports and `__all__` only; no logic.

### Details
- Keep the existing ruff import-order grouping.

## Compatibility considerations

Additive re-exports only.

## Security considerations

N/A: no behavior or data change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_dedup.py`
- `uv run ruff check` and `uv run mypy scripts/` stay clean

## Completion criteria

- The listed names import from `shared.mcp_dedup`; the docstring says version 2; the file is under the size gate.

## Out of Scope

Logic changes in the split modules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-160000 | 20261123-160000 | facade re-exports and docstring version 2 |
| 2 | Add or update tests per Validation plan | Completed | 20261123-160000 | 20261123-160000 | covered by row 26 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-160000 | 20261123-160000 | gates pass |

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
- **Requirement ID**: `REQ-001` (control endpoints and response shape), `REQ-003` (result metadata and result classes at finalization)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/shared/mcp_dedup.py`
