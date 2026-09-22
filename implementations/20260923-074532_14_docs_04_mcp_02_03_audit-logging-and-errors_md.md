## Goal

Add missing `## Related Documents` section and fix invalid `related` reference in `docs/04_mcp_02_03_audit-logging-and-errors.md` per REQ-002, REQ-004.

## Scope

Modify only `docs/04_mcp_02_03_audit-logging-and-errors.md` to add a missing structural section and fix an invalid cross-reference in its YAML Front Matter.

## Assumptions

- The file exists and has Front Matter with an invalid `related` field (confirmed by `check_docs_structure.py`)
- The file is missing the required `## Related Documents` section (confirmed by `check_docs_structure.py`)
- Both changes are needed: adding the section and fixing the reference

## Design decisions

- Add `## Related Documents\n<placeholder>` section as minimal valid content per Plan's Approach
- Fix the invalid `related` reference using git history to find the correct filename
- Keep the same YAML structure — only modify values, not keys

## Alternatives considered

- Adding specific references to `## Related Documents`: too speculative without knowing which documents are relevant
- Removing the invalid `related` reference entirely: rejected because the Plan states to use git history to find renamed files and update references accordingly
- Keeping the old reference: rejected because it violates REQ-002

## Implementation

### Target file

`docs/04_mcp_02_03_audit-logging-and-errors.md`

### Procedure

1. Read the current Front Matter of `docs/04_mcp_02_03_audit-logging-and-errors.md`
2. Identify the invalid `related` reference
3. Fix the invalid `related` reference using git history
4. Locate where the `## Related Documents` section should be inserted
5. Insert `## Related Documents\n<placeholder>` before the first `## Status` heading (or after the last `## ` heading if none exists)
6. Verify Markdown structure is not broken

### Method

String replacement within the YAML Front Matter block for the reference fix; insert a new section between the H1 heading and the first `## Status` heading.

### Details

Current state (approximate):
```yaml
---
title: "Audit Logging and Errors"
area: mcp
tags: []
related:
  - <invalid-reference>
status: draft
---

# Audit Logging and Errors

...document content...
```

After modification:
```yaml
---
title: "Audit Logging and Errors"
area: mcp
tags: []
related:
  - <corrected-filename>
status: draft
---

# Audit Logging and Errors

...document content...

## Related Documents
<placeholder>
```

Steps:
1. Run `git log --all --diff-filter=D -- "**/<invalid-reference>"` to find the actual filename
2. Replace the invalid reference in the Front Matter with the actual filename
3. Scan the document body for the appropriate insertion point for `## Related Documents`
4. Insert `## Related Documents\n<placeholder>` after the last `## ` heading (or after the H1 if no headings exist)
5. Verify the YAML indentation and Markdown structure remain valid

## Compatibility considerations

- Changing a cross-reference does not alter document content
- Adding a `## Related Documents` section does not alter any existing content
- The new filename resolves to an existing file in the repository
- This aligns with Plan's Approach: "add placeholder content for missing sections"

## Security considerations

No security impact — updating cross-references and adding documentation sections does not affect access control or authentication.

## Rollback considerations

1. Revert the string replacement to restore original reference
2. Remove the inserted `## Related Documents\n<placeholder>` section to restore original structure
3. No data loss risk — changes are purely additive

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid cross-references and missing sections.

## Completion criteria

- `related` entry contains corrected filename instead of the invalid reference
- `## Related Documents` section present after the last `## ` heading
- `<placeholder>` content present under the section
- YAML syntax remains valid
- Cross-reference resolves to an existing file in the repository
- Markdown structure not broken

## Out of scope

- Modifying any other file
- Determining whether additional references should be added to `## Related Documents`

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/04_mcp_02_03_audit-logging-and-errors.md
