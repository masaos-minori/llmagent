## Goal

Fix H1 heading count and add `## Keywords` section in `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`: consolidate extra headings to meet exactly-one requirement per REQ-004, add missing section per REQ-005.

## Scope

Modify only `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` to:
1. Reduce H1 heading count from 0 to exactly 1
2. Add `## Keywords\n<placeholder>` section

## Assumptions

- The document currently has 0 H1 headings (confirmed by `check_docs_structure.py`) — it needs exactly one
- The document is missing `## Keywords` section (confirmed by `check_docs_structure.py`)
- Document content must not change — only heading levels and sections need adjustment

## Design decisions

- Add a new H1 heading at the top of the document body (after Front Matter) since none exists — Plan's Approach states "add an H1 if none exists"
- Add `## Keywords\n<placeholder>` as minimal valid section per Plan's Approach

## Alternatives considered

- Keeping zero H1 headings: rejected because it violates REQ-004 which requires exactly one
- Demoting existing headings: rejected because there are no existing headings to demote

## Implementation

### Target file

`docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`

### Procedure

1. Read the current document to identify the Front Matter block and determine appropriate H1 title
2. Locate the end of the Front Matter block (the closing `---`)
3. Insert a new H1 heading line after the Front Matter: `# Fail-Open / Fail-Closed and Risk Tiers`
4. Insert `## Keywords\n<placeholder>` after the H1 heading
5. Verify Markdown structure is not broken

### Method

Insert two lines after the Front Matter closing `---`: the H1 heading, then `## Keywords`, `<placeholder>`.

### Details

Current structure (approximate):
```markdown
---
title: "Fail-Open / Fail-Closed and Risk Tiers"
area: mcp
status: draft
related: []
...
---

## Overview
...
```

After modification:
```markdown
---
title: "Fail-Open / Fail-Closed and Risk Tiers"
area: mcp
status: draft
related: []
...
---

# Fail-Open / Fail-Closed and Risk Tiers

## Keywords
<placeholder>

## Overview
...
```

Steps:
1. Insert `# Fail-Open / Fail-Closed and Risk Tiers` after the Front Matter closing `---`
2. Insert `## Keywords\n<placeholder>` between the H1 heading and the first `## Overview` heading

## Compatibility considerations

- Adding an H1 heading changes the visual hierarchy but preserves the content
- Adding `## Keywords` section does not alter any existing content
- This aligns with Plan's Approach: "add an H1 if none exists"

## Security considerations

No security impact — modifying heading levels and adding documentation sections does not affect access control or authentication.

## Rollback considerations

1. Remove the four inserted lines (`# Fail-Open / Fail-Closed and Risk Tiers`, `## Keywords`, `<placeholder>`) to restore original structure if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding H1 heading count and missing sections.

## Completion criteria

- Exactly one H1 heading present after modification
- `## Keywords` section present after H1 heading
- `<placeholder>` content present under the section
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

- Adding `## Related Documents` section (separate requirement)
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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260922-094335_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-095006
- **Related target files**: docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
