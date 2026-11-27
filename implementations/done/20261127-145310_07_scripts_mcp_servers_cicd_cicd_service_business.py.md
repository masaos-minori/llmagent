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
- Wrap a form the canonicalizer rejects into `CicdAuthorizationError` at the handler entry, so the observable denial stays 403 (user decision, 20261127).

### Method
- `_parse_repo()` currently raises on a bad slug but does not normalize it, and `handle_trigger_workflow()` passes `req.workflow` unchanged to the guard and the backend (verified in Step 3a); add the canonicalization call at the entry of each handler that the guard tests pin.
- Step 3a verification (20261127): `handle_trigger_workflow()` runs `_assert_allowed_repo()` and `_assert_allowed_workflow()` before `_parse_repo()` (lines 70-71, 76), so canonicalization must happen at the handler entry, before both guards, not after the guard.
- Step 3a verification (20261127): `normalize_repo_key()` takes two arguments (`owner`, `repo`), not a slug (`scripts/shared/repo_identity.py:21`), so the handler must split the slug first and then canonicalize the parts. The shared insertion point that keeps canonicalization before the guard is `_validate_and_parse_repo()` (lines 50-53, used by the read handlers at lines 95, 114, 128) plus the trigger handler entry, since `handle_trigger_workflow()` calls `_parse_repo()` directly at line 76.
- Step 3a verification (20261127, exception shape): canonicalizing at handler entry puts the canonicalizer ahead of the guard, so a rejected form would raise `CicdValidationError` (HTTP 422 per `scripts/mcp_servers/exception_handlers.py`) instead of the pinned `CicdAuthorizationError` (403). User decision (20261127): keep 403, so the handler wraps the canonicalizer's `CicdValidationError` into `CicdAuthorizationError` through one helper (`_canonical_or_denied()`); the guard's denial policy stays the observable behavior for a tool call. Pinned by `test_rejected_form_is_denied_before_the_backend_call` and `test_invalid_repo_form_is_denied_before_the_backend_call`.
- Step 3a verification (20261127, scope): the read handlers do not call `_assert_allowed_workflow()`, so workflow canonicalization is added only to the trigger handler; the read handlers canonicalize the repository through `_validate_and_parse_repo()`. URL encoding stays in the `cicd_service_github_actions.py` row.
- Step 3a verification (20261127): `handle_trigger_workflow()`'s dry-run preview text is built from the canonical values, so a non-canonical request now shows the canonical form in the preview. Existing pins use already-canonical values and stay valid; the new case pins the canonical preview.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | canonicalization at handler entry; rejected form wrapped as CicdAuthorizationError to keep 403 (user decision 20261127) |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | end-of-batch full suite: 6 failures all matching tools/known_test_failures_baseline.txt; diff-cover 96% |
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