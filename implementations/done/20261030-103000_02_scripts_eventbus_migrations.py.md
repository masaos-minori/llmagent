# Implementation Procedure: eventbus migrations.py dlq_outbox step

## Goal

Register the `eventbus_dlq_outbox` (new) forward migration step (registry head → head+1) in
`scripts/eventbus/migrations.py` so the outbox table upgrades existing databases only through
the dbmig001 framework (REQ-010; plan AC-7).

## Scope

**In scope:**
- `scripts/eventbus/migrations.py`: append one `MigrationSpec` (new) to `REGISTRY`.

**Out of scope:**
- Framework core (dbmig001 row 01), baseline DDL (row 01 of this plan), startup wiring/CLI
  (dbmig001 rows 03/05 — already consume `REGISTRY`, no change needed there).

## Assumptions
- Hard gate: this row runs only after dbmig001 rows 01 (`shared/db_migrations.py` with
  `MigrationSpec` (new)/`MigrationRunner` (new)), 02 (`REGISTRY` + `eventbus_ledger_baseline` (new) 3→4) and
  04 (baseline stamp 4) are implemented. Verified at HEAD `124e340b4`: the module does not
  exist yet — it is created by dbmig001 row 02; this row appends to that file.
- Version numbering: registry head after dbmig001 is 4, so this step is `4 → 5` and matches
  row 01's baseline stamp. If dbmig001 lands a different head, use head → head+1 consistently.

## Design decisions
- Spec fields per the framework contract (dbmig001 row 01): `id="eventbus_dlq_outbox"`,
  `from_version=4`, `to_version=5`, preconditions check `PRAGMA user_version == 4` and the
  schema fingerprint passes, `mutation_sql` (new) is the exact DDL+index text of row 01 plus
  `PRAGMA user_version = 5;`, postcondition runs `shared.eventbus_schema_fingerprint.assert_matches`
  (stamping lives inside the step SQL — the runner never writes `user_version` itself).
- Registration is a plain append to the ordered `REGISTRY`; insertion order defines the path
  (dbmig001 row 02 design).
- Corrected at implementation (2026-10-31): "the schema fingerprint passes" cannot be a
  precondition of this step — mid-apply the database legitimately lacks `dlq_outbox`, and the
  runner's `ensure_ledger` creates `schema_migrations` before any step precondition runs.
  The implemented `_precondition_outbox_step` instead refuses unless: `user_version == 4`,
  `schema_migrations` is present (rejects a forged stamp), the core eventbus tables are
  present, and `dlq_outbox` is absent (step already applied). Full-shape fingerprint
  validation stays where the document intends it: the step postcondition
  (`assert_matches`) and startup `schema.py::_init_schema`.

## Alternatives considered
- Ad-hoc `CREATE TABLE IF NOT EXISTS` at startup: forbidden by REQ-010 and rejected —
  unregistered mutation of an existing canonical database.

## Implementation
### Target file
`scripts/eventbus/migrations.py` (new)

### Procedure
1. Define the `eventbus_dlq_outbox` (new) `MigrationSpec` (new) with the contract above.
2. Append it to `REGISTRY` after `eventbus_ledger_baseline` (new).

### Method
One spec constant + one registry append; SQL text byte-identical to row 01's appended DDL.

### Details
- Supporting test edits ride on `tests/eventbus/test_eventbus_migrations.py` (created by
  dbmig001 row 15; non-target row, disclosed in plan UNK-04): add cases that (a) a
  data-bearing version-4 database migrates to 5 with `dlq_outbox` (new) present and rows
  preserved, (b) a fresh baseline database and the migrated database are fingerprint-equal,
  (c) an outbox-then-ledger order is impossible (registry order enforced), (d) unknown
  targets still refuse.
- Implemented at `452a7335b` (2026-10-31): dbmig001 landed on `origin/master`; registry head
  is 4, so the appended step is `4 → 5` exactly as planned. The `mutation_sql` stamp
  (`PRAGMA user_version = 5;`) lives inside the SQL string, matching the bootstrap step's
  style. Ledger-content assertions in tests are order-insensitive (sets) because
  `read_ledger` orders by `applied_at` then `id`, so same-second steps tie alphabetically.
- The bootstrap step (`eventbus_ledger_baseline`) postcondition was re-scoped to
  `_postcondition_ledger_baseline` (ledger + baseline tables) rather than full
  `assert_matches`: once `dlq_outbox` joins schema.sql, the full fingerprint (built from
  schema.sql) cannot match an intermediate version-4 database mid-path. The full-shape check
  remains at the path end (this step's postcondition) and at startup.

## Compatibility considerations
- Databases already at the new baseline (fresh installs) skip the step; version-3 databases
  take the two-step path 3→4→5 through the ledger.

## Security considerations
- Static in-repo SQL; values never interpolated from user input.

## Rollback considerations
- Forward-only framework: rollback is code revert plus restore-from-backup per the gate;
  no down-migration exists by design.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_migrations.py
  tests/db/test_eventbus_schema_equivalence.py` (row 15 harness applies the step against a
  data-bearing baseline with fault injection between backup and migration).

## Completion criteria
- A version-4 EventBus database upgrades to the new baseline via one registered, ledger-
  recorded, gate-gated step with all rows preserved; fingerprint equivalence holds.

## Out of Scope
- Runtime outbox behavior (rows 03-06), baseline DDL text ownership (row 01), docs (rows 12-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `eventbus_dlq_outbox` (new) spec to `REGISTRY` | Completed | 20261031-063000 | 20261031-064039 | Gated on dbmig001 rows 01/02/04 4->5 appended after eventbus_ledger_baseline; precondition corrected (version+ledger+core tables+no dlq_outbox) |
| 2 | Add migration tests to `tests/eventbus/test_eventbus_migrations.py` | Completed | 20261031-063000 | 20261031-064039 | Disclosed non-target test file (UNK-04) TestEventbusOutboxStep: v4-with-data migration, fresh-vs-migrated fingerprint equality, registry-order refusal, precondition refusal |
| 3 | Run migration + equivalence tests | Completed | 20261031-063000 | 20261031-064039 | targeted pytest passed; tests/db/test_eventbus_schema_equivalence.py 3 passed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | dbmig001 framework/registry not yet implemented | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-010`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `scripts/eventbus/migrations.py`