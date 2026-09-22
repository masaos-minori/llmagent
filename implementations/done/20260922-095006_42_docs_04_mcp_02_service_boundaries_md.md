## Goal

Fix invalid `source` reference in `docs/04_mcp_02_service_boundaries.md`: remove deleted file reference per REQ-003.

## Scope

Modify only `docs/04_mcp_02_service_boundaries.md` to remove the invalid `source` field value referencing a deleted file.

## Assumptions

- The `source` field currently contains a reference to a deleted Python file (confirmed by `check_docs_structure.py`)
- No structural sections are missing (not flagged by `check_docs_structure.py`)
- Existing Front Matter values must not be changed except for removing the invalid reference

## Design decisions

- Remove the invalid `source` reference entirely rather than guessing its intent — Plan's Approach states "prefer removing over guessing"

## Alternatives considered

- Looking up git history to find the new filename: rejected because the plan says "If intentionally deleted, remove the reference"

## Implementation

### Target file

`docs/04_mcp_02_service_boundaries.md`

### Procedure

1. Read the current document structure to identify the `source` field with the deleted file reference
2. Check git history: `git log --all --diff-filter=D -- "**/<filename>"` to confirm deletion
3. If confirmed deleted: remove the invalid `source` value from Front Matter
4. Verify Markdown structure is not broken

### Method

Find the `source:` line in Front Matter and remove the invalid value.

### Details

Current structure (approximate):
```markdown
---
title: "Service Boundaries"
area: mcp
status: draft
related: []
source: "<deleted-file-path>"
...
---

# Service Boundaries

## Status
...
```

After modification:
```markdown
---
title: "Service Boundaries"
area: mcp
status: draft
related: []
...
---

# Service Boundaries

## Status
...
```

Remove the `source: "<deleted-file-path>"` line from Front Matter.

## Compatibility considerations

- Removing an invalid `source` reference does not change existing section meanings or other Front Matter values
- No structural changes beyond Front Matter cleanup

## Security considerations

No security impact — removing a documentation reference does not affect access control or authentication.

## Rollback considerations

Re-add the original `source: "<deleted-file-path>"` line to Front Matter to restore original state if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid references.

## Completion criteria

- Invalid `source` reference removed from Front Matter
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

- Fixing invalid `related` references in sibling MCP docs (separate requirement)
- Adding `## Keywords` section (separate requirement)
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
- **Source plan**: plans/20260922-094335_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-095006
- **Related target files**: docs/04_mcp_02_service_boundaries.md
