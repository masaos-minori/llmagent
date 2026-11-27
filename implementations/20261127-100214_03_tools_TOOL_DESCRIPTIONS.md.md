## Goal
- Document the new tool in `tools/TOOL_DESCRIPTIONS.md` (`REQ-006`: Index row and Work Items row) so `tools/check_tool_descriptions_sync.py` passes.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Run after the seq 01 procedure. Another Plan (the repeated-row generator) adds its own rows to the same file; the two edits add separate rows and do not touch the same lines.
- Verified in Step 3a: the `amend_plan.py` Index row and Work Items row are the placement pattern (Index row beside it; Work Items row after the `amend_plan.py` row).

## Design decisions
- Index row Type `Work item`; Work Items row target `implementations/*.md` of a Plan.

## Alternatives considered
- N/A: single placement beside the Plan tools.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Index row: `finalize_procedures.py | Work item | Run the stale, structure, and Plan coverage checks for every procedure of a Plan, print only failures, classify each symbol_missing finding (created here, not a code symbol, ambiguous); --apply edits only the unambiguous names`.
2. Work Items row: state the checks and their unchanged exit semantics, discovery by `Source plan` base name (active procedures; `--include-done` adds archived ones for the per-document checks), the one-line `OK:` summary with computed counts, the classification rules in one sentence each, `--apply` and `--dry-run`, exit codes 0/1/2, and the usage line `finalize_procedures.py <plan> [--apply] [--dry-run] [--include-done] [--root R]`.

### Method
- Match the cell style of neighboring rows; keep each row on one line.

### Details
- State the limit: classification is lexical; a name matching no rule stays `ambiguous` and is never edited.

## Compatibility considerations
- N/A: documentation row only.

## Security considerations
- N/A: no behavior change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` exits 0.

## Completion criteria
- Both rows exist and describe the behavior of seq 01; the sync check passes.

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
- **Source issue**: issues/20261126-151441_wfeff006_finalize-procedure-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-095609_wfeff006_finalize-procedure-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-100214
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
