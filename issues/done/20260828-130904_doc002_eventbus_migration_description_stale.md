# DOC-002: eventbus.sqlite migration description is stale — the implementation has incremental migration, the shared doc says it does not

## Priority
Medium

## Summary
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` states that
`eventbus.sqlite` "does not support backward-compatible migrations" and requires database
recreation for any schema change, grouping it with `rag.sqlite`/`session.sqlite`. This
contradicts the running EventBus service's actual startup path
(`scripts/eventbus/db.py::open_db()` -> `_init_schema()` -> `_migrate()`), which performs
incremental, idempotent `ALTER TABLE`/`CREATE INDEX` migrations against the `events` table on
every startup. The doc must be corrected to describe `eventbus.sqlite`'s actual migration
behavior instead of grouping it with the truly create-only databases.

## Background
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` section 8 documents
`db/create_schema.py::create_schema()`'s DDL-only, `IF NOT EXISTS` initialization for
`rag.sqlite`/`session.sqlite`/`workflow.sqlite`/`eventbus.sqlite`, and section 8a explicitly
carves out `workflow.sqlite` as the sole exception with incremental migration support ("`rag`,
`session`, `eventbus` do not support backward-compatible migrations... applies only to those
three databases"). Separately, `docs/06_eventbus_03_persistence_schema_and_replay.md` already
states "Migrations for existing databases are idempotent" for the `events` table — a claim that
matches the code, but was apparently never reconciled with the shared cross-DB doc's opposite
claim.

## Problem
Two current, code-confirmed facts are in tension with the shared doc's section 8/8a claim:

1. `scripts/db/create_schema.py::create_eventbus_schema()` is indeed create-only (idempotent DDL
   via `build_eventbus_schema_sql()`, no `ALTER TABLE`) — this part of the doc's premise is
   accurate for that specific code path.
2. `scripts/eventbus/db.py::open_db()` — the path the actual running EventBus server uses at
   every startup (`scripts/eventbus/app.py` imports and calls this `open_db()`, not
   `create_schema.py`) — calls `_init_schema()`, which runs `_migrate()` when the `events` table
   already exists. `_migrate()` performs additive `ALTER TABLE ... ADD COLUMN`
   (`delivery_failure_count`, `dlq_requeue_count`), a `ALTER TABLE ... DROP COLUMN retry_count`,
   and `CREATE INDEX IF NOT EXISTS` for two indexes — all idempotent, all against the existing
   `eventbus.sqlite` file, with no Archive/Delete/Recreate involved.

The shared doc's section 8/8a describes only the `create_schema.py` bootstrap path and does not
account for the EventBus service's own `open_db()`/`_migrate()` path, leading it to state
`eventbus.sqlite` "does not support backward-compatible migrations" when the service that owns
that database in fact self-migrates additively on every start.

## Reason for Change
An operator or AI agent following the shared doc's guidance would conclude that any
`eventbus.sqlite` schema change requires the Archive -> Delete -> Recreate procedure (data loss),
when the actual running service already applies additive schema changes safely in place. This
is a correctness-relevant operational documentation gap: it could lead to unnecessary data loss
(recreating a database that did not need it) or to a maintainer wrongly assuming no migration
mechanism exists when one already runs on every EventBus startup.

## Implementation Intent
Documentation-only change. Update
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` section 8 and 8a to:
distinguish the `db/create_schema.py` bootstrap path (still create-only/idempotent-DDL for
`rag.sqlite`/`session.sqlite`, and for `eventbus.sqlite` when invoked directly) from the EventBus
service's own `scripts/eventbus/db.py::open_db()`/`_migrate()` path, which performs incremental,
additive column/index migrations on the `events` table at every service startup. State plainly
that `eventbus.sqlite` does have an incremental migration mechanism, owned by
`scripts/eventbus/db.py`, distinct in form from `workflow.sqlite`'s versioned migration list
(`db/schema_sql.py`) but functionally incremental rather than create-only. Do not claim it
supports arbitrary schema evolution — describe only what `_migrate()` actually does (additive
columns, one column drop, additive indexes), consistent with
`docs/06_eventbus_03_persistence_schema_and_replay.md`'s existing, already-accurate statement.

## Target Files or Areas
- `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` (section 8, section 8a — confirmed stale claim)
- `docs/06_eventbus_03_persistence_schema_and_replay.md` (already accurate; verify no update needed, or cross-reference the corrected shared-doc section)
- Reference for correct current behavior: `scripts/eventbus/db.py` (`_init_schema()`, `_migrate()`), `scripts/eventbus/app.py` (confirms `open_db()` is the live startup path), `scripts/db/create_schema.py::create_eventbus_schema()` (confirms the separate create-only bootstrap path)

## Required Changes
- Correct `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` section 8's blanket claim that `eventbus.sqlite` "does not support backward-compatible migrations," so it no longer groups `eventbus.sqlite` with `rag.sqlite`/`session.sqlite` without qualification.
- Update section 8a to note that `eventbus.sqlite` has its own incremental migration mechanism (`scripts/eventbus/db.py::_migrate()`), separate from `workflow.sqlite`'s versioned migration-list mechanism, and describe the two `eventbus.sqlite` code paths (`create_schema.py` bootstrap vs. `eventbus/db.py` live-service startup) clearly enough that a reader does not conflate them.
- Cross-check `docs/06_eventbus_03_persistence_schema_and_replay.md` for consistency with the corrected shared-doc wording; update only if a genuine gap is found.

## Constraints
Documentation-only: do not modify `scripts/eventbus/db.py`, `scripts/db/create_schema.py`, or any other implementation file as part of this issue.

## Acceptance Criteria
- `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` no longer states that `eventbus.sqlite` lacks an incremental migration mechanism; it accurately describes `scripts/eventbus/db.py::_migrate()`'s additive column/index behavior.
- The doc clearly distinguishes the `create_schema.py` bootstrap path from the EventBus service's own `open_db()`/`_migrate()` startup path for `eventbus.sqlite`.
- `docs/06_eventbus_03_persistence_schema_and_replay.md` and the corrected shared doc do not contradict each other on this point.
- No unverified claim about migration scope (e.g., implying `_migrate()` supports arbitrary future schema changes) is introduced — describe only the confirmed additive-column/drop-column/index behavior.

## Testing Expectations
Not required — documentation-only change with no behavior impact. Manual verification: re-read the updated section against `scripts/eventbus/db.py::_migrate()` and `scripts/eventbus/app.py`'s use of `open_db()`.

## Documentation Impact
Yes. `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` must be corrected as described above. Keep the change to the factual migration-capability statement and the path distinction — do not add the full list of migrated columns/indexes beyond what is needed to describe the mechanism, and do not restate `_migrate()`'s SQL verbatim.

## Out of Scope
- Do not change `scripts/eventbus/db.py`, `scripts/db/create_schema.py`, or any other implementation behavior.
- Do not extend or unify the `create_schema.py` bootstrap path with the `eventbus/db.py` live-migration path — this issue is documentation-only.
- Do not perform a general rewrite of `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` beyond correcting the identified `eventbus.sqlite` claim.

## Dependencies
N/A: none

## Unresolved Questions
- Whether `rag.sqlite`/`session.sqlite` genuinely have no equivalent hidden incremental-migration path elsewhere in the codebase (analogous to `eventbus/db.py` vs. `create_schema.py`) was not verified as part of this issue and should be checked before treating the rest of section 8/8a as fully confirmed.
- Whether the doc should also record why two separate `eventbus.sqlite` initialization paths exist (`create_schema.py` vs. `eventbus/db.py`) as intentional design or as a `Known Issue` — left to the implementer to determine from further evidence or by asking the code owner.

## AI Implementation Instruction
Before editing, re-read `scripts/eventbus/db.py::_init_schema()`/`_migrate()` and confirm
`scripts/eventbus/app.py` still calls `open_db()` at startup (`grep -n "open_db" scripts/eventbus/app.py`), since this issue's evidence may go stale if either changes before implementation. Also spot-check whether `rag.sqlite`/`session.sqlite` have an equivalent hidden migration path before asserting they remain purely create-only in the rewritten text — if unconfirmed, phrase that part conservatively or mark it `Needs Confirmation` rather than repeating the original doc's blanket claim unchanged. Keep the edit minimal: correct the `eventbus.sqlite` claim and add the path distinction only; do not rewrite unrelated sections of the document. Do not modify any file under `scripts/`.
