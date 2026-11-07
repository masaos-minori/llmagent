## Goal

- tests/db/test_db_public_api.py — remove db.store facade tests (AC-001, REQ-003)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Delete the facade tests rather than repoint them: the kept `db`-module `__all__` tests already guard the direct-import surface (REQ-003).

## Alternatives considered

- Convert the store tests into `db`-module assertions: rejected — duplicate coverage; the surface is already tested (REQ-003).

## Implementation
### Target file
`tests/db/test_db_public_api.py`
### Procedure
1. Delete the `db.store` reload fixture (lines 24-31) if, after removing the three
   tests below, no remaining test consumes it; if a shared fixture helper is also used
   by the kept `db`-module tests, strip only its `db.store` reload step.
2. Delete the three store-facade tests entirely:
   - `test_store_all_exists` (36-40),
   - `test_store_all_symbols_exist` (46-52),
   - `test_store_wildcard_import_works` (62-67).
3. Do not touch the `db`-module `__all__` and wildcard tests or any other test in the file:
   the package-level direct-import surface stays (plan Assumptions).
4. Verification finding (2026-11-07): the module docstring line 4 (`- __all__ exists in
   db.store and db.__init__`) names the deleted facade — update it to name only the `db`
   package surface. The fixture is used by the kept `db`-module tests, so apply the
   strip-only variant of step 1 (the whole fixture stays; its saved/del/yield/restore
   targets become just `db`).
### Method
REQ-003 / AC-001. The file guards the public import surface of `scripts/db`: a fixture
region (lines 24-31) reloads `db.store` for facade tests, and three tests assert the
facade exists — `test_store_all_exists` (36-40), `test_store_all_symbols_exist`
(46-52), `test_store_wildcard_import_works` (62-67). The `db`-module-level `__all__`
and wildcard tests cover the direct-import surface (`db/__init__.py` imports
submodules directly at lines 49-60) and must keep passing.
### Details
Test deletions only; the kept tests are untouched.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: nothing (Phase 2 of the `facade-cutover` unit; must land before sibling documents 01
  deletes the file these tests reference).
  - Blocks: sibling documents 01, 11, 26.

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: `grep -n "db\.store\b" tests/db/test_db_public_api.py | grep -v store_impl | grep -v store_protocols`
  Expected: no matches.
- Command: `uv run pytest tests/db/test_db_public_api.py -q`
  Expected: pass with the remaining `db`-module tests intact (AC-001).
  still guard `__all__` completeness.

## Completion criteria

- no test references the deleted facade; the package surface tests (AC-001, REQ-003)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the three store-facade tests in `tests/db/test_db_public_api.py` — Plan Phase 2 | Completed | 20261107-164339 | 20261107-164339 | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Completed | 20261107-164339 | 20261107-164339 |  |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Completed | 20261107-164339 | 20261107-164339 |  |

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
- **Requirement ID**: REQ-003 / AC-001
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `tests/db/test_db_public_api.py`