## Goal
Correct the supported-baseline list in the db recovery-and-reference doc so the `workflow.sqlite`
row names all five current tables including `tool_call_state` (`REQ-004`).

## Scope
**Release unit**: wfaudit003-full (Phase 2)

- Covers Plan `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md` row 4 only:
  `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, the baseline bullet at L143.
- Documentation-only change; no code or test edits.

## Assumptions
- Procedures `144827_01`-`144827_03` land with this document; the bullet describes the post-change
  accepted shape that fails-or-passes startup.
- Sibling procedures `134201_05` (wfaudit001) and `135741_04` (wfaudit007) also edit this file;
  they have lower seqs, land first, and touch disjoint regions (retention/recovery narrative
  around L85-93 and later sections). This edit changes only the L143 baseline bullet.

## Design decisions
- Extend the bullet in place: the bullet is the canonical "what a healthy baseline looks like"
  enumeration used by the DB-recreation runbook, so it must equal the gate's required set.
- Keep the trailing clause "a legacy marker table or a shape difference fails startup" unchanged —
  it already covers refusal behavior generically.

## Alternatives considered
- Rewriting the bullet as a pointer to the gate module instead of an explicit list: rejected — the
  runbook's value is that an operator can compare `sqlite3 .tables` output against a written list
  without reading code.
- Adding the `tool_call_state` column list to the bullet: rejected — column shapes belong to
  `scripts/db/schema_sql.py` per the docs content policy.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md` — baseline bullet (L143).

### Procedure
Extend the table list in the `workflow.sqlite` baseline bullet.

### Method
Replace:

> - `workflow.sqlite`: `tasks`, `attempts`, `processed_events`, `artifacts` present, and no
>   `schema_migrations` or `workflow_schema_version` table; a legacy marker table or a shape
>   difference fails startup.

with:

> - `workflow.sqlite`: `tasks`, `attempts`, `processed_events`, `artifacts`, `tool_call_state`
>   present, and no `schema_migrations` or `workflow_schema_version` table; a legacy marker table
>   or a shape difference fails startup.

### Details
- Single list extension inside one bullet; the `eventbus.sqlite` and `mdq.sqlite` bullets below it
  stay untouched.

## Compatibility considerations
- N/A: documentation-only change. The doc's DB-recreation procedure (section 11) already recreates
  via `create_workflow_schema()`, which creates `tool_call_state`, so the runbook stays executable
  after the gate change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- Reverting this document alone is safe; the `REQ-004` acceptance grep would flag the stale
  four-table form if procedures 01-03 land without it.

## Validation plan
- Docs checkers per `routing.md`:
  - `uv run python tools/check_docs_quality.py`
  - `uv run python tools/check_docs_structure.py docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
  - `uv run python tools/check_docs_consistency.py --domain db`
- Acceptance grep: `grep -rn "tasks.*attempts.*processed_events.*artifacts" docs/41_db docs/90_deployment`
  shows only five-table forms after procedures 04-07 land.

## Completion criteria
- The baseline bullet lists five tables; docs checkers exit 0; no four-table form remains in
  `docs/41_db`.

## Out of Scope
- Recovery-narrative regions owned by sibling procedures `134201_05` and `135741_04`, and the
  eventbus/mdq baseline bullets.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docs checkers |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document is the documentation change |

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
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
