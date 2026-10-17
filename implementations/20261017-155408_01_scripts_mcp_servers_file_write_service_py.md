# Implementation Procedure — `scripts/mcp_servers/file/write_service.py`

## Goal

Give `file-write-mcp` an audit record. The write service currently emits no audit
entry; add one per mutating call capturing before/after state and approval correlation
(`REQ-004`, `REQ-005`).

## Scope

Modify only `scripts/mcp_servers/file/write_service.py`. Add an audit-log write on each
successful mutating write-service operation (`write_file`, `edit_file`, `create_directory`,
`move_file`), mirroring the sibling `delete_service.py` pattern. Do not touch
`delete_service.py`, `read_service.py`, or any other file.

## Assumptions

- An audit log path is available from config the same way `delete_service.py` reads it
  (`_audit_log_path`). Confirm the write-config exposes an equivalent key; if not, reuse
  the delete-service config field rather than inventing a new one.
- Approval for file-write is a server-checked gate (common-guard allowlist/denylist), so
  the audit record can correlate to the originating approved call.

## Design decisions

- Reuse the `delete_service.py` `_write_audit_log(op, path)` shape (append one line, log
  errors, never raise) so file-write stays consistent with the sibling server and the
  audit-failure-is-logged-never-raised risk mitigation.
- Extend the record with before/after state (target path + size/hash delta) rather than
  rewriting the format, so existing consumers are not broken.

## Alternatives considered

- Writing a brand-new audit schema for file-write alone: rejected — the shared schema in
  `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` (REQ-005) is the intended single
  format; a per-server format would drift.
- Emitting the audit record from the server/dispatch layer instead of the service:
  rejected — the service owns the before/after state and is the single choke point for
  every mutating call.

## Implementation

### Target file

`scripts/mcp_servers/file/write_service.py`

### Procedure

1. Add a `_write_audit_log(self, op, ...)` helper to `WriteFileService`, mirroring
   `delete_service.py`'s helper (append one line, catch `OSError`, log, never propagate).
2. At the end of each mutating method (`write_file`, `edit_file`, `create_directory`,
   `move_file`) after a successful result, call `_write_audit_log` with the operation name
   and before/after state (target path and a content delta such as size or hash).
3. Ensure the audit path is wired from config in `__init__` / `build_service`.

### Method

- Locate `WriteFileService` (class at line 43) and its mutating methods
  (`write_file` 122, `edit_file` 187, `create_directory` 208, `move_file` 231).
- Copy the append-only, never-raise contract from `delete_service.py:_write_audit_log`
  (line 76) and adapt the record string to the shared schema fields.
- Insert audit calls at the success return path of each mutating method.

### Details

- Record must include: timestamp (ISO8601), `op=<name>`, before-state (pre-write target
  existence/content), after-state (post-write target content), and approval correlation
  (the approved operation identity). Do not log file contents or sensitive values.
- Keep before/after as lightweight identifiers (path + size/hash), not full content.

## Compatibility considerations

Extending the audit record changes file-write's audit line format. Align the field set
with the schema defined in `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` (this
procedure does not modify that doc). Verify no consumer parses the old empty-format
shape; if one exists, extend rather than rewrite.

## Security considerations

- The audit record must not contain file contents, secrets, or full sensitive output
  (mirrors the Audit layer's "without secrets" rule in `security_02`).
- Audit failure must remain non-fatal (logged, never raised) so a failed audit write
  cannot break a legitimate write call.

## Rollback considerations

Revert the commit to `write_service.py`.

## Validation plan

- Unit: assert a newly written audit record is emitted for a successful write and
  contains before/after + correlation fields.
- Negative: assert a disallowed write (allowlist/denylist rejection) emits no success
  audit record (or an appropriately tagged one).
- Command: `uv run pytest tests/mcp_servers/file/ -q`.
- Docs: documentation-consistency check passes.

## Completion criteria

Every mutating write-service call writes exactly one audit record containing before/after
state and approval correlation, conforming to the shared schema, and audit failures do
not propagate.

## Out of scope

Any change to `delete_service.py`, read services, dispatch, or the audit schema doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the audit-record change in write_service.py | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: schema doc is a separate row |

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
- **Requirement ID**: `REQ-005` (file-write-mcp writes an audit record); `REQ-004` (audit
  captures before/after state and correlates to approval)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `scripts/mcp_servers/file/write_service.py`
