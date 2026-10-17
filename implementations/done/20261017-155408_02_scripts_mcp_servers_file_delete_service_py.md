# Implementation Procedure — `scripts/mcp_servers/file/delete_service.py`

## Goal

Extend the existing `file-delete-mcp` audit record to carry before/after state and
approval correlation (`REQ-004`), and assess whether a postcondition check is needed
(`REQ-003`).

## Scope

Modify only `scripts/mcp_servers/file/delete_service.py`. Extend `_write_audit_log` and
its call sites to include before/after state and approval correlation. Assess postcondition
need; if a gap exists, add a minimal check, otherwise document it as not applicable.

## Assumptions

- `_write_audit_log(self, op, path)` exists at line 76 with format
  `{ts} op={op} path={path} user=llm-agent`; extend rather than rewrite.
- Deletion is a server-checked operation, so approval correlation applies.

## Design decisions

- Extend the record string with before/after identifiers (target existence + size before;
  existence after) rather than changing the leading `{ts} op=` prefix, preserving any
  consumers keyed on that shape.
- Postcondition for delete is naturally "the target no longer exists"; evaluate whether
  the existing dry-run/stat already guarantees this without a separate postcondition hook.

## Alternatives considered

- Adding a separate audit method: rejected — reuse the single existing `_write_audit_log`
  so all delete audit lines share one format.
- Full postcondition verification like git: rejected — delete has no mutable post-state to
  verify beyond non-existence, which the operation itself guarantees.

## Implementation

### Target file

`scripts/mcp_servers/file/delete_service.py`

### Procedure

1. Extend `_write_audit_log` (line 76) to accept and serialize before/after state and an
   approval-correlation field, appending them to the existing record line.
2. At both call sites (`delete_file` line 122, `delete_directory` line 199), compute the
   before-state (existence + size) and after-state (non-existence) and pass them.
3. If a postcondition assessment finds no gap, leave `delete_service.py` as-is for that
   layer and note it in the tool doc (separate row).

### Method

- Read `_write_audit_log` (76–91) and its two callers (122, 199).
- Add before/after fields to the `record` f-string; keep the leading prefix intact.

### Details

- Before-state: target path + size (or dry-run stat summary for directories).
- After-state: confirmation the target no longer exists.
- Approval correlation: the approved operation identity already in scope for the call.
- Do not log sensitive content.

## Compatibility considerations

The audit line gains trailing fields; leading `{ts} op={op}` prefix is unchanged. Confirm
no consumer requires an exact-line match; align field names with
`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` (that doc is a separate row).

## Security considerations

Before/after must be identifiers only (size/existence), never file contents. Audit
failure stays logged-never-raised (existing contract preserved).

## Rollback considerations

Revert the commit to `delete_service.py`.

## Validation plan

- Assert the audit record for a delete contains before/after + correlation fields.
- Regression: legitimate deletes still succeed and produce a well-formed record.
- Command: `uv run pytest tests/mcp_servers/file/ -q`.

## Completion criteria

Every delete writes an audit record with before/after state and approval correlation;
legitimate-delete semantics are unchanged.

## Out of scope

Any other server, the audit schema doc, and postcondition logic if assessed as not
applicable.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the audit record in delete_service.py | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: tool doc is a separate row |

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
- **Requirement ID**: `REQ-004` (audit before/after + correlation); `REQ-003` (postcondition
  assessment)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `scripts/mcp_servers/file/delete_service.py`
