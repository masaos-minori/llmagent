## Goal

Fix invalid `source` references in `docs/00_security_01_architecture-and-trust-boundaries.md`: remove deleted file references per REQ-003.

## Scope

Modify only `docs/00_security_01_architecture-and-trust-boundaries.md` to remove invalid `source` field values referencing deleted Python files.

## Assumptions

- The `source` field currently contains references to deleted Python files (confirmed by `check_docs_structure.py`)
- No structural sections are missing (not flagged by `check_docs_structure.py`)
- Existing Front Matter values must not be changed except for removing the invalid references

## Design decisions

- Remove all invalid `source` references entirely rather than guessing their intent — Plan's Approach states "prefer removing over guessing"

## Alternatives considered

- Looking up git history to find new filenames: rejected because the plan says "If intentionally deleted, remove the reference"

## Implementation

### Target file

`docs/00_security_01_architecture-and-trust-boundaries.md`

### Procedure

1. Read the current document structure to identify the `source` field(s) with deleted file references
2. Check git history: `git log --all --diff-filter=D -- "**/<filename>"` to confirm deletion
3. If confirmed deleted: remove each invalid `source` value from Front Matter
4. Verify Markdown structure is not broken

### Method

Find the `source:` line(s) in Front Matter and remove the invalid values.

### Details

Current structure (approximate):
```markdown
---
title: "Architecture and Trust Boundaries"
area: security
status: draft
related: []
source: "<deleted-file-path-1>"
source: "<deleted-file-path-2>"
...
---

# Architecture and Trust Boundaries

## Status
...
```

After modification:
```markdown
---
title: "Architecture and Trust Boundaries"
area: security
status: draft
related: []
...
---

# Architecture and Trust Boundaries

## Status
...
```

Remove all `source: "<deleted-file-path>"` lines from Front Matter.

## Compatibility considerations

- Removing invalid `source` references does not change existing section meanings or other Front Matter values
- No structural changes beyond Front Matter cleanup

## Security considerations

No security impact — removing a documentation reference does not affect access control or authentication.

## Rollback considerations

Re-add the original `source: "<deleted-file-path>"` lines to Front Matter to restore original state if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid references.

## Completion criteria

- All invalid `source` references removed from Front Matter
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

- Fixing invalid `related` references in sibling security docs (separate requirement)
- Adding `## Keywords` section (separate requirement)
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260922-094335_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-095006
- **Related target files**: docs/00_security_01_architecture-and-trust-boundaries.md