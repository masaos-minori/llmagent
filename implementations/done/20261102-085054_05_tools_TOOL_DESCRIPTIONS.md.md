## Goal
- Register `tools/scan_change_consumers.py` in `tools/TOOL_DESCRIPTIONS.md` (`REQ-005`: tool registered, sync check passes).

## Scope
- In scope: one row in the Index table and one row in the "Work Items" table of the one file. Out of scope: other rows, the Index heading count, and the `run_validation_gates.py` rows another Plan edits.

## Assumptions
- Step 3a verification: `check_tool_descriptions_sync.py` cross-checks `tools/*.py` against backticked `*.py` names in the file (no count check); the Index heading says "61 modules" while 69 `tools/*.py` files exist, so the count is already stale. Do not touch the count here (sibling Plans add rows at the same time).
- The `## Work Items` section (target/description columns) lists work-item tools, e.g. `check_plan_target_overlaps.py`; the new tool is a planning-time work-item helper, so it goes there and in the Index with category `Work item`.
- Overlap (Step 2): `tools/TOOL_DESCRIPTIONS.md` is also a target of the Plans filed from `flowimp003`, `flowimp005`, `flowimp007`, `flowimp008`, `flowimp010`, and `flowimp011`. Judged compatible: each adds its own row or updates different existing rows (flowimp005 edits the two `run_validation_gates.py` rows). Source plan A7 and A9 record it. Locate rows by text, not line number.
- Names the tool created by row 01 (earlier-`seq`).

## Design decisions
- Insert each new row next to the `check_plan_target_overlaps.py` row of the same table to keep related tools adjacent.
- Keep each row on one line and keep the column count of its table.

## Alternatives considered
- N/A: registration fixed by the Plan.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Add the Index row after `check_plan_target_overlaps.py` (3 columns: file, category, purpose).
2. Add the "Work Items" row after that table's `check_plan_target_overlaps.py` row (3 columns: file, target, description).

### Method
- Index row: `scan_change_consumers.py` | Work item | Read-only planning aid: list candidate direct and indirect consumers of a schema, API, or constant change (candidates only).
- Work Items row: target `scripts/`, `tests/`, `tools/`, `deploy/`, `docs/` via `git ls-files`, optional `.testmondata`; description states the categories, the candidates-only and absence-is-not-evidence notice, the testmon state line, `--seed`, `--format text|json` (escape the pipe as `\|`), `--report`, exit code 0, read-only.

### Details
- Use the same escaping for `|` inside table cells as the neighboring rows.

## Compatibility considerations
- N/A: additive rows.

## Security considerations
- N/A: documentation-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`

## Completion criteria
- Both rows exist and the sync checker passes with the tool present.

## Out of Scope
- The Index count, other tools' rows, and `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Index row and the Work Items row | Completed | 2026-11-02 | 2026-11-02 | Added Index row and Work Items row after check_plan_target_overlaps rows; files changed: tools/TOOL_DESCRIPTIONS.md |
| 2 | Run `check_tool_descriptions_sync.py` | Completed | 2026-11-02 | 2026-11-02 | check_tool_descriptions_sync: No issues found; tests/tools targeted run (testmon-forceselect) 55 passed; full suite deferred to plan end; docs N/A: no docs/*.md edit |

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
- **Requirement ID**: `REQ-005` (register the tool)
- **Source issue**: issues/20261030-191006_flowimp001_consumer-impact-scan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080004_flowimp001_consumer-impact-scan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085054
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
