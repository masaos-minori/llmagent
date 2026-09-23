## Goal

Fix invalid `related` reference to `scripts/shared/tool_constants.py` in `docs/04_mcp_02_service_boundaries.md` per REQ-002.

## Scope

Modify only `docs/04_mcp_02_service_boundaries.md` to fix one invalid cross-reference in its YAML Front Matter.

## Assumptions

- The file exists and has Front Matter with an invalid `related` field pointing to `scripts/shared/tool_constants.py` (confirmed by `check_docs_structure.py`)
- One `related` reference needs correction in this file

## Design decisions

- Replace the invalid reference with its actual filename found via git history
- Keep the same YAML structure — only modify values, not keys
- Use git history as the source of truth for renamed/deleted files

## Alternatives considered

- Removing the reference entirely: rejected because the Plan states to use git history to find renamed files and update references accordingly
- Keeping the old reference: rejected because it violates REQ-002

## Implementation

### Target file

`docs/04_mcp_02_service_boundaries.md`

### Procedure

1. Read the current Front Matter of `docs/04_mcp_02_service_boundaries.md`
2. Locate the `related` field containing `scripts/shared/tool_constants.py`
3. Replace it with the correct filename from git history
4. Verify YAML syntax is correct after modification

### Method

String replacement within the YAML Front Matter block — replace the exact substring `scripts/shared/tool_constants.py` with the actual filename.

### Details

Current state (approximate):
```yaml
---
title: "Service Boundaries"
area: mcp
tags: []
related:
  - scripts/shared/tool_constants.py
status: draft
---
```

After modification:
```yaml
---
title: "Service Boundaries"
area: mcp
tags: []
related:
  - <corrected-filename>
status: draft
---
```

Steps:
1. Run `git log --all --diff-filter=D -- "**/tool_constants.py"` to find the actual filename
2. Replace `- scripts/shared/tool_constants.py` with the actual filename
3. Verify the YAML indentation and syntax remain valid

## Compatibility considerations

- Changing a cross-reference does not alter document content
- The new filename resolves to an existing file in the repository
- This aligns with Plan's Approach: "use git history to find renamed/deleted files, update or remove references accordingly"

## Security considerations

No security impact — updating a cross-reference does not affect access control or authentication.

## Rollback considerations

1. Revert the string replacement to restore original reference
2. No data loss risk — the change is purely a reference update

## Validation plan

Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` — expect zero errors for this file regarding invalid cross-references.

## Completion criteria

- `related` entry contains corrected filename instead of `scripts/shared/tool_constants.py`
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-135308 | 20260923-135308 |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260922-064743_doc002_fix-front-matter-inconsistencies-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-074532
- **Related target files**: docs/04_mcp_02_service_boundaries.md