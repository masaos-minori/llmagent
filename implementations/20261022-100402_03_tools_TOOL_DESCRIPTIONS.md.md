## Goal
Describe the anchor check in the `_docs_consistency_lib.py` rows of `tools/TOOL_DESCRIPTIONS.md` (REQ-006: document the check).

## Scope
- Edit the two `_docs_consistency_lib.py` rows; no other row.

## Assumptions
- The sync checker validates row presence, not the wording of descriptions.

## Design decisions
- Mention that the check is Warning-level and uses GitHub-style heading slugs, without listing implementation detail.

## Alternatives considered
N/A: two-row docs edit.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. In the detailed row, change "broken internal links" in the generic-check list to also state that an `#anchor` matching no heading of the target document (same-page links included) is reported as a Warning, using GitHub-style heading slugs.
2. Leave the short summary row ("generic checks") unchanged.

### Method
- Minimal in-place edit; keep the `\|` escaping and the rest of the row text.

### Details
- Re-read the file before editing: it is also edited by the EventBus/Shared/DB domain-coverage procedures of the same batch.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
- The detailed row states the anchor check, its Warning level, and the slug rule; the sync checker passes.

## Out of Scope
- Other tools' rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the detailed `_docs_consistency_lib.py` row | Pending | — | — | |
| 2 | Run `check_tool_descriptions_sync.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (document the check)
- **Source issue**: `issues/20261021-101812_anchorcheck_add-a-dedicated-anchor-validation-check-for-docs-links.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093452_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100402
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
