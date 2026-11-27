# Implementation Procedure — docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md

## Goal

Record the four log limits, the redirect policy and trusted hosts, and the complete, partial, and error
result contract in the CI/CD server section.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-007 (documentation records the limits, the redirect policy, and the result
contract). Acceptance criterion: AC-5.

## Assumptions
- Line 63 currently states only that log retrieval is bounded by a job count limit and a total size
  limit (`max_log_size_kb`) (re-verified 20261127).
- The credential, permission, allowlist, and terminology passages in the same section are the mcpci001
  pass's work, and the dispatch-state paragraphs are the mcpci002 pass's work; this document changes the
  log-retrieval paragraph only (Plan Assumptions, compatible overlap).
- Per the mcpci001 plan's Assumptions, run the mcpai012 CI/CD consistency sweep after these rows land,
  otherwise the sweep rewrites the section against the pre-change source.

## Design decisions
- N/A: documentation-only change.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure
- State the four limits: raw download, decompressed, selected job, and returned output.
- State the redirect policy: the maximum redirect count and the trusted GitHub log hosts, and that
  redirects outside the trusted hosts are rejected.
- State the result contract: per-job status, included bytes, error code, and truncation state;
  partial_success for a mixed result; a tool error when every job fails; totals.

### Method
- Update the log-retrieval passage at line 63 in place; keep the cross-reference to
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
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` (per
  `rules/tool-gates.md`).

## Completion criteria
- The section states the four limits, the redirect policy and trusted hosts, and the complete, partial,
  and error result contract (AC-5); the doc checkers report no finding.

## Out of Scope
- The credential and allowlist paragraphs (mcpci001's row) and the dispatch-state paragraphs (mcpci002's
  row) in the same file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | log limits, redirect policy and trusted hosts, and the complete/partial/error contract recorded; the cross-reference to mcp_05_01 was absent from the file and was added |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | — | — | check_docs_structure, check_docs_quality, check_docs_consistency --domain mcp clean |

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
- **Requirement ID**: REQ-007 (CI/CD log streaming documentation)
- **Source issue**: issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-065519_mcpci003_cicd-log-streaming-bounds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-151141
- **Related target files**: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`