# Implementation Procedure — `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`

## Goal

Document file-write, file-delete, and shell's current five-layer coverage (implemented vs.
not applicable) (`REQ-006`).

## Scope

Modify only `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`. Add or update a
per-category statement of which of the five Layered protection layers (Agent approval,
Common guard, Command-specific guard, Postcondition verification, Audit) are implemented
vs. not applicable for each of the three tools.

## Assumptions

- This doc already exists and describes these three tools.
- Documentation is written after the code changes in rows 1–6 are implemented (Phase 6),
  so it reflects the resolved coverage.

## Design decisions

- State each layer per tool as implemented or not-applicable, with a one-line justification
  grounded in the actual code (e.g. file-write audit now present; shell audit extended).

## Alternatives considered

- Appending to a single shared test module across servers: rejected — each
  server owns its existing test file and fixtures; keeping tests co-located
  preserves coverage locality and reuse.

## Implementation

### Target file

`docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`

### Procedure

1. After rows 1–3 are implemented, record each tool's five-layer coverage.
2. For each tool, list the five layers and mark implemented / not-applicable with a short
   reason.
3. Note file-write's new audit record (REQ-005) and shell's extended audit (REQ-004).

### Method

- Edit the relevant section(s) in place; do not restructure the doc.

### Details

- Be precise: distinguish "not implemented but intended" from "formally not applicable".

## Compatibility considerations

N/A: documentation change.

## Security considerations

Do not expose sensitive implementation details beyond what the policy already describes.

## Rollback considerations

Revert the commit to the doc.

## Validation plan

- Documentation-consistency check (`governance_04_documentation-checks.md`, GV-022 family)
  passes.

## Completion criteria

The doc states each of file-write, file-delete, and shell's five-layer coverage as
implemented or not applicable.

## Out of scope

Other tool docs, the audit schema doc, code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document five-layer coverage for file-write/delete/shell | Completed | 2026-10-17 | 2026-10-17 | documented current (not resolved) state per user decision |
| 2 | Add or update tests per Validation plan | N/A (docs-only) | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | docs consistency check (--domain mcp) passed, no issues |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-17 | 2026-10-17 | this doc |

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
- **Requirement ID**: `REQ-006` (document each tool's five-layer coverage)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`
