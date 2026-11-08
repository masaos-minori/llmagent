## Goal
Correct the startup-validation section of the migration-and-scaling doc so the accepted-shape list
names all five current workflow tables including `tool_call_state` (`REQ-004`); this row was added
by the 2026-11-08 plan amendment after a fourth stale list was found in `docs/41_db`.

## Scope
**Release unit**: wfaudit003-full (Phase 2)

- Covers Plan `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md` row 7 (amendment
  2026-11-08): `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, section 8a
  (accepted-tables sentence at L45).
- Documentation-only change; no code or test edits.

## Assumptions
- Procedures `144827_01`-`144827_03` land with this document; the doc describes the post-change
  gate behavior.
- The same file already states `execution_snapshots` is retired (section on the retirement,
  confirmed during verification); this edit must not contradict that — it only extends the
  accepted-tables list.

## Design decisions
- Keep the sentence structure identical and only extend the parenthesized list: the section's
  purpose is the no-migration policy statement, and the list is its shape reference.
- Do not add column names: the sentence says "and their required columns" generically, and per the
  docs content policy column shapes live in `scripts/db/schema_sql.py`.

## Alternatives considered
- Rewording the section to "the five tables the gate requires" with a cross-link to the gate
  module: rejected — the consistency checker verifies symbol references against `scripts/`, and a
  new cross-link for a one-word fix adds maintenance without fixing a wrong claim.
- Removing the explicit list entirely: rejected — the list is the operator-facing definition of
  the accepted shape in this doc family.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` — section 8a, L45.

### Procedure
Extend the parenthesized table list in the first sentence of section 8a.

### Method
Replace:

> `workflow.sqlite` is accepted only when the current required tables (`tasks`, `attempts`,
> `processed_events`, `artifacts`) and their required columns are present.

with:

> `workflow.sqlite` is accepted only when the current required tables (`tasks`, `attempts`,
> `processed_events`, `artifacts`, `tool_call_state`) and their required columns are present.

### Details
- Single list extension in one sentence; the legacy-marker sentences that follow stay untouched.

## Compatibility considerations
- N/A: documentation-only change. `wfaudit010`'s retirement note in this file (the
  `execution_snapshots` history) is preserved and is consistent with a five-table required set.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- Reverting this document alone is safe; the `REQ-004` acceptance grep over `docs/41_db` would flag
  the stale four-table claim if the gate change lands without it.

## Validation plan
- Docs checkers per `routing.md`:
  - `uv run python tools/check_docs_quality.py`
  - `uv run python tools/check_docs_structure.py docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
  - `uv run python tools/check_docs_consistency.py --domain db`
- Acceptance grep: `grep -rn "tasks.*attempts.*processed_events.*artifacts" docs/41_db docs/90_deployment`
  shows only five-table forms after procedures 04-07 land.

## Completion criteria
- Section 8a lists five tables; docs checkers exit 0; no four-table form remains in `docs/41_db`.

## Out of Scope
- The rest of this document (no-migration policy narrative, eventbus validation section 8b, and
  the `execution_snapshots` retirement history already present).

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
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`