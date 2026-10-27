# Enforce DLQ redelivery uniqueness with a database constraint

## Priority
Medium

## Summary
Guarantee at the SQLite schema level that one original dead-letter event has at most one redelivery descendant, instead of relying on an application-level existence check and the in-process lock.

## Background
Source: `memo-issue.md` Issue 09, re-verified against current source on 2026-10-27.

- `scripts/eventbus/dlq_repo.py` implements requeue by first running `SELECT 1 FROM events WHERE redelivered_from = ?` and returning `already_redelivered` when a row exists, then inserting the new row with `redelivered_from` set. `Explicit in code`.
- `scripts/eventbus/schema.sql` declares `redelivered_from TEXT` on `events` and only `event_id TEXT NOT NULL UNIQUE`; no unique or partial unique index on `redelivered_from` was found. `Explicit in code` for the column; absence of an index elsewhere (for example in a migration or `create_schema` code) is `Needs confirmation`.
- The check and the insert are serialized by the module-level DB lock for the single shared connection. `Strongly implied by code`.
- Prior work: `issues/done/20261023-154325_eventbus001_dlq-requeue-transactional.md` made requeue transactional; it did not add a constraint.

## Problem
If a second connection or process ever writes to the same database, two requeues of one original event can both pass the existence check and create two descendants.

## Reason for Change
The invariant "at most one successful redelivery per original" is enforced only by the application check and one in-process lock. Today there is a single shared connection, so no duplicate is demonstrated; the constraint removes the dependence on that deployment assumption. No timing pressure.

## Implementation Intent
Make the database the owner of the invariant with a partial unique index on `redelivered_from` (rows where it is not NULL), map a uniqueness violation to the existing typed `already_redelivered` result, and keep the pre-insert check only for friendly classification. Treat the schema change as a versioned change covered by the schema fingerprint validation.

## Target Files or Areas
- `scripts/eventbus/schema.sql`
- `scripts/eventbus/dlq_repo.py`
- `scripts/shared/eventbus_schema_fingerprint.py` and the schema creation and startup validation that use it (`scripts/db/create_schema.py`, `deploy/init_db.sh`, to be confirmed)
- `tests/eventbus/`, `tests/db/`
- ADR-006 and the EventBus schema docs under `docs/24_eventbus/`

## Required Changes
- Confirm no existing constraint on `redelivered_from` anywhere in schema creation or migration code.
- Add a partial unique index on `redelivered_from` and define how existing databases receive it (migration or rebuild) and how existing duplicates, if any, are handled.
- Map the uniqueness conflict to `already_redelivered`.
- Update the schema version and fingerprint, and make fingerprint validation detect removal of the index.
- Record the invariant in ADR-006 and the schema docs.

## Constraints
- Do not change the requeue result vocabulary or the HTTP mapping.
- A startup against a database that already contains duplicate descendants must fail with a clear message or be repaired by a documented procedure, not silently.

## Acceptance Criteria
- Two connections concurrently requeueing one original: exactly one succeeds and the other returns `already_redelivered`.
- Removing the index makes schema fingerprint validation fail.
- ADR-006 and the schema docs state that the database enforces the invariant.

## Testing Expectations
- A concurrency test with two SQLite connections to the same database file.
- Schema creation, fingerprint and startup-gate tests; migration test for an existing database.
- `uv run pytest tests/eventbus tests/db`, mypy, ruff.

## Documentation Impact
Yes. State the invariant and where it is enforced (ADR-006, schema docs); mention the index in the schema description only at the level of "the database enforces uniqueness of the redelivery source".

## Out of Scope
- Multi-process deployment support for EventBus.
- Changing the transaction begin mode beyond what the conflict mapping requires.
- Other DLQ requeue semantics.

## Dependencies
N/A: none open. Schema work may interact with the `ebcompat002` facade removal only through imports; no ordering required.

## Unresolved Questions
- How are existing databases upgraded (in-place `CREATE UNIQUE INDEX` versus rebuild)? `Needs confirmation`: read `scripts/db/create_schema.py` and the startup schema gate.
- Can duplicate descendants already exist in production data? `Needs confirmation`: requires a read-only query on the live database, not run here.

## AI Implementation Instruction
Add only the constraint, its error mapping, versioning and tests. Do not refactor the requeue logic. Check for existing duplicates before writing the migration and stop and report if any exist.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-155850
- **Related target files**: `scripts/eventbus/schema.sql`, `scripts/eventbus/dlq_repo.py`, `scripts/shared/eventbus_schema_fingerprint.py`, `tests/eventbus/`, `tests/db/`, `docs/24_eventbus/`
