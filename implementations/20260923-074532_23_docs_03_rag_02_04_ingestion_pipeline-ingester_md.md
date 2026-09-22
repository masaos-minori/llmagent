## Goal

Reduce H1 heading count from 3 to exactly 1 in `docs/03_rag_02_04_ingestion_pipeline-ingester.md` per REQ-003.

## Scope

Modify only `docs/03_rag_02_04_ingestion_pipeline-ingester.md` to consolidate extra H1 headings to meet exactly-one requirement.

## Assumptions

- The file currently has 3 H1 headings (confirmed by `check_docs_structure.py`)
- The first H1 is likely the correct document title; the second and third should be demoted to H2
- Document content must not change — only heading levels need adjustment

## Design decisions

- Demote the second and third H1 headings to H2 level rather than deleting them — Plan's Approach states "demote extra headings to H2 without changing content meaning"
- Keep the first H1 as the document title

## Alternatives considered

- Deleting the extra H1s: rejected because it would lose content hierarchy
- Keeping all three H1 headings: rejected because it violates REQ-003

## Implementation

### Target file

`docs/03_rag_02_04_ingestion_pipeline-ingester.md`

### Procedure

1. Read the current document to identify which H1 heading is the document title and which are extra headings
2. Locate the second and third H1 heading lines (start with `# ` followed by text) after the Front Matter
3. Change each extra H1 to H2 by adding one `#` prefix: `# Heading` → `## Heading`
4. Verify Markdown structure is not broken

### Method

Find the second and third occurrences of a line starting with `# ` (not `## `) after the Front Matter and increment their heading levels by one.

### Details

Current structure (approximate):
```markdown
---
title: "Ingestion Pipeline Ingester"
area: rag
tags: []
related: []
...
---

# Ingestion Pipeline Ingester

## Overview
...

# Additional Section One
...

# Additional Section Two
...
```

After modification:
```markdown
---
title: "Ingestion Pipeline Ingester"
area: rag
tags: []
related: []
...
---

# Ingestion Pipeline Ingester

## Overview
...

## Additional Section One
...

## Additional Section Two
...
```

Steps:
1. Change the second `# Additional Section One` to `## Additional Section One`
2. Change the third `# Additional Section Two` to `## Additional Section Two`
3. Verify the Markdown structure is not broken

## Compatibility considerations

- Demoting H1s to H2 changes the visual hierarchy but preserves the content
- This aligns with Plan's Approach: "demote extra headings to H2 without changing content meaning"

## Security considerations

No security impact — modifying heading levels does not affect access control or authentication.

## Rollback considerations

1. Revert the heading level changes: `## Heading` → `# Heading` to restore original structure if needed

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding H1 heading count.

## Completion criteria

- Exactly one H1 heading present after modification
- Second and third H1 headings demoted to H2 level
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

- Modifying any other file

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/03_rag_02_04_ingestion_pipeline-ingester.md
