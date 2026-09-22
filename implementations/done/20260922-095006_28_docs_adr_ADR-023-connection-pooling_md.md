## Goal

Add missing `## Keywords` section to `docs/adr/ADR-023-connection-pooling.md` per REQ-005.

## Scope

Modify only `docs/adr/ADR-023-connection-pooling.md` to add the `## Keywords` section.

## Assumptions

- The document currently has no `## Keywords` section (confirmed by `check_docs_structure.py`)
- Placeholder content `<placeholder>` is acceptable for this structural section
- Existing Front Matter and content must not be changed

## Design decisions

- Add `## Keywords\n<placeholder>` as minimal valid section per Plan's Approach
- Do not attempt to infer keywords from document content — use placeholder to avoid guessing

## Alternatives considered

- Inferring keywords from document title/content: rejected because it risks incorrect keyword assignment; placeholder preserves neutrality
- Adding specific keywords based on ADR topic: rejected for same reason — could introduce subjective classification

## Implementation

### Target file

`docs/adr/ADR-023-connection-pooling.md`

### Procedure

1. Read the current document structure to locate the first `## ` heading after the Front Matter
2. Insert `## Keywords\n<placeholder>` before the first `## ` heading (after the H1)
3. Verify Markdown structure is not broken

### Method

Find the position immediately after the H1 heading (`# ADR-023:...`) and insert the new section there.

### Details

Current structure (approximate):
```markdown
---
title: "ADR-023: ..."
area: governance
...
---

# ADR-023: コネクションプーリング方針

## Status
...
```

After modification:
```markdown
---
title: "ADR-023: ..."
area: governance
...
---

# ADR-023: コネクションプーリング方針

## Keywords
<placeholder>

## Status
...
```

Insert `## Keywords\n<placeholder>` between the H1 heading and the first `## Status` heading.

## Compatibility considerations

- Adding a new section does not change existing section meanings or Front Matter values
- The placeholder content will be replaced during implementation phase if needed

## Security considerations

No security impact — adding a documentation section does not affect access control or authentication.

## Rollback considerations

Remove the two inserted lines (`## Keywords` and `<placeholder>`) to restore original structure if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding missing sections.

## Completion criteria

- `## Keywords` section present after H1 heading
- `<placeholder>` content present under the section
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

- Fixing invalid `related` references in sibling ADRs (separate requirement)
- Adding `## Related Documents` section (separate requirement)
- Modifying any other file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Blocked | 20260922-182034 | 20260922-182034 | Target file docs/adr/20260922-095006_28ADR-023-connection-pooling.md does not exist |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — |  |

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
- **Related target files**: docs/adr/ADR-023-connection-pooling.md