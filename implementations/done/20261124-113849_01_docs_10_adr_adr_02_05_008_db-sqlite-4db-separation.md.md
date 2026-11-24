## Goal
Rename the ADR-008 file to match its six-store title, with no content change (REQ-001).

## Scope
**Release unit**: adr008-rename

- Edits only `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`; part of the single rename commit, because a renamed file with an unupdated reference fails the reference, link, and ceiling checks.

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
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Run `git mv docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md` and record the new path as `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md` (new).
2. Do not edit the ADR text, front matter, or approval bullets.
3. Verify the content is identical: `git diff --cached -M --stat` shows a rename with no content change.

### Method
- Use `git mv` only; do not copy and delete.

### Details
- The ADR id stays 008 because `ADR_FILE_RE` reads the number from the name.
- This is the only procedure that names the new path in backticks, so the later procedures resolve it from this sibling.

## Compatibility considerations
N/A: a path or name change only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_authority.py` (they pass only once all procedures of the release unit are applied); `uv run python tools/check_adr_preservation.py --base HEAD docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md` for the pre-rename base (findings are read as rename effects).
- `uv run python tools/check_docs_quality.py` for document targets.

## Completion criteria
- The new file exists, the old file does not, `git log --follow` shows the history, and the text is unchanged.

## Out of Scope
- Any other file, any content edit, archived issues, plans, and procedures, and the two status baseline files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change per Implementation | Completed | — | 20261124-122205 | 1: changed: docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md -> docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md (git mv, rename, 0 content changes) |
| 2 | Run the checkers per Validation plan | Completed | 20261124-122205 | 20261124-130311 | end-of-unit run Pass: adr_structure/adr_authority/adr_reference/adr_invariant_matrix/known_deviation_sync/docs_structure/docs_quality/content_policy; docs_consistency domain Pass; full suite green after live-approved pin-test fix (76->75); run_cited_adr_tests 75/75 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261124-112759_adrren001_rename-adr-008-file.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-113352_adrren001_rename-adr-008-file.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-113849
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
