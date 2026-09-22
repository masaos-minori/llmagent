## Goal

Fix invalid `related` reference in `docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md`: add missing `## Keywords` section per REQ-005.

## Scope

Modify only `docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md` to:
1. Add `## Keywords\n<placeholder>` section

## Assumptions

- The document is missing `## Keywords` section (confirmed by `check_docs_structure.py`)
- Existing Front Matter values must not be changed

## Design decisions

- Add `## Keywords\n<placeholder>` as minimal valid section per Plan's Approach

## Alternatives considered

- Skipping this file because it has no other issues: rejected because REQ-005 requires adding `## Keywords` to all documents missing it

## Implementation

### Target file

`docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md`

### Procedure

1. Read the current document to identify the first `## ` heading after the Front Matter
2. Locate the first `## ` heading line after the Front Matter
3. Insert `## Keywords\n<placeholder>` before the first `## ` heading (after the H1)
4. Verify Markdown structure is not broken

### Method

Insert two lines after the H1 heading and before the first `## Status` heading: `## Keywords`, `<placeholder>`.

### Details

Current structure (approximate):
```markdown
---
title: "Agent Control Plane Responsibility Boundaries"
area: adr
status: draft
related: []
...
---

# Agent Control Plane Responsibility Boundaries

## Status
...
```

After modification:
```markdown
---
title: "Agent Control Plane Responsibility Boundaries"
area: adr
status: draft
related: []
...
---

# Agent Control Plane Responsibility Boundaries

## Keywords
<placeholder>

## Status
...
```

Steps:
1. Insert `## Keywords\n<placeholder>` between the H1 heading and the first `## Status` heading

## Compatibility considerations

- Adding `## Keywords` section does not alter any existing content
- The placeholder content will be replaced during implementation phase if needed

## Security considerations

No security impact — adding a documentation section does not affect access control or authentication.

## Rollback considerations

1. Remove the two inserted lines (`## Keywords` and `<placeholder>`) to restore original structure if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding missing sections.

## Completion criteria

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-073942 | 20260923-073942 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260923-073944 | 20260923-073944 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-073946 | 20260923-073946 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-073948 | 20260923-073948 |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260922-094335_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-095006
- **Related target files**: docs/adr/ADR-014-agent-control-plane-responsibility-boundaries.md