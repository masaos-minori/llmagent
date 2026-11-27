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
- Step 3a verification (20261127): `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` contains no URL assertion, so it cannot pin the encoding by itself. The only existing URL pin is `tests/mcp_servers/cicd/test_cicd_mcp_service.py:352`, which asserts the substring for a canonical value and stays valid because `quote(..., safe="")` leaves a canonical file name unchanged. The encoding case is therefore added to the companion file named in the Validation plan.
- Step 3a verification (20261127, contradiction): Execution Status row 2 says the covering test is "a reference file, not a modification target", while this document's Companion test files section and the Plan's frozen target table (`plans/done/20261126-152931_mcpci001_cicd-credential-config-contract.md` line 66) name the same file as the companion to add the URL case to. The Companion section is taken as authoritative; the file was modified and the row-2 note corrected.
- Step 3a verification (20261127): the backend receives the canonical value from the handler (procedure seq 07), so `quote()` is defense-in-depth at the URL construction point; the added case pins the encoding through the backend directly, which is the layer this row owns.

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

### Companion test files
- `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`
  - Procedure: add the URL path-segment case — a workflow value containing a separator or a percent-encoded segment is encoded as one segment in the dispatch URL; a canonical file name encodes unchanged.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — | the covering test is a reference file, not a modification target row 2's reference-file note is superseded: the companion file is the modification target per the Plan's frozen table; URL path-segment case added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | end-of-batch full suite: 6 failures all matching the baseline; diff-cover 96% |
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