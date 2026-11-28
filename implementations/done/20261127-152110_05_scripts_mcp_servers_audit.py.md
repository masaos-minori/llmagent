# Implementation Procedure — scripts/mcp_servers/audit.py

## Goal

Remove the duplicate `requested_target` assignment and record the CI/CD error-code vocabulary in the
module docstring's Error Type Vocabulary section.

## Scope
**Release unit**: exactly-one audit event

Requirements implemented: REQ-008 (the duplicate assignment is removed), REQ-006 (the vocabulary section
names the CI/CD codes). Acceptance criteria: AC-6.

## Assumptions
- Lines 124-125 and 128-129 assign `record["requested_target"]` twice with the same value
  (re-verified 20261127), so the removal changes no observable output for the other eight servers and the
  Issue's stop-and-report condition is not triggered (Plan Assumption).
- The CI/CD vocabulary values are the frozenset defined by the `scripts/mcp_servers/cicd/cicd_models.py`
  row; this document names them in the docstring, it does not import them.
- `AuditEmission` (lines 236-296) is not modified; only the duplicate assignment and the docstring change.

## Design decisions
- The docstring's vocabulary section (lines 8-20) lists the mdq and web_search vocabularies today; the
  CI/CD entry is added as a third numbered vocabulary in the same style.

## Alternatives considered
- N/A: single-function change; the rejected alternative is adding a shared text-redaction helper here,
  which the Plan's Redaction home decision places in the CI/CD backend.

## Implementation
### Target file
`scripts/mcp_servers/audit.py`

### Procedure
- Delete the second `if requested_target:` block at lines 128-129.
- Add the CI/CD vocabulary to the Error Type Vocabulary section, naming the codes the models row defines.

### Method
- Keep the first assignment at lines 124-125 as the single source of the record field.
- Step 3b correction: the citations hold at revision da8097e74 (the duplicate block is at 128-129, the
  first assignment at 124-125). `AuditEmission` starts at line 238, not 236.
- Step 3b correction: the CI/CD entry names seven codes, including `unexpected_error`, and states that it
  has no `EXCEPTION_ERROR_CODES` entry because it names the audit category for a failure with no CI/CD
  exception class.

### Details
- N/A: no behavior change beyond the removed duplicate write.

## Compatibility considerations
- The record output for the other servers is unchanged (AC-6), which the reference test file pins.

## Security considerations
- N/A: no redaction behavior changes.

## Rollback considerations
- N/A: revert the commit (release unit: validated with the CI/CD server row).

## Validation plan
- Unit: shared helper behavior for all servers — `uv run pytest tests/mcp_servers/test_audit_redaction.py`
  (reference file, not modified).
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The duplicate assignment is gone and the record output for the other servers is unchanged (AC-6); the
  docstring names the CI/CD vocabulary (REQ-006).

## Out of Scope
- The CI/CD emission itself (`scripts/mcp_servers/cicd/cicd_server.py` row); the vocabulary definition
  (`scripts/mcp_servers/cicd/cicd_models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | duplicate `if requested_target:` block deleted; CI/CD vocabulary added as the third numbered entry, naming the seven codes and the no-mapping note for `unexpected_error` |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128 | 20261128 | `uv run pytest tests/mcp_servers/test_audit_redaction.py` passes (33); gates all Pass |

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
- **Requirement ID**: REQ-006, REQ-008 (duplicate requested_target removal, CI/CD vocabulary record)
- **Source issue**: issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-070305_mcpci004_cicd-error-audit-coverage.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152110
- **Related target files**: `scripts/mcp_servers/audit.py`
