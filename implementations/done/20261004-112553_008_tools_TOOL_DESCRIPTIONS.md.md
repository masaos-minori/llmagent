## Goal
Update `tools/TOOL_DESCRIPTIONS.md` for the `merge-related` subcommand, the `rename_doc.py` front matter handling, and the revised `check_docs_structure.py` rules (REQ-006: keep tool descriptions in sync).

## Scope
- In: the rows for `manage_frontmatter.py`, `rename_doc.py`, and `check_docs_structure.py` (both the short table and the detailed table where each appears).
- Out: rows for other tools.

## Assumptions
- The file is written in Japanese; new text follows that language and the existing row style.
- `tools/check_tool_descriptions_sync.py` checks that every tool has a row and that no row names a deleted file; no new tool file is added, so no new row is needed.

## Design decisions
- Edit existing rows in place; keep each row's length and structure.

## Alternatives considered
- Add a separate row for the subcommand: rejected; the subcommands are listed inside the tool's existing row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. In the `manage_frontmatter.py` rows, add `merge-related` (dry-run default, `--fix`, recursive, ADR handling) to the subcommand lists.
2. In the `rename_doc.py` rows, add that front matter `related:` entries are rewritten.
3. In the `check_docs_structure.py` row, replace the Related Documents wording with the ADR-only requirement, the non-ADR leftover finding, and the ADR coverage check.

### Method
- Keep Japanese prose consistent with the neighboring rows.
- Mention behavior at the level of detail the existing rows use.

### Details
- Churn on this file is high; fetch before editing and edit in one commit with the other REQ-006 rows.

## Compatibility considerations
- Documentation-only change.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
- The three tools' rows describe the new behavior.
- The sync check passes.

## Out of scope
- Rows for tools this Plan does not touch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the three tools' rows | Completed | 20261004-125204 | 20261004-125204 | edited the three tools' rows (short and detailed tables) |
| 2 | N/A: no tests for this file | Completed | 20261004-125204 | 20261004-125204 | N/A: no tests for this file |
| 3 | Run `tools/check_tool_descriptions_sync.py` | Completed | 20261004-125204 | 20261004-125204 | check_tool_descriptions_sync.py: No issues found |
| 4 | N/A: this file is the documentation change | Completed | 20261004-125204 | 20261004-125204 | N/A: this file is the documentation change |

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
- **Requirement ID**: `REQ-006` (document the tool changes)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: tools/TOOL_DESCRIPTIONS.md