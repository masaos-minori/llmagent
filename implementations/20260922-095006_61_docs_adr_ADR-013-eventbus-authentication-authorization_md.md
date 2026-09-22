## Goal

Fix invalid `related` references in `docs/adr/ADR-013-eventbus-authentication-authorization.md`: update invalid `related` refs per REQ-003.

## Scope

Modify only `docs/adr/ADR-013-eventbus-authentication-authorization.md` to:
1. Update invalid `related` field references from ADR-style names to proper filenames

## Assumptions

- The document has invalid `related` references pointing to non-existent ADR files (confirmed by `check_docs_structure.py`)
- Existing Front Matter values must not be changed except for updating the references

## Design decisions

- Update each invalid `related` reference to point to the correct filename — Plan's Approach states "If found under new name, update the reference"

## Alternatives considered

- Removing invalid `related` entries entirely: rejected because it would lose existing cross-references
- Adding a new `source` field instead of fixing `related`: rejected because the issue is specific to `related`

## Implementation

### Target file

`docs/adr/ADR-013-eventbus-authentication-authorization.md`

### Procedure

1. Read the current document to identify the `related:` line in Front Matter containing invalid ADR references
2. Locate the `related:` line in Front Matter that contains invalid references (e.g., `[ADR-001, ADR-002]`)
3. Replace each invalid ADR name with its correct filename equivalent
4. Verify Markdown structure is not broken

### Method

Use string replacement on the `related:` line in Front Matter.

### Details

Current structure (approximate):
```markdown
---
title: "EventBus Authentication and Authorization"
area: adr
status: draft
related: [ADR-001, ADR-002]
...
---

# EventBus Authentication and Authorization

## Status
...
```

After modification:
```markdown
---
title: "EventBus Authentication and Authorization"
area: adr
status: draft
related: [adr/ADR-001-agent-control-plane-responsibility-boundaries.md, adr/ADR-002-git-mcp-server-side-write-enforcement.md]
...
---

# EventBus Authentication and Authorization

## Status
...
```

Steps:
1. Replace `related: [ADR-001, ADR-002]` with `related: [adr/ADR-001-agent-control-plane-responsibility-boundaries.md, adr/ADR-002-git-mcp-server-side-write-enforcement.md]` in Front Matter

## Compatibility considerations

- Updating invalid `related` references does not change existing section meanings or other Front Matter values

## Security considerations

No security impact — updating documentation references does not affect access control or authentication.

## Rollback considerations

1. Revert the `related:` field to its original value in Front Matter if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid references.

## Completion criteria

- Invalid `related` references updated to correct filenames
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

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
- **Related target files**: docs/adr/ADR-013-eventbus-authentication-authorization.md
