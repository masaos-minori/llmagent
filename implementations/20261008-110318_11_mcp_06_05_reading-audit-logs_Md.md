# Implementation Procedure: Update MCP audit log reading documentation

## Goal

Document record fields + audit-failure counter in `docs/22_mcp/mcp_06_05_reading-audit-logs.md` (REQ-010). Document new `/health` counter and record shape.

## Scope

- Modify `docs/22_mcp/mcp_06_05_reading-audit-logs.md`:
  - Lines 48, 63, 93: update record fields and add audit-failure counter documentation.

## Assumptions

- The audit log reading documentation currently documents the old record shape without `canonical_target`.
- The `/health` endpoint does not currently document an audit-failure counter.

## Design decisions

- **Record fields**: Add `canonical_target` field documentation.
- **Audit-failure counter**: Add documentation for the per-process audit-failure counter exposed in `/health` details.
- **Outcome values**: Update outcome vocabulary to `"ok"`/`"error"`/`"rejected"`.

## Alternatives considered

- Creating a separate section for the audit-failure counter: rejected because the plan requires adding it to the existing documentation.

## Implementation
### Target file
`docs/22_mcp/mcp_06_05_reading-audit-logs.md`

### Procedure
1. Document record fields + audit-failure counter (REQ-010).

### Method
Edit `docs/22_mcp/mcp_06_05_reading-audit-logs.md`:
- Lines 48, 63, 93: Update record fields and add audit-failure counter documentation.
- Add `canonical_target` field documentation.
- Add documentation for per-process audit-failure counter exposed in `/health` details.
- Update outcome vocabulary to `"ok"`/`"error"`/`"rejected"`.

### Details
- The audit log reading documentation currently documents the old record shape without `canonical_target`.
- The `/health` endpoint does not currently document an audit-failure counter.

## Compatibility considerations

- This is a documentation-only change; no code or configuration impact.

## Security considerations

- No security impact: this is a documentation update.

## Rollback considerations

- Revert the documentation changes — acceptable because they are simple text edits.

## Validation plan

- **Manual review**: Confirm the documentation accurately reflects the new record shape and counter.
- **Documentation consistency**: `uv run python tools/check_docs_consistency.py --domain mcp` — confirm clean.

## Completion criteria

- Record fields include `canonical_target`.
- Audit-failure counter documented in `/health` details.
- Outcome vocabulary updated to `"ok"`/`"error"`/`"rejected"`.
- No `"success"` string remains in the audit section.

## Out of scope

- Modifying `ADR-012-git-mcp-server-side-write-enforcement.md` (covered in its own document).
- Modifying `mcp_04_05_git.md` (covered in its own document).
- Modifying `governance_03_issue-and-uncertainty-management.md` (covered in its own document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update record fields + audit-failure counter docs (`docs/22_mcp/mcp_06_05_reading-audit-logs.md`) | Pending | — | — | REQ-010 |
| 2 | Run documentation consistency check | Pending | — | — | REQ-010 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20261007-153904_gitaudit01_fix-git-mcp-audit-records-and-policy-rejection-error-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261007-191952_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-110318
- **Related target files**: docs/22_mcp/mcp_06_05_reading-audit-logs.md
