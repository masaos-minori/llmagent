## Goal

Update invalid `related` reference in `docs/adr/ADR-009-rag-ft5-text-separation.md` from `ADR-002` to correct filename per REQ-002.

## Scope

Modify only `docs/adr/ADR-009-rag-ft5-text-separation.md` to fix one invalid cross-reference in its YAML Front Matter.

## Assumptions

- The file exists and has Front Matter with an invalid `related` field pointing to `ADR-002` (confirmed by git history inspection)
- One `related` reference needs correction in this file

## Design decisions

- Replace the invalid reference with its actual filename found via git history
- Keep the same YAML structure — only modify values, not keys
- Use git history as the source of truth for renamed/deleted files

## Alternatives considered

- Removing the reference: rejected because the Plan states to use git history to find renamed files and update references accordingly
- Keeping the old reference: rejected because it violates REQ-002

## Implementation

### Target file

`docs/adr/ADR-009-rag-ft5-text-separation.md`

### Procedure

1. Read the current Front Matter of `docs/adr/ADR-009-rag-ft5-text-separation.md`
2. Locate the `related` field containing `ADR-002`
3. Replace it with the correct filename from git history
4. Verify YAML syntax is correct after modification

### Method

String replacement within the YAML Front Matter block — replace the exact substring `ADR-002` with the actual filename.

### Details

Current state (approximate):
```yaml
---
title: "RAG FT5 Text Separation"
area: adr
tags: []
related:
  - ADR-002
status: draft
---
```

After modification:
```yaml
---
title: "RAG FT5 Text Separation"
area: adr
tags: []
related:
  - <corrected-filename-for-ADR-002>
status: draft
---
```

Steps:
1. Run `git log --all --diff-filter=D -- "**/ADR-002*.md"` to find the actual filename for ADR-002
2. Replace `- ADR-002` with the actual filename
3. Verify the YAML indentation and syntax remain valid

## Compatibility considerations

- Changing a cross-reference does not alter document content
- The new filename resolves to an existing file in the repository
- This aligns with Plan's Approach: "use git history to find renamed/deleted files, update or remove references accordingly"

## Security considerations

No security impact — updating a cross-reference does not affect access control or authentication.

## Rollback considerations

1. Revert the string replacement to restore original reference
2. No data loss risk — the change is purely a reference update

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid cross-references.

## Completion criteria

- `related` entry contains corrected filename instead of `ADR-002`
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
- **Related target files**: docs/adr/ADR-009-rag-ft5-text-separation.md
