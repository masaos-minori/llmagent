## Goal

Fix invalid `source` reference in `docs/04_mcp_01_tool_ownership_matrix.md`: remove deleted file reference and add missing `## Related Documents` section per REQ-003, REQ-005.

## Scope

Modify only `docs/04_mcp_01_tool_ownership_matrix.md` to:
1. Remove invalid `source` field value referencing a deleted file
2. Add `## Related Documents\n<placeholder>` section

## Assumptions

- The `source` field currently contains a reference to a deleted Python file (confirmed by `check_docs_structure.py`)
- The document is missing `## Related Documents` section (confirmed by `check_docs_structure.py`)
- Existing Front Matter values must not be changed except for removing the invalid reference

## Design decisions

- Remove the invalid `source` reference entirely rather than guessing its intent — Plan's Approach states "prefer removing over guessing"
- Add `## Related Documents\n<placeholder>` as minimal valid section per Plan's Approach
- Do not attempt to infer what the deleted file was about — use git history if needed but prefer removal

## Alternatives considered

- Looking up git history to find the new filename: rejected because the plan says "If intentionally deleted, remove the reference"
- Adding a placeholder source value: rejected because it would introduce a false reference

## Implementation

### Target file

`docs/04_mcp_01_tool_ownership_matrix.md`

### Procedure

1. Read the current document structure to identify the `source` field with the deleted file reference
2. Check git history: `git log --all --diff-filter=D -- "**/<filename>"` to confirm deletion
3. If confirmed deleted: remove the invalid `source` value from Front Matter
4. Locate the first `## ` heading after the Front Matter
5. Insert `## Related Documents\n<placeholder>` before the first `## ` heading (after the H1)
6. Verify Markdown structure is not broken

### Method

Find the `source:` line in Front Matter and remove the invalid value. Then insert the `## Related Documents` section between the H1 heading and the first `## Status` heading.

### Details

Current structure (approximate):
```markdown
---
title: "Tool Ownership Matrix"
area: mcp
status: draft
related: []
source: "<deleted-file-path>"
...
---

# Tool Ownership Matrix

## Status
...
```

After modification:
```markdown
---
title: "Tool Ownership Matrix"
area: mcp
status: draft
related: []
...
---

# Tool Ownership Matrix

## Related Documents
<placeholder>

## Status
...
```

Steps:
1. Remove the `source: "<deleted-file-path>"` line from Front Matter
2. Insert `## Related Documents\n<placeholder>` between the H1 heading and the first `## Status` heading

## Compatibility considerations

- Removing an invalid `source` reference does not change existing section meanings or other Front Matter values
- Adding `## Related Documents` section does not alter any existing content
- The placeholder content will be replaced during implementation phase if needed

## Security considerations

No security impact — removing a documentation reference does not affect access control or authentication.

## Rollback considerations

1. Re-add the original `source: "<deleted-file-path>"` line to Front Matter
2. Remove the two inserted lines (`## Related Documents` and `<placeholder>`) to restore original structure if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid references and missing sections.

## Completion criteria

- Invalid `source` reference removed from Front Matter
- `## Related Documents` section present after H1 heading
- `<placeholder>` content present under the section
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
- **Requirement ID**: REQ-003, REQ-005
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260922-094335_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-095006
- **Related target files**: docs/04_mcp_01_tool_ownership_matrix.md
