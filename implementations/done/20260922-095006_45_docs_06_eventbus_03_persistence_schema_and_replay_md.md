## Goal

Fix invalid `source` reference in `docs/06_eventbus_03_persistence_schema_and_replay.md`: replace `index.md` → `00_index.md`, add missing `## Keywords` and `## Related Documents` sections per REQ-003, REQ-005.

## Scope

Modify only `docs/06_eventbus_03_persistence_schema_and_replay.md` to:
1. Replace invalid `source` field value (`index.md` → `00_index.md`)
2. Add `## Keywords\n<placeholder>` section
3. Add `## Related Documents\n<placeholder>` section

## Assumptions

- The `source` field currently contains `index.md` which was renamed to `00_index.md` (confirmed by `check_docs_structure.py`)
- The document is missing both `## Keywords` and `## Related Documents` sections (confirmed by `check_docs_structure.py`)
- Existing Front Matter values must not be changed except for updating the reference

## Design decisions

- Update the `source` reference from `index.md` to `00_index.md` — Plan's Approach states "If found under new name, update the reference"
- Add both `## Keywords\n<placeholder>` and `## Related Documents\n<placeholder>` as minimal valid sections per Plan's Approach

## Alternatives considered

- Adding a new `related` field entry instead of fixing `source`: rejected because the reference exists under a different name

## Implementation

### Target file

`docs/06_eventbus_03_persistence_schema_and_replay.md`

### Procedure

1. Read the current document structure to identify the `source` field with `index.md` reference
2. Locate the `source:` line in Front Matter containing `index.md`
3. Replace `index.md` with `00_index.md` in the `source` value
4. Locate the first `## ` heading after the Front Matter
5. Insert `## Keywords\n<placeholder>` before the first `## ` heading (after the H1)
6. Insert `## Related Documents\n<placeholder>` after `## Keywords` section
7. Verify Markdown structure is not broken

### Method

Use string replacement on the `source:` line in Front Matter. Then insert both sections between the H1 heading and the first `## Status` heading.

### Details

Current structure (approximate):
```markdown
---
title: "Persistence Schema and Replay"
area: eventbus
status: draft
related: []
source: "index.md"
...
---

# Persistence Schema and Replay

## Status
...
```

After modification:
```markdown
---
title: "Persistence Schema and Replay"
area: eventbus
status: draft
related: []
source: "00_index.md"
...
---

# Persistence Schema and Replay

## Keywords
<placeholder>

## Related Documents
<placeholder>

## Status
...
```

Steps:
1. Replace `source: "index.md"` with `source: "00_index.md"` in Front Matter
2. Insert `## Keywords\n<placeholder>` between the H1 heading and the first `## Status` heading
3. Insert `## Related Documents\n<placeholder>` after the `## Keywords` section

## Compatibility considerations

- Updating an invalid `source` reference does not change existing section meanings or other Front Matter values
- Adding `## Keywords` and `## Related Documents` sections does not alter any existing content
- The placeholder content will be replaced during implementation phase if needed

## Security considerations

No security impact — updating a documentation reference does not affect access control or authentication.

## Rollback considerations

1. Revert `source: "00_index.md"` back to `source: "index.md"` in Front Matter
2. Remove the four inserted lines (`## Keywords`, `<placeholder>`, `## Related Documents`, `<placeholder>`) to restore original structure if needed.

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid references and missing sections.

## Completion criteria

- Invalid `source` reference updated from `index.md` to `00_index.md`
- `## Keywords` section present after H1 heading
- `## Related Documents` section present after `## Keywords` section
- `<placeholder>` content present under each section
- All existing sections preserved unchanged
- Markdown structure not broken

## Out of scope

- Fixing invalid `related` references in sibling eventbus docs (separate requirement)
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
- **Related target files**: docs/06_eventbus_03_persistence_schema_and_replay.md
