## Goal
Replace the old ADR-008 file name with the new one in this document (one Markdown link) (REQ-002).

## Scope
**Release unit**: adr008-rename

- Edits only `docs/90_deployment/deployment_01_deployment.md`; part of the single rename commit, because a renamed file with an unupdated reference fails the reference, link, and ceiling checks.

## Assumptions
- The rename and all reference updates land in one commit; the rename procedure (seq 01) runs first, so after it the old file name no longer exists.
- This procedure names the old and the new file name as plain text (not in backticks) so the stale check does not look for a file that the rename has moved; the new path is declared `(new)` once, in the rename procedure.
- Only the old-name references listed in Procedure change; no other text of the file is edited, and no archived issue, plan, or procedure is touched.

## Design decisions
- A pure name replacement; no wording, order, or format change.

## Alternatives considered
N/A: mechanical rename; the Plan fixes the approach.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. Replace every occurrence of adr_02_05_008_db-sqlite-4db-separation.md with adr_02_05_008_db-six-sqlite-store-separation.md (one Markdown link; lines 288).
2. Change nothing else in the file.

### Method
- Use the Edit tool with exact strings, or `sed -i` limited to this file; confirm with `rg -n "db-sqlite-4db-separation" docs/90_deployment/deployment_01_deployment.md` that no match remains afterwards.

### Details
- Front matter `related` entries are file names without a directory; Markdown links use the relative path `../10_adr/<name>`; keep each form's shape and replace only the name.

## Compatibility considerations
N/A: a path or name change only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_docs_consistency.py --domain deployment`.
- `uv run python tools/check_docs_quality.py` for document targets.

## Completion criteria
- `rg -c "db-sqlite-4db-separation" docs/90_deployment/deployment_01_deployment.md` reports no match; front matter `related` entries and links resolve.

## Out of Scope
- Any other file, any content edit, archived issues, plans, and procedures, and the two status baseline files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change per Implementation | Completed | — | 20261124-123348 | 1: changed: docs/90_deployment/deployment_01_deployment.md (1 replacement, line 288) |
| 2 | Run the checkers per Validation plan | Completed | 20261124-123348 | 20261124-130311 | end-of-unit run Pass: adr_structure/adr_authority/adr_reference/adr_invariant_matrix/known_deviation_sync/docs_structure/docs_quality/content_policy; docs_consistency domain Pass; full suite green after live-approved pin-test fix (76->75); run_cited_adr_tests 75/75 |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261124-112759_adrren001_rename-adr-008-file.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-113352_adrren001_rename-adr-008-file.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-113849
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`
