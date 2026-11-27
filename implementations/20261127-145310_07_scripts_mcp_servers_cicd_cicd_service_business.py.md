# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_business.py

## Goal

Canonicalize the request workflow identifier before the guard and the backend call, so the guard and the URL see the same canonical value.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-005 (the workflow identifier is canonicalized by one function). Acceptance criterion: AC-4.

## Assumptions
- The canonicalization function is defined in the `cicd_models.py` row and imported here; this document does not define it.

## Design decisions
- Canonicalization happens once at the dispatch entry, before the guard, so the guard comparison and the backend call cannot diverge.

## Alternatives considered
- Canonicalizing inside the guard only: rejected per REQ-005 — the backend URL must receive the same canonical value.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_business.py`

### Procedure
- In `handle_trigger_workflow()`, canonicalize `req.workflow` through `canonical_workflow_id()` from `scripts/mcp_servers/cicd/cicd_models.py` before the guard check and the backend call.
- Canonicalize the repository value through `normalize_repo_key()` before `_parse_repo()` matching.

### Method
- `_parse_repo()` currently raises on a bad slug but does not normalize it, and `handle_trigger_workflow()` passes `req.workflow` unchanged to the guard and the backend (verified in Step 3a); add the canonicalization call at the entry of each handler that the guard tests pin.

### Details
- Newly rejected inputs (blank `workflow`, separators, percent-encoding) are listed in the Plan's change record.

## Compatibility considerations
- Values that are already canonical are unchanged.

## Security considerations
- N/A: the rejection policy lives in the models and guards rows.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit: canonicalization before guard and backend — `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py` (companion).
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Request and allowlist values canonicalize identically through the same function (AC-4); the existing guard cases (`ci.yml`, `deploy.yml`, `../ci.yml`, `..\ci.yml`) still behave as pinned.

## Out of Scope
- URL path encoding (`cicd_service_github_actions.py` row).

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_mcp_service.py`
  - Procedure: add canonicalization cases to the guard tests that pin raw-string matching (lines 131-173): file name, numeric id, path separator, percent-encoding, wildcard, duplicate, blank, and invalid repository forms.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion test file) | Pending | — | — | |
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
- **Requirement ID**: REQ-005 (canonical workflow identifier at call time)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_business.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`
