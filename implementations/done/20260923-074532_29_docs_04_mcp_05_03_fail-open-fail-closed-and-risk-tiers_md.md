## Goal

Add missing H1 heading to `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` per REQ-003.

## Scope

Modify only `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` to add an H1 heading.

## Assumptions

- The file currently has 0 H1 headings (confirmed by `check_docs_structure.py`)
- Document content must not change — only heading addition is needed
- The document title can be inferred from the filename

## Design decisions

- Add `# <Title>` as the first line after Front Matter to satisfy REQ-003
- Use the filename-derived title "Fail-Open Fail-Closed and Risk Tiers"

## Alternatives considered

- Demoting an existing subheading to H1: rejected because there are no existing H1 headings to demote
- Keeping the file without an H1: rejected because it violates REQ-003

## Implementation

### Target file

`docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`

### Procedure

1. Read the current document to understand its content and determine appropriate title
2. Insert `# Fail-Open Fail-Closed and Risk Tiers` as the first line after Front Matter
3. Verify Markdown structure is not broken

### Method

Prepend an H1 heading after the Front Matter closing `---`.

### Details

Current state (approximate):
```yaml
---
title: "Fail-Open Fail-Closed and Risk Tiers"
area: mcp
tags: []
related: []
status: draft
---

<no H1 heading>
<document content begins>
```

After modification:
```yaml
---
title: "Fail-Open Fail-Closed and Risk Tiers"
area: mcp
tags: []
related: []
status: draft
---

# Fail-Open Fail-Closed and Risk Tiers

<document content continues>
```

Steps:
1. Determine the document title from the filename (likely "Fail-Open Fail-Closed and Risk Tiers")
2. Prepend `# Fail-Open Fail-Closed and Risk Tiers` after the Front Matter closing `---`
3. Verify the Markdown structure is not broken

## Compatibility considerations

- Adding an H1 heading changes visual hierarchy but is required by REQ-003
- The title matches the document's existing `title` field in Front Matter
- This aligns with Plan's Approach: "add exactly-one H1 heading"

## Security considerations

No security impact — adding a heading does not affect access control or authentication.

## Rollback considerations

1. Remove the added H1 heading to restore original state
2. No data loss risk — the change is purely additive

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding H1 heading count.

## Completion criteria

- Exactly one H1 heading present after modification
- H1 heading text matches the document title
- All existing content preserved unchanged
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md