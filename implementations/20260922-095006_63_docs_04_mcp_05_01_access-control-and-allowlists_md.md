## Goal

Fix invalid `related` references in `docs/04_mcp_05_01_access-control-and-allowlists.md`: update invalid `related` refs per REQ-003, add missing `## Keywords` section per REQ-005.

## Scope

Modify only `docs/04_mcp_05_01_access-control-and-allowlists.md` to:
1. Update invalid `related` field references from ADR-style names to proper filenames
2. Add `## Keywords\n<placeholder>` section

## Assumptions

- The document has invalid `related` references pointing to non-existent ADR files (confirmed by `check_docs_structure.py`)
- The document is missing `## Keywords` section (confirmed by `check_docs_structure.py`)
- Existing Front Matter values must not be changed except for updating the references

## Design decisions

- Update each invalid `related` reference to point to the correct filename — Plan's Approach states "If found under new name, update the reference"
- Add `## Keywords\n<placeholder>` as minimal valid section per Plan's Approach

## Alternatives considered

- Removing invalid `related` entries entirely: rejected because it would lose existing cross-references
- Adding a new `source` field instead of fixing `related`: rejected because the issue is specific to `related`

## Implementation

### Target file

`docs/04_mcp_05_01_access-control-and-allowlists.md`

### Procedure

1. Read the current document to identify the `related:` line in Front Matter containing invalid ADR references
2. Locate the `related:` line in Front Matter that contains invalid references (e.g., `[ADR-001, ADR-002]`)
3. Replace each invalid ADR name with its correct filename equivalent
4. Locate the first `## ` heading after the Front Matter
5. Insert `## Keywords\n<placeholder>` before the first `## ` heading (after the H1)
6. Verify Markdown structure is not broken

### Method

Use string replacement on the `related:` line in Front Matter. Then insert the `## Keywords` section between the H1 heading and the first `## Status` heading.

### Details

Current structure (approximate):
```markdown
---
title: "Access Control and Allowlists"
area: mcp
status: draft
related: [ADR-001, ADR-002]
...
---

# Access Control and Allowlists

## Status
...
```

After modification:
```markdown
---
title: "Access Control and Allowlists"
area: mcp
status: draft
related: [adr/ADR-001-agent-control-plane-responsibility-boundaries.md, adr/ADR-002-git-mcp-server-side-write-enforcement.md]
...
---

# Access Control and Allowlists

## Keywords
<placeholder>

## Status
...
```

Steps:
1. Replace `related: [ADR-001, ADR-002]` with `related: [adr/ADR-001-agent-control-plane-responsibility-boundaries.md, adr/ADR-002-git-mcp-server-side-write-enforcement.md]` in Front Matter
2. Insert `## Keywords\n<placeholder>` between the H1 heading and the first `## Status` heading

## Compatibility considerations

- Updating invalid `related` references does not change existing section meanings or other Front Matter values
- Adding `## Keywords` section does not alter any existing content
- The placeholder content will be replaced during implementation phase if needed

## Security considerations

No security impact — updating documentation references does not affect access control or authentication.

## Rollback considerations

1. Revert the `related:` field to its original value in Front Matter
2. Remove the two inserted lines (`## Keywords` and `<placeholder>`) to restore original structure if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid references and missing sections.

## Completion criteria

- Invalid `related` references updated to correct filenames
- `## Keywords` section present after H1 heading
- `<placeholder>` content present under the section
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

- Modifying any other file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-000729 | 20260923-000729 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260923-000731 | 20260923-000731 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-000733 | 20260923-000733 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-000735 | 20260923-000735 |  |

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
- **Related target files**: docs/04_mcp_05_01_access-control-and-allowlists.md