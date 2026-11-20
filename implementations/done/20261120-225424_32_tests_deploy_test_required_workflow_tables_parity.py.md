## Goal

Keep the workflow-table parity pins consistent with the changed `tool_call_state` DDL (`REQ-005` DDL pin, `REQ-010` deploy verification).

## Scope
**Release unit**: N/A: cited only by Plan step 6 (deployment), which is outside both Release units.

## Assumptions
- The parity list names tables, not columns; the expected DDL text this test pins comes from `scripts/db/schema_sql.py` (row 12).

## Design decisions
- Update any pinned `tool_call_state` DDL/checksum/shape expectation to the new nine-state `CHECK` text.
- Keep the parity assertion itself unchanged (table inventory is unchanged).

## Alternatives considered
- N/A: test-only mirror of row 12.

## Implementation
### Target file
`tests/deploy/test_required_workflow_tables_parity.py`

### Procedure
Refresh the DDL-shape expectations against the new canonical text after row 12 lands (Plan step 6).

### Method
Run the test, adopt the new canonical shape, and confirm `tools/check_db_separation.py` still passes.

### Details
- If the test embeds a DDL copy, replace it verbatim with the row 12 output rather than paraphrasing.

## Compatibility considerations
No deploy.sh file change (Plan step 6: deploy note validated, runbook applies).

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit together with row 12.

## Validation plan
`uv run pytest tests/deploy/test_required_workflow_tables_parity.py && uv run python tools/check_db_separation.py`.

## Completion criteria
Parity, separation check, and the canonical DDL all agree on the new table shape.

## Out of Scope
The DDL itself (row 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | No file change needed: the parity test expresses parity directly against the canonical DDL fingerprint (`build_workflow_schema_sql()` → `schema_fingerprint`), with no embedded DDL copy or checksum — row 12's nine-state `CHECK` text is adopted automatically. Verified, not assumed. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | `uv run pytest tests/deploy/test_required_workflow_tables_parity.py`: 5 passed (in the combined run with row 24: 57 passed); `uv run python tools/check_db_separation.py`: "No violations found". |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-11-21 | N/A: test-only |

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
- **Requirement ID**: `REQ-005`, `REQ-010`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `tests/deploy/test_required_workflow_tables_parity.py`
