## Goal
- Register `tools/amend_plan.py` in `tools/TOOL_DESCRIPTIONS.md` so `check_tool_descriptions_sync.py` passes (`REQ-006`).

## Scope
- In scope: one Index row and one `## Work Items` row. Out of scope: the Index heading count and other rows.

## Assumptions
- Step 3a verification: `tools/check_tool_descriptions_sync.py` compares live `tools/*.py` against backticked `*.py` names anywhere in the file (no count check); the Index heading `## Index (61 modules)` is already stale against the live file count, so it is not touched (sibling Plans add rows concurrently).
- Overlap (Step 2): also a target of `plans/20261102-080631_flowimp008_workitem-bulk-close.md` and `plans/20261102-081312_flowimp010_artifact-commit-split.md`, plus the Plans filed from flowimp001, 003, 005, and 007 (generated procedures). Judged compatible (Plan A7, A7a): each adds its own rows. Anchors here are chosen away from the neighbors' (before `audit_plan_target_paths.py` in the Index, first data row of the Work Items table).
- `tools/amend_plan.py` is created by the seq 01 procedure (acceptable earlier-`seq` reference).

## Design decisions
- Index row category `Work item`, placed before the `audit_plan_target_paths.py` row; Work Items row as the first data row, with target `plans/*.md` (excluding `plans/done/`).

## Alternatives considered
N/A: every tool needs a row (Global Rule 9).

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the `audit_plan_target_paths.py` Index row and insert the new Index row before it.
2. Insert the row in the `## Work Items` table before the `check_plan_target_overlaps.py` row.

### Method
- Index row: `amend_plan.py` | Work item | Append a target file to a Frozen Plan in `plans/` (dry run, section-scoped edits, freeze re-check), then run the structure, path-audit, and overlap checks.
- Work Items row: `amend_plan.py` | `plans/*.md` (excluding `plans/done/`) | Appends one `Implementation Target Files` row and the matching `Freeze status`, Requirement Traceability, `Related target files`, `Affected areas`, step, and `Work Items Created` edits; refuses a file already a target or reference row; keeps `Frozen` only if the four Freeze criteria pass, otherwise sets `Draft`; `--dry-run` writes nothing; `--class` is recorded, never decided by the tool.

### Details
- One line per row, same column counts as the neighbors.

## Compatibility considerations
- N/A: additive rows.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`: passes with the tool present (AC-7).

## Completion criteria
- Both rows exist with correct column counts and `check_tool_descriptions_sync.py` passes (AC-7).

## Out of Scope
- The Index heading count, other tools' rows, and `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Index row and the Work Items row for `tools/amend_plan.py` | Completed | 20261102-140007 | 20261102-140007 | Step 3a: no correction. Changed: tools/TOOL_DESCRIPTIONS.md (Index row, Work Items row). No docs/00_index.md mapping for tools/ files |
| 2 | Run `uv run python tools/check_tool_descriptions_sync.py` | Completed | 20261102-140007 | 20261102-140007 | check_tool_descriptions_sync: No issues found; full suite deferred to plan end |

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
- **Requirement ID**: `REQ-006` (register the tool)
- **Source issue**: issues/20261030-191737_flowimp011_plan-amend-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081027_flowimp011_plan-amend-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085611
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
