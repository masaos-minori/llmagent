# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_github_actions.py

## Goal

Encode the canonical workflow identifier as one URL path segment so separators and unsafe encoding cannot alter the dispatch path.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-005 (URL-encoded as one path segment). Acceptance criterion: AC-4.

## Assumptions
- The canonical value is produced by `canonical_workflow_id()` in the `cicd_models.py` row; this document only encodes it.

## Design decisions
- `urllib.parse.quote(value, safe="")` per Plan D5, applied at the URL construction point.

## Alternatives considered
- N/A: single-function change; no alternative was considered by the Plan.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_github_actions.py`

### Procedure
- At line 111, replace the raw f-string interpolation of `workflow` in the dispatch URL with `urllib.parse.quote(workflow, safe="")`.

### Method
- The current URL is `f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"` with no quoting (verified in Step 3a); quote only the workflow segment, keep `owner`/`repo` as produced by `_parse_repo()`.

### Details
- N/A: no other behavior in this file changes.

## Compatibility considerations
- Canonical values that contain no separators encode to the same string as today.

## Security considerations
- Path-segment injection through the workflow value is prevented (AC-4).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit: URL path segment encoding — `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` (reference file, not modified).
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Separators and unsafe encoding cannot alter the path (AC-4); the error-edge tests still pass.

## Out of Scope
- Canonicalization itself (`cicd_models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | the covering test is a reference file, not a modification target |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs rows |

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
- **Requirement ID**: REQ-005 (canonical identifier encoded as one URL path segment)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_github_actions.py`
