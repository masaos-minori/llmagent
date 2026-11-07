## Goal

- scripts/eventbus/README.md — reverse the stub-module decision (AC-005, REQ-007)

## Scope
**Release unit**: N/A: outside the facade-cutover unit

- Phase 3 documentation only; it follows the Phase 1-2 unit and changes no code. Checker-config consolidation stays with compatrm004 (Plan Release unit row).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Rewrite the section instead of deleting it: the reversed 2026-10-27 decision must stay auditable.

## Alternatives considered

- Delete the stub-module section entirely: rejected — the reversed decision needs an audit trail.

## Implementation
### Target file
`scripts/eventbus/README.md`
### Procedure
1. Replace the whole section (lines 15-21, from `## Stub Module Pattern` through the
   Decision line) with:
   ```markdown
   ## Module Import Pattern

   Each layer module is the public import surface for its own operations: connection
   operations from `db_conn.py`, event operations from `event_repo.py`, delivery
   operations from `delivery_repo.py`, and DLQ operations from `dlq_repo.py`.

   **Rule**: Import each operation from its owning layer module. Do not add re-export
   stubs.

   **Decision (2026-11-07)**: The `db.py` stub facade and its "Retain this facade"
   decision (2026-10-27) are reversed: all consumers, including
   `scripts/agent/services/*`, import the layer modules directly.
   ```
2. Leave the numbered layer-module list (lines 7-13) and the rest of the README
   unchanged.
### Method
REQ-007 / AC-005. The "Stub Module Pattern" section (lines 15-21) mandates the facade:
- line 17: "`db.py` is a stub module that re-exports functions ... single entry point"
- line 19: "**Rule**: Do not add new functions here. Add them to the appropriate layer
  module and re-export from this stub."
- line 21: "**Decision (2026-10-27)**: Retain this facade as the single entry point for
  the eventbus module; all consumer imports, including `scripts/agent/services/*`, go
  through it."

compatrm003 deletes the stub (docs 02) and every production module already imports the
layer modules directly, so the section must be reversed.
Verification finding (2026-11-07): `scripts/agent/services/*` does not import `eventbus`
at all (grep before and after the cutover); the new Decision line inherits the frozen
plan wording that names it — kept as-is, it states the rule for any future consumer.
### Details
Prose only.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: sibling documents 02-10 (the README documents the module-direct import pattern that
  those docs implement).
  - Blocks: none.

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Revert the documentation commit.

## Validation plan

- Command: `grep -n "Stub Module\|Retain this facade" scripts/eventbus/README.md`
  Expected: no matches other than the historical note inside the new Decision line.
- Command: `python3 tools/check_docs_links.py`
  Expected: no broken links (the README is scanned as a module document).
  decision (AC-005).

## Completion criteria

- the README prescribes module-direct imports and records the reversed (AC-005, REQ-007)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reverse the stub-module section in `scripts/eventbus/README.md` — Plan Phase 3 | Completed | 20261107-164122 | 20261107-164122 | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Completed | 20261107-164122 | 20261107-164122 |  |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Completed | 20261107-164122 | 20261107-164122 |  |

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
- **Requirement ID**: REQ-007 / AC-005
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `scripts/eventbus/README.md`