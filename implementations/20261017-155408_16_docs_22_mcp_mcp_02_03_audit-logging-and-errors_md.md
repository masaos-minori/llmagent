# Implementation Procedure — `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

## Goal

Define the before/after state and approval-correlation fields in the shared audit record
schema (`REQ-004`, `REQ-005`).

## Scope

Modify only `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`. Extend the audit record
schema to specify before/after state fields and an approval-correlation field, and note the
per-server differences (file servers logged-never-raised; github raises
`GitHubAuditError`; file-write now emits a record).

## Assumptions

- This doc defines the canonical audit schema that rows 1–5 implement against.
- The existing schema has `{ts} op={op} {fields}` style records without before/after or
  correlation.

## Design decisions

- Add explicit field definitions for before-state, after-state, and approval-correlation,
  stating they are identifiers only (never full content/secrets).
- Document the failure-handling variants per server without over-constraining them.

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

### Procedure

1. Add the before/after state fields to the audit record schema with their allowed
   contents (identifiers only).
2. Add the approval-correlation field definition.
3. Note which servers emit/extend these fields (rows 1–5) and their failure handling.

### Method

- Edit the schema section in place; keep the doc consistent with `routing.md` doc
  structure.

### Details

- Keep field names stable across servers where feasible so consumers can parse them.

## Compatibility considerations

The schema change drives the format rows 1–5 produce; coordinate field names so all
servers align. This doc is the single source of truth for the format.

## Security considerations

Explicitly forbid logging file contents, secrets, or full sensitive output in any audit
field.

## Rollback considerations

Revert the commit to the doc.

## Validation plan

- Documentation-consistency check (`governance_04_documentation-checks.md`) passes.

## Completion criteria

The audit schema defines before/after state and approval-correlation fields.

## Out of scope

Server code (separate rows), other docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define before/after + correlation fields in audit schema | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A (docs-only) | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs consistency check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | — | — | this doc |

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
- **Requirement ID**: `REQ-004` (audit before/after + correlation); `REQ-005` (file-write
  audit schema)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`
