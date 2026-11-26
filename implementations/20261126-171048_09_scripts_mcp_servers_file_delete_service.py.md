## Goal
- Run the allowed-root guard before the dry-run branch with shared validation for dry-run and real deletion (REQ-004, dry-run parity), and write the intent audit before the destructive operation with fail-closed behavior plus `applied_audit_failed` reporting (REQ-005, audit order).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `delete_file` (line 131) and `delete_directory` (line 211) flow reordering, intent-audit-before-delete with fail-closed, the `applied_audit_failed` outcome via the shared vocabulary, and the test updates in the companion.
- Out of scope: the server-layer audit-record identifiers (seq 10).

## Assumptions
- Verified in Step 3a: in `scripts/mcp_servers/file/delete_service.py`, the dry-run return at lines 219-220 precedes `_check_not_deleting_allowed_root` at line 224 in `delete_directory`; `delete_file` has no allowed-root guard at all (file deletes are guarded only by `_resolve_safe`); audit is written only after deletion at line 153.
- The `applied_audit_failed` outcome comes from the shared vocabulary in `scripts/shared/write_outcome.py` (`APPLIED_AUDIT_FAILED`).
- Fail closed means an intent-audit write failure aborts the operation before the destructive call; the completion audit failure after an applied delete does not undo the delete but changes the reported outcome to `applied_audit_failed`.

## Design decisions
- Intent audit is written before `unlink()`/`rmtree()`/`rmdir()`; if the intent-audit write raises, the operation is refused (fail closed) rather than executed without a record (REQ-005).
- The completion audit stays after the destructive call; its failure maps the response outcome to `APPLIED_AUDIT_FAILED` from `scripts/shared/write_outcome.py` instead of being logged and swallowed.
- Dry-run and real deletion share one validation path: `_resolve_safe`, `_require_dir`, and the allowed-root guard run before the dry-run branch in both `delete_file` and `delete_directory` (REQ-004).

## Alternatives considered
- Best-effort intent audit — rejected: REQ-005 requires fail-closed before a destructive operation.

## Implementation
### Target file
`scripts/mcp_servers/file/delete_service.py`

### Procedure
1. In `delete_directory`, move `_check_not_deleting_allowed_root(target)` before the `if req.dry_run:` branch (line 219).
2. Apply the allowed-root guard to `delete_file` through the same shared path before its dry-run branch (line 135).
3. Write the intent audit before the destructive call in both methods; raise `FileAuthorizationError` (or the existing audit-failure error path) when the intent audit fails.
4. Map completion-audit failures after an applied delete to the `applied_audit_failed` outcome; dry-run responses keep no audit record.

### Method
- Existing response models gain no new fields; the outcome is reported through the existing response shape per the shared write-outcome vocabulary.

### Details
- Audit line format is unchanged for existing consumers; only the write order and failure handling change.

### Companion test files
- `tests/mcp_servers/file/test_delete_service.py`
  - Procedure: extend the existing audit tests at lines 62-68 with dry-run-vs-real authorization parity and audit fault-injection cases (audit permission, read-only filesystem, disk-full).
  - Validation: intent-audit failure aborts the operation; completion-audit failure yields `applied_audit_failed`; dry-run against an allowed root is refused.

## Compatibility considerations
- Dry-run calls against an allowed root now fail instead of returning a scan result (REQ-004 behavior change, recorded in the Plan).
- Callers that previously received a success response when the audit log was unwritable now receive `applied_audit_failed` (REQ-005).

## Security considerations
- Fail-closed intent audit closes the gap where a destructive operation succeeds with no audit record (Plan Problem analysis).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Companion tests: dry-run against an allowed root is refused; intent audit precedes the destructive call; intent-audit failure aborts the operation; completion-audit failure yields `applied_audit_failed`.
- `uv run pytest tests/mcp_servers/file/test_delete_service.py -v`; full `rules/toolchain.md` sequence.

## Completion criteria
- Allowed-root guard precedes every dry-run branch; intent audit is written before the destructive call and fails closed; completion-audit failure reports `applied_audit_failed`; tests pass (AC-3, AC-4).

## Out of Scope
- Server-layer audit-record identifiers (seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (dry-run parity with the allowed-root guard), `REQ-005` (intent audit fail-closed, `applied_audit_failed`)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/delete_service.py`, `tests/mcp_servers/file/test_delete_service.py`
