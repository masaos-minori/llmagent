## Goal

Update invalid `related` reference in `docs/adr/ADR-008-sqlite-4db-separation.md` from `ADR-002` to correct filename and fix broken links per REQ-002.

## Scope

Modify only `docs/adr/ADR-008-sqlite-4db-separation.md` to fix one invalid cross-reference in its YAML Front Matter and address broken links.

## Assumptions

- The file exists and has Front Matter with an invalid `related` field pointing to `ADR-002` (confirmed by git history inspection)
- Broken links exist in the document body that also need fixing
- One `related` reference needs correction in this file

## Design decisions

- Replace the invalid reference with its actual filename found via git history
- Fix broken links identified during the process
- Keep the same YAML structure — only modify values, not keys
- Use git history as the source of truth for renamed/deleted files

## Alternatives considered

- Removing the reference: rejected because the Plan states to use git history to find renamed files and update references accordingly
- Keeping the old reference: rejected because it violates REQ-002

## Implementation

### Target file

`docs/adr/ADR-008-sqlite-4db-separation.md`

### Procedure

1. Read the current Front Matter of `docs/adr/ADR-008-sqlite-4db-separation.md`
2. Locate the `related` field containing `ADR-002`
3. Replace it with the correct filename from git history
4. Identify broken links in the document body
5. Fix broken links by updating paths to existing files

### Method

String replacements within the YAML Front Matter block and document body — replace invalid references with actual filenames.

### Details

Current state (approximate):
```yaml
---
title: "SQLite 4DB Separation"
area: adr
tags: []
related:
  - ADR-002
status: draft
---

# SQLite 4DB Separation

...broken link to non-existent file...
```

After modification:
```yaml
---
title: "SQLite 4DB Separation"
area: adr
tags: []
related:
  - <corrected-filename-for-ADR-002>
status: draft
---

# SQLite 4DB Separation

...fixed link to existing file...
```

Steps:
1. Run `git log --all --diff-filter=D -- "**/ADR-002*.md"` to find the actual filename for ADR-002
2. Replace `- ADR-002` with the actual filename in the Front Matter
3. Scan the document body for broken links (links to non-existent files)
4. Update broken links to point to existing files where possible
5. Verify the YAML indentation and syntax remain valid

## Compatibility considerations

- Changing a cross-reference does not alter document content
- The new filename resolves to an existing file in the repository
- Fixing broken links improves document navigability without changing meaning
- This aligns with Plan's Approach: "use git history to find renamed/deleted files, update or remove references accordingly"

## Security considerations

No security impact — updating cross-references and fixing links does not affect access control or authentication.

## Rollback considerations

1. Revert the string replacements to restore original references
2. Revert broken link fixes to their original state
3. No data loss risk — changes are purely reference updates

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid cross-references and broken links.

## Completion criteria

- `related` entry contains corrected filename instead of `ADR-002`
- All broken links fixed to point to existing files
- YAML syntax remains valid
- Cross-reference resolves to an existing file in the repository
- No other fields modified

## Out of scope

- Modifying any other file
- Determining whether additional references should be added or removed

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/adr/ADR-008-sqlite-4db-separation.md
