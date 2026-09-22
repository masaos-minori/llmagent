## Goal

Update invalid `related` references in `docs/adr/ADR-013-eventbus-authentication-authorization.md` from `ADR-002`/`ADR-006` to correct filenames per REQ-002.

## Scope

Modify only `docs/adr/ADR-013-eventbus-authentication-authorization.md` to fix two invalid cross-references in its YAML Front Matter.

## Assumptions

- The file exists and has Front Matter with invalid `related` fields pointing to `ADR-002` and `ADR-006` (confirmed by git history inspection)
- Two `related` references need correction in this file

## Design decisions

- Replace each invalid reference with its actual filename found via git history
- Keep the same YAML structure — only modify values, not keys
- Use git history as the source of truth for renamed/deleted files

## Alternatives considered

- Removing both references: rejected because the Plan states to use git history to find renamed files and update references accordingly
- Keeping the old references: rejected because they violate REQ-002

## Implementation

### Target file

`docs/adr/ADR-013-eventbus-authentication-authorization.md`

### Procedure

1. Read the current Front Matter of `docs/adr/ADR-013-eventbus-authentication-authorization.md`
2. Identify the `related` field entries referencing `ADR-002` and `ADR-006`
3. Replace each with the correct filename from git history
4. Verify YAML syntax is correct after modification

### Method

String replacements within the YAML Front Matter block — replace each invalid reference with its actual filename.

### Details

Current state (approximate):
```yaml
---
title: "EventBus Authentication Authorization"
area: adr
tags: []
related:
  - ADR-002
  - ADR-006
status: draft
---
```

After modification:
```yaml
---
title: "EventBus Authentication Authorization"
area: adr
tags: []
related:
  - <corrected-filename-for-ADR-002>
  - <corrected-filename-for-ADR-006>
status: draft
---
```

Steps:
1. Run `git log --all --diff-filter=D -- "**/ADR-002*.md"` to find the actual filename for ADR-002
2. Run `git log --all --diff-filter=D -- "**/ADR-006*.md"` to find the actual filename for ADR-006
3. Replace `- ADR-002` with the actual filename
4. Replace `- ADR-006` with the actual filename
5. Verify the YAML indentation and syntax remain valid

## Compatibility considerations

- Changing cross-references does not alter document content
- New filenames resolve to existing files in the repository
- This aligns with Plan's Approach: "use git history to find renamed/deleted files, update or remove references accordingly"

## Security considerations

No security impact — updating cross-references does not affect access control or authentication.

## Rollback considerations

1. Revert the string replacements to restore original references
2. No data loss risk — changes are purely reference updates

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid cross-references.

## Completion criteria

- Both `related` entries contain corrected filenames instead of `ADR-002` and `ADR-006`
- YAML syntax remains valid
- All cross-references resolve to existing files in the repository
- No other fields modified

## Out of scope

- Modifying any other file
- Determining whether additional references should be added or removed

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/adr/ADR-013-eventbus-authentication-authorization.md
