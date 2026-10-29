# Implementation Procedure: scripts/eventbus/schema.sql (Published-at ownership procedure 3)

## Goal

Remove the dead database-side `published_at` default from the events table and bump
`user_version` to 3 so the migration path is pinned.

## Scope

- Drop the `DEFAULT (strftime(...))` clause from the `events` table `published_at`
  column definition.
- Bump `PRAGMA user_version` in `scripts/eventbus/schema.sql` from 2 to 3.

## Assumptions

- `published_at` is already NOT NULL (`schema.sql:9`); the default clause is dead code
  because both INSERTs pass the column explicitly (`event_repo.py:36-37`,
  `dlq_repo.py:104`).
- `scripts/init_db.sh` applies `CREATE TABLE IF NOT EXISTS` with `PRAGMA
  foreign_keys = ON`, not `PRAGMA user_version`, so the bump must be handled in the
  migration path.

## Design decisions

- Follow the plan's migration shape: the column change is a no-op on existing rows, so
  no rebuild is needed for the column itself.

## Alternatives considered

- None in this cycle (issue already deferred the larger ALTER TABLE migration to a
  follow-up issue).

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. Edit the `published_at` column line: `published_at TEXT NOT NULL,` (remove the
   `DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ'))` clause).
2. Change `PRAGMA user_version = 2;` to `PRAGMA user_version = 3;` (`schema.sql:45`).
3. Do not add a new index here; `idx_events_redelivered_from` already exists at
   `schema.sql:21` (added by commit `a711abe1f`).

### Method
Inline edit of two lines in the single schema file.

### Details
- The plan's "Add index (if missing)" step is already satisfied; recorded in the plan's
  Blocker Log.
- `user_version` 3 reasons (recorded in the plan and docs row 6): the `date-time`
  format check becomes enforced via `rfc3339-validator`.

## Compatibility considerations

- Existing databases with `user_version = 2` must be bumped to 3 when the migration is
  applied; the version-pin test (row 7) enforces the new value.

## Security considerations

- None specific.

## Rollback considerations

- Restore the DEFAULT clause and `user_version = 2` together with the route/repo
  rollbacks (rows 1-2) so the server-side default path remains functional.

## Validation plan

- `tests/eventbus/test_eventbus_schema_version.py` version pin updated to 3 (row 7);
  existing schema tests stay green.

## Completion criteria

- Schema has no `strftime` default on `published_at`; `user_version = 3`; eventbus test
  suite green.

## Out of Scope

- Index additions (verified unnecessary in this cycle).
- Larger ALTER TABLE migrations (deferred follow-up issue per the plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261028-122454_ebpubat006_published-at-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-233320_ebpubat006_published-at-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-103639
- **Related target files**: scripts/eventbus/schema.sql
