## Goal

Reduce H1 heading count from 2 to exactly 1 in `docs/agent_02_runtime-architecture.md`, add missing `## Related Documents` section per REQ-003, REQ-004.

## Scope

Modify only `docs/agent_02_runtime-architecture.md` to consolidate extra H1 headings and add a missing structural section.

## Assumptions

- The file currently has 2 H1 headings (confirmed by `check_docs_structure.py`)
- The file is missing the required `## Related Documents` section (confirmed by `check_docs_structure.py`)
- Both changes are needed: reducing H1 count and adding the section

## Design decisions

- Demote the second H1 heading to H2 level rather than deleting it — Plan's Approach states "demote extra headings to H2 without changing content meaning"
- Add `## Related Documents\n<placeholder>` as minimal valid content per Plan's Approach

## Alternatives considered

- Deleting the extra H1: rejected because it would lose content hierarchy
- Keeping both H1 headings: rejected because it violates REQ-003

## Implementation

### Target file

`docs/agent_02_runtime-architecture.md`

### Procedure

1. Read the current document to identify which H1 heading is the document title and which is an extra heading
2. Locate the second H1 heading line (starts with `# ` followed by text) after the Front Matter
3. Change the second H1 to H2 by adding one `#` prefix: `# Heading` → `## Heading`
4. Locate where the `## Related Documents` section should be inserted
5. Insert `## Related Documents\n<placeholder>` before the first `## Status` heading (or after the last `## ` heading if none exists)
6. Verify Markdown structure is not broken

### Method

Find the second occurrence of a line starting with `# ` (not `## `) after the Front Matter and increment its heading level by one. Then insert the new section between the H1 heading and the first `## Status` heading.

### Details

Current structure (approximate):
```markdown
---
title: "Runtime Architecture"
area: agent
tags: []
related: []
...
---

# Runtime Architecture

## Overview
...

# Additional Section Title
...
```

After modification:
```markdown
---
title: "Runtime Architecture"
area: agent
tags: []
related: []
...
---

# Runtime Architecture

## Overview
...

## Related Documents
<placeholder>

## Additional Section Title
...
```

Steps:
1. Change the second `# Additional Section Title` to `## Additional Section Title`
2. Insert `## Related Documents\n<placeholder>` after the last `## ` heading (or after the H1 if no headings exist)
3. Verify the Markdown structure is not broken

## Compatibility considerations

- Demoting an H1 to H2 changes the visual hierarchy but preserves the content
- Adding `## Related Documents` section does not alter any existing content
- This aligns with Plan's Approach: "demote extra headings to H2 without changing content meaning"

## Security considerations

No security impact — modifying heading levels and adding documentation sections does not affect access control or authentication.

## Rollback considerations

1. Revert the heading level change: `## Heading` → `# Heading` to restore original structure if needed
2. Remove the inserted `## Related Documents\n<placeholder>` section to restore original structure if needed

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding H1 heading count and missing sections.

## Completion criteria

- Exactly one H1 heading present after modification
- Second H1 heading demoted to H2 level
- `## Related Documents` section present after the last `## ` heading
- `<placeholder>` content present under the section
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

- Modifying any other file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-135308 | 20260923-135308 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260923-135543 | 20260923-135543 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-135543 | 20260923-135543 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-135543 | 20260923-135543 |  |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/agent_02_runtime-architecture.md