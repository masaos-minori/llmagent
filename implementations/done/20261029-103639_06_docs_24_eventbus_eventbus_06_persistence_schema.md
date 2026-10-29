# Implementation Procedure: docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md (Published-at ownership procedure 6)

## Goal

Update the persistence documentation for the frozen plan: document the events table
`published_at` column becoming NOT NULL without a database default (the dead
`strftime(...)` default is removed and existing rows are preserved), the `user_version`
2 -> 3 bump with the reason (`rfc3339-validator` added to the `date-time` format
check), and the publisher-supplied `published_at` with `FormatChecker` (new) validation in the
publish flow.

## Scope

- Update `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` for the schema
  and validation changes.

## Assumptions

- The doc already describes the events table columns; the edit adjusts the
  `published_at` row and adds a short migration note rather than restructuring the page.

## Design decisions

- Follow `skills/python-documentation` conventions when writing: keep the existing page
  structure, update the column table entry, and state behavior changes in the prose the
  surrounding pages already use.

## Alternatives considered

- Adding a new docs page for the ownership change (rejected: the change belongs to the
  existing persistence page).

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. Update the events table description: `published_at` is supplied by the publisher and
   validated by the route; no database default remains.
2. Record the `user_version` 3 value and the migration reason (enforced `date-time`
   format check via `rfc3339-validator`).
3. Note that existing rows are preserved by the change (no-op column edit).

### Method
Inline documentation edit following `skills/python-documentation` (English, existing page
structure preserved).

### Details
- Overlap caveat: `docs/24_eventbus/eventbus_08_reference_api.md` is a target row of
  ebaudit005 and ebtestdrift007; it was verified as not a data-model/ingestion contract
  doc in this plan's Block Log and is not touched by this procedure.

## Compatibility considerations

- Docs must match the shipped schema after rows 1-3 land; update docs in the same
  cycle.

## Security considerations

- None specific.

## Rollback considerations

- Revert the doc edits together with the schema rollback.

## Validation plan

- `uv run python tools/stale_detector.py <this doc>` after the code rows land; docs link
  check via `docs/00_index.md` conventions.

## Completion criteria

- The page describes publisher-supplied `published_at`, no DB default, and user_version
  3 with reason.

## Out of Scope

- Other eventbus docs pages.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261029-154000 | 20261029-160102 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261029-154000 | 20261029-160102 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-154000 | 20261029-160102 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261029-154000 | 20261029-160102 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20261028-122454_ebpubat006_published-at-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-233320_ebpubat006_published-at-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-103639
- **Related target files**: docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md