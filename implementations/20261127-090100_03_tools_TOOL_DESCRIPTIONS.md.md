## Goal
- Document the new tool in `tools/TOOL_DESCRIPTIONS.md` (`REQ-006`: Index row and Work Items row) so `tools/check_tool_descriptions_sync.py` passes.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Run after the seq 01 procedure; before it the sync check would report a missing file.
- Verified in plan-to-implementation-procedure Step 3a: the `amend_plan.py` Index row is at `tools/TOOL_DESCRIPTIONS.md:111` and its Work Items row at line 285; the tool must be named in backticks as `fill_affected_areas.py`.

## Design decisions
- Place the Index row next to the `amend_plan.py` row with Type `Work item`; place the Work Items row after the `amend_plan.py` row with the target `plans/*.md` (excluding `plans/done/`).

## Alternatives considered
- N/A: single obvious placement beside the sibling Plan tools.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Index table: add `| \`fill_affected_areas.py\` | Work item | Read-only: print the mechanical \`Affected areas\` columns (Change, Churn (30d), Bus Factor, deploy.sh Impact) and a module-size note for a Plan's target files; \`--insert\` writes only that table |`.
2. Work Items table: add one row stating the target, the rules (Change keywords; churn is the commit count of \`git log --since=30.days ... HEAD -- <file>\`; bus factor is High when one lowercased author name holds more than 70 percent; \`N/A (new)\` for a created file; \`Blast Radius\` is the placeholder \`TODO: author judgment\`), every git call has standard input closed, exit codes 0/1/2, and `fill_affected_areas.py <plan> [--insert] [--dry-run] [--root R] [--since S]`.

### Method
- Match the cell style of the neighboring rows; keep the rows on single lines.

### Details
- State the known limit: one person under two names beyond case reads as separate authors.

## Compatibility considerations
- N/A: documentation row only.

## Security considerations
- N/A: no behavior change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` exits 0.

## Completion criteria
- Both rows exist and describe the behavior implemented by seq 01; the sync check passes.

## Out of Scope
- Gate definitions, `rules/tool-gates.md`, other tools' rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Index row and the Work Items row | Pending | — | — | |
| 2 | Run `uv run python tools/check_tool_descriptions_sync.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (tool inventory)
- **Source issue**: issues/20261126-151440_wfeff005_affected-areas-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-085326_wfeff005_affected-areas-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-090100
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
