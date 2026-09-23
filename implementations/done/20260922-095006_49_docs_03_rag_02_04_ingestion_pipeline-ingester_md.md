## Goal

Fix H1 heading count in `docs/03_rag_02_04_ingestion_pipeline-ingester.md`: consolidate extra headings to meet exactly-one requirement per REQ-004.

## Scope

Modify only `docs/03_rag_02_04_ingestion_pipeline-ingester.md` to reduce H1 heading count from 3 to exactly 1.

## Assumptions

- The document currently has 3 H1 headings (confirmed by `check_docs_structure.py`)
- The first H1 is likely the correct one; additional H1 headings should be demoted to H2
- Document content must not change — only heading levels need adjustment

## Design decisions

- Demote the second and third H1 headings to H2 level rather than deleting them — Plan's Approach states "demote extra headings to H2 without changing content meaning"
- Keep the first H1 as-is since it represents the document title

## Alternatives considered

- Deleting the extra H1s: rejected because it would lose content hierarchy
- Keeping all three H1 headings: rejected because it violates REQ-004

## Implementation

### Target file

`docs/03_rag_02_04_ingestion_pipeline-ingester.md`

### Procedure

1. Read the current document to identify which H1 heading is the document title and which are extra headings
2. Locate each H1 heading line (starts with `# ` followed by text) after the Front Matter
3. Change the second and third H1 headings to H2 level by adding one `#` prefix: `# Heading` → `## Heading`
4. Verify Markdown structure is not broken

### Method

Find each occurrence of a line starting with `# ` (not `## `) after the Front Matter and increment its heading level by one.

### Details

Current structure (approximate):
```markdown
---
title: "Ingestion Pipeline - Ingester"
area: rag
status: draft
...
---

# Ingestion Pipeline - Ingester

## Overview
...

# Additional Section Title 1
...

# Additional Section Title 2
...
```

After modification:
```markdown
---
title: "Ingestion Pipeline - Ingester"
area: rag
status: draft
...
---

# Ingestion Pipeline - Ingester

## Overview
...

## Additional Section Title 1
...

## Additional Section Title 2
...
```

Change both `# Additional Section Title` lines to `## Additional Section Title`.

## Compatibility considerations

- Demoting H1 headings to H2 changes the visual hierarchy but preserves the content
- This aligns with Plan's Approach: "demote extra headings to H2 without changing content meaning"

## Security considerations

No security impact — modifying heading levels does not affect access control or authentication.

## Rollback considerations

Revert the heading level changes: `## Heading` → `# Heading` to restore original structure if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding H1 heading count.

## Completion criteria

- Exactly one H1 heading present after modification
- Second and third H1 headings demoted to H2 level
- All existing sections and content preserved unchanged
- Markdown structure not broken

## Out of scope

- Adding `## Keywords` section (separate requirement)
- Adding `## Related Documents` section (separate requirement)
- Modifying any other file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-133638 | 20260923-133638 | Revalidated 20260923-133638: target file already reflects this change; Execution Status was not updated when the edit was made. |
| 2 | Add or update tests per Validation plan | Completed | 20260923-133638 | 20260923-133638 | Revalidated 20260923-133638: target file already reflects this change; Execution Status was not updated when the edit was made. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-133638 | 20260923-133638 | Revalidated 20260923-133638: target file already reflects this change; Execution Status was not updated when the edit was made. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-133638 | 20260923-133638 | Revalidated 20260923-133638: target file already reflects this change; Execution Status was not updated when the edit was made. |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260922-094335_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-095006
- **Related target files**: docs/03_rag_02_04_ingestion_pipeline-ingester.md