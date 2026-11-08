## Goal
Correct the `workflow.sqlite` schema-reference paragraph in the db schema-reference doc so the
created-tables list names all five current tables, matching the post-`wfaudit010` DDL and the
extended startup gate (`REQ-004`).

## Scope
**Release unit**: wfaudit003-full (Phase 2)

- Covers Plan `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md` row 3 only:
  `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, section 7 (the table list at
  L46).
- Documentation-only change; no code or test edits.

## Assumptions
- Procedures `144827_01`-`144827_03` (gate + shell mirrors) land with this document; the doc
  describes the post-change state, matching this repository's documentation policy.
- Sibling procedure `134201_04` (wfaudit001 processed-events retention narrative for the same
  file) edits the same section 7 text block; it has the lower seq and lands first. The two edits
  touch disjoint sentences — this one rewrites only the created-tables sentence.

## Design decisions
- Rename the list's subject from "Task tables" to "Task and tool-state tables" rather than
  appending `tool_call_state` under a "task tables" label — `tool_call_state` is not a task table,
  and the sentence should not imply it is.
- Keep the rest of the long section-7 paragraph (status CHECK constraints, gate/markers sentence,
  recovery link) untouched; the gate sentence there already describes shape-and-columns acceptance
  in general terms that stay true after the gate extension.

## Alternatives considered
- Leaving the sentence as-is because it already mentions `tool_call_state.state` later in the
  same line: rejected — the created-tables list is the doc's authoritative enumeration and would
  still read as a four-table set.
- Adding a per-table column list to this paragraph: rejected — column shapes are owned by
  `schema_sql.py` per the docs content policy (`skills/DESIGN.md`); the doc points at the DDL file
  instead.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md` — section 7, created-tables
sentence (L46).

### Procedure
Rewrite the first list sentence in the section-7 paragraph.

### Method
Replace:

> Task tables (tasks, attempts, processed_events, artifacts) are created with `CREATE TABLE IF
> NOT EXISTS` (DDL in `scripts/db/schema_sql.py`).

with:

> Task and tool-state tables (tasks, attempts, processed_events, artifacts, tool_call_state) are
> created with `CREATE TABLE IF NOT EXISTS` (DDL in `scripts/db/schema_sql.py`).

### Details
- Single-sentence rewrite; sentence count and paragraph structure unchanged.
- The paragraph's later clause "the pattern already established for `tool_call_state.state`"
  becomes consistent with the enumeration above it.

## Compatibility considerations
- N/A: documentation-only change. Cross-check with `wfaudit010`'s doc edits confirmed the doc
  nowhere describes `execution_snapshots` as required.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- Reverting this document alone is safe; if procedures 01-03 land without it, the acceptance grep
  (`REQ-004`) and `check_docs_consistency.py` would flag the stale four-table claim.

## Validation plan
- `uv run pytest tests/ -q` not required for this file; docs checkers per `routing.md`:
  - `uv run python tools/check_docs_quality.py`
  - `uv run python tools/check_docs_structure.py docs/41_db/db_02_architecture_and_schema-schema-reference.md`
  - `uv run python tools/check_docs_consistency.py --domain db`
- Acceptance grep: `grep -rn "tasks.*attempts.*processed_events.*artifacts" docs/41_db docs/90_deployment`
  shows only five-table forms after procedures 04-07 land.

## Completion criteria
- Section 7 lists five tables; docs checkers exit 0; the acceptance grep contains no four-table
  form in `docs/41_db`.

## Out of Scope
- Other sections of this document (including the retention narrative handled by sibling
  `134201_04`), the gate code, and the deploy scripts.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-072224 | 20261109-072224 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261109-072224 | 20261109-072224 | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-072224 | 20261109-072224 | Docs checkers |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-072224 | 20261109-072224 | This document is the documentation change |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261107-203216_wfaudit003_schema-gate-table-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-144827
- **Related target files**: `docs/41_db/db_02_architecture_and_schema-schema-reference.md`