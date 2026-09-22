## Goal

Fix H1 heading count and add `## Keywords` section in `docs/05_agent_12_01_memory-overview-and-modes.md`: consolidate extra headings to meet exactly-one requirement per REQ-004, add missing section per REQ-005.

## Scope

Modify only `docs/05_agent_12_01_memory-overview-and-modes.md` to:
1. Reduce H1 heading count from 2 to exactly 1
2. Add `## Keywords\n<placeholder>` section

## Assumptions

- The document currently has 2 H1 headings (confirmed by `check_docs_structure.py`)
- The first H1 is likely the correct one; additional H1 headings should be demoted to H2
- The document is missing `## Keywords` section (confirmed by `check_docs_structure.py`)
- Document content must not change — only heading levels and sections need adjustment

## Design decisions

- Demote the second H1 heading to H2 level rather than deleting it — Plan's Approach states "demote extra headings to H2 without changing content meaning"
- Add `## Keywords\n<placeholder>` as minimal valid section per Plan's Approach

## Alternatives considered

- Deleting the extra H1: rejected because it would lose content hierarchy
- Keeping both H1 headings: rejected because it violates REQ-004

## Implementation

### Target file

`docs/05_agent_12_01_memory-overview-and-modes.md`

### Procedure

1. Read the current document to identify which H1 heading is the document title and which is an extra heading
2. Locate the second H1 heading line (starts with `# ` followed by text) after the Front Matter
3. Change the second H1 to H2 by adding one `#` prefix: `# Heading` → `## Heading`
4. Locate the first `## ` heading after the Front Matter
5. Insert `## Keywords\n<placeholder>` before the first `## ` heading (after the H1)
6. Verify Markdown structure is not broken

### Method

Find the second occurrence of a line starting with `# ` (not `## `) after the Front Matter and increment its heading level by one. Then insert the `## Keywords` section between the H1 heading and the first `## Status` heading.

### Details

Current structure (approximate):
```markdown
---
title: "Memory Overview and Modes"
area: agent
status: draft
related: []
...
---

# Memory Overview and Modes

## Overview
...

# Additional Section Title
...
```

After modification:
```markdown
---
title: "Memory Overview and Modes"
area: agent
status: draft
related: []
...
---

# Memory Overview and Modes

## Keywords
<placeholder>

## Overview
...

## Additional Section Title
...
```

Steps:
1. Change the second `# Additional Section Title` to `## Additional Section Title`
2. Insert `## Keywords\n<placeholder>` between the H1 heading and the first `## Overview` heading

## Compatibility considerations

- Demoting an H1 to H2 changes the visual hierarchy but preserves the content
- Adding `## Keywords` section does not alter any existing content
- This aligns with Plan's Approach: "demote extra headings to H2 without changing content meaning"

## Security considerations

No security impact — modifying heading levels and adding documentation sections does not affect access control or authentication.

## Rollback considerations

1. Revert the heading level change: `## Heading` → `# Heading` to restore original structure if needed
2. Remove the four inserted lines (`## Keywords`, `<placeholder>`) to restore original structure if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding H1 heading count and missing sections.

## Completion criteria

- Exactly one H1 heading present after modification
- Second H1 heading demoted to H2 level
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260922-212554 | 20260922-212554 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260922-212555 | 20260922-212555 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260922-212556 | 20260922-212556 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260922-212558 | 20260922-212558 |  |

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
- **Related target files**: docs/05_agent_12_01_memory-overview-and-modes.md