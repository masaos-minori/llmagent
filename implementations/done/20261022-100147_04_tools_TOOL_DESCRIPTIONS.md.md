## Goal
Update the `check_docs_consistency.py` option row of `tools/TOOL_DESCRIPTIONS.md` to list the new domains (REQ-005: keep the domain lists in sync).

## Scope
- Edit the option row only; the first-table row (purpose summary) names no domains and stays.

## Assumptions
- `tools/check_tool_descriptions_sync.py` checks the presence of tool rows, not the domain list wording.

## Design decisions
- Replace the phrase "the five domains above" with "the domains above" to avoid a stale count.

## Alternatives considered
N/A: single-row docs edit.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. In the option cell change `--domain agent\|mcp\|rag\|deployment\|overview` to also list `eventbus`, `shared`, and `db` (keep the `\|` escaping used in the table).
2. In the description cell replace "Integrates the checks for the five domains above." with a sentence saying it integrates the checks for the listed domains and that the `eventbus`, `shared`, and `db` domains run only the generic checks.

### Method
- Minimal in-place edit of the one row; keep the rest of the cell (the `--skip` and agent-domain text) unchanged.

### Details
- Re-read the file before editing; it is also targeted by the anchor-validation Plan of this batch.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
- The option row lists all registered domain names and no longer says "five".
- The sync checker passes.

## Out of Scope
- Other rows of the file and the tool's behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the option row | Completed | 20261022-103313 | 20261022-103313 | Changed: tools/TOOL_DESCRIPTIONS.md |
| 2 | Run `check_tool_descriptions_sync.py` | Completed | 20261022-103313 | 20261022-103313 | validated; full suite 9687 passed, 14 skipped; docs checkers pass; check_tool_descriptions_sync passes |

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
- **Requirement ID**: `REQ-005` (sync the domain lists)
- **Source issue**: `issues/20261021-101756_domaincov_decide-consistency-check-coverage-for-the-eventbus-and-shared-db-docs-domains.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093304_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100147
- **Related target files**: tools/TOOL_DESCRIPTIONS.md