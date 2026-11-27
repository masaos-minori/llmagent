# Implementation Procedure — docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md

## Goal

Record the five dispatch states, the correlation and polling strategy, and why automatic retry stays
disabled, and remove the statement that a dispatch response proves run creation.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-010 equivalent for this Plan — REQ-008 (documentation records the states,
correlation, polling, and the retry rationale). Acceptance criterion: AC-6.

## Assumptions
- Line 73 currently states postcondition verification is not applicable because the server "returns a
  confirmation rather than a resulting state to compare" (re-verified 20261127); that statement is the
  one REQ-008 removes.
- The credential, permission, allowlist, and terminology passages in the same section are the mcpci001
  pass's work on this file (compatible overlap); this document changes the dispatch-state paragraphs only.

## Design decisions
- N/A: documentation-only change.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure
- State the five dispatch states (accepted, confirmed, accepted_unconfirmed, `outcome_unknown`,
  reconciliation_required) and that a 2xx response never becomes confirmed without a matched run.
- State the correlation strategy: the marker in the workflow inputs when the workflow contract allows
  it, otherwise the fallback correlation on workflow identifier, ref, actor, and dispatch time, recorded
  as a digest.
- State the bounded polling and that the same logical call is searched for an existing run before a
  repeat dispatch.
- State why automatic retry stays disabled: accepted_unconfirmed and `outcome_unknown` are never
  retried automatically, and `trigger_workflow` is declared non-retryable.
- Replace the line 73 postcondition statement with the reconciled-state description.

### Method
- Update the cicd-mcp section in place; keep the cross-reference to
  `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`.

### Details
- N/A.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Structure check: `uv run python tools/check_docs_structure.py`.
- Per `rules/tool-gates.md`, run the documentation checkers after the change.

## Completion criteria
- The section records the five states, the correlation and polling strategy, and the retry rationale,
  and contains no statement that a dispatch response proves run creation (AC-6); the checkers report no
  finding.

## Out of Scope
- The credential and allowlist paragraphs (mcpci001's row for the same file).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-008 (CI/CD dispatch documentation)
- **Source issue**: issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-005001_mcpci002_cicd-dispatch-reconciliation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-150154
- **Related target files**: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`
