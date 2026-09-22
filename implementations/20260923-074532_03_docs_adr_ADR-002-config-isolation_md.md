## Goal

Update invalid `related` reference in `docs/adr/ADR-002-config-isolation.md` from `ADR-001` to correct filename `ADR-001-workflow-engine-mandatory.md` per REQ-002.

## Scope

Modify only `docs/adr/ADR-002-config-isolation.md` to fix one invalid cross-reference in its YAML Front Matter.

## Assumptions

- The file exists and has Front Matter with an invalid `related` field pointing to `ADR-001` (confirmed by git history inspection)
- The correct filename is `ADR-001-workflow-engine-mandatory.md` based on Plan's evidence
- Only one `related` reference needs correction in this file

## Design decisions

- Replace the invalid reference `ADR-001` with the actual filename `ADR-001-workflow-engine-mandatory.md`
- Keep the same YAML structure — only modify the value, not the key
- Use git history as the source of truth for renamed/deleted files

## Alternatives considered

- Removing the reference entirely: rejected because the Plan states to use git history to find renamed files and update references accordingly
- Keeping the old reference: rejected because it violates REQ-002 (all references must resolve to existing files)

## Implementation

### Target file

`docs/adr/ADR-002-config-isolation.md`

### Procedure

1. Read the current Front Matter of `docs/adr/ADR-002-config-isolation.md`
2. Locate the `related` field containing `ADR-001`
3. Replace `ADR-001` with `ADR-001-workflow-engine-mandatory.md` in that field
4. Verify YAML syntax is correct after modification

### Method

String replacement within the YAML Front Matter block — replace the exact substring `ADR-001` with `ADR-001-workflow-engine-mandatory.md`.

### Details

Current state (approximate):
```yaml
---
title: "Config Isolation"
area: adr
tags: []
related:
  - ADR-001
status: draft
---
```

After modification:
```yaml
---
title: "Config Isolation"
area: adr
tags: []
related:
  - ADR-001-workflow-engine-mandatory.md
status: draft
---
```

Steps:
1. Locate the `related:` section in the YAML Front Matter
2. Find the line `- ADR-001`
3. Change it to `- ADR-001-workflow-engine-mandatory.md`
4. Verify the YAML indentation and syntax remain valid

## Compatibility considerations

- Changing a cross-reference does not alter document content
- The new filename resolves to an existing file in the repository
- This aligns with Plan's Approach: "use git history to find renamed/deleted files, update or remove references accordingly"

## Security considerations

No security impact — updating a cross-reference does not affect access control or authentication.

## Rollback considerations

1. Revert the string replacement: `ADR-001-workflow-engine-mandatory.md` → `ADR-001`
2. No data loss risk — the change is purely a reference update

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid cross-references.

## Completion criteria

- `related` field contains `ADR-001-workflow-engine-mandatory.md` instead of `ADR-001`
- YAML syntax remains valid
- Cross-reference resolves to an existing file in the repository
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
- **Related target files**: docs/adr/ADR-002-config-isolation.md
