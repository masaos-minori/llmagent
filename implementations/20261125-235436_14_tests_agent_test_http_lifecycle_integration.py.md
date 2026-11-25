## Goal

Add end-to-end unconfirmed-visibility and repeated-shutdown tests across real processes (REQ-009, REQ-010, REQ-011).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 1 tests are outside R3-ownership)

## Assumptions
- Phase 1 tests are expected to fail until Phases 3-5 land.

## Design decisions
- N/A: test row, no design decision of its own.

## Alternatives considered
- N/A.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_integration.py`

### Procedure
Add tests: a retained unconfirmed record is visible end to end (`list_processes()` and the status service), and a repeated `shutdown_all` re-terminates retained records.

### Method
Extend the existing integration module, which already exercises shutdown paths and the lifecycle logger (`:795`, `:1371-1410`).

### Details
- Use the real-process fixtures already in the module; assert the retained record's pid, pgid, and outcome reach the status service (AC-1).

## Compatibility considerations
- N/A: test-only.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_integration.py` — green after Phases 3-5 (AC-1).

## Completion criteria
- Unconfirmed visibility and repeated-shutdown behavior are pinned end to end.

## Out of Scope
- The implementation changes (rows 03, 04, 09, 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Tests first, expected to fail until Phases 3-5 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Test row: validation is the pytest run |

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
- **Requirement ID**: REQ-009, REQ-010, REQ-011 (defect-pinning tests first)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `tests/agent/test_http_lifecycle_integration.py`
