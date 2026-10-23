# Create one strict fail-closed startup gate for configuration, schemas, process readiness, and health

## Priority
High

## Summary
Validate the EventBus schema shape (not only `user_version`) at runtime startup and in `deploy/init_db.sh` with one shared validator, preflight configuration and token maps, and make `deploy/setup_services.sh` prove process and health readiness before reporting success.

## Background
Confirmed against HEAD (adversarial re-verification):
- Schema validation exists in two separate code paths. Runtime: `_init_schema()` in `scripts/eventbus/schema.py` returns as soon as `PRAGMA user_version` equals the expected value, so a correctly stamped but malformed database passes; `_matches_current_schema()` (columns only) runs only for an unstamped database (version 0). Deployment: `deploy/init_db.sh` runs `scripts/db/create_schema.py`, whose `create_eventbus_schema()` compares only the version number and then runs `executescript(build_eventbus_schema_sql())` (all `CREATE ... IF NOT EXISTS`), which silently adds missing tables and indexes but never verifies shape; the script then only prints `sqlite3 ... .tables`. Workflow is the only database with a table-presence check in `init_db.sh`.
- `deploy/setup_services.sh` starts EventBus in the background (`... python -m eventbus.app &`), records the PID, prints the output of one `sleep 2 && curl /health` (or `まだ起動中`) and then prints `Event Bus (:8015, PID ...): started` unconditionally. It never checks that the process is alive or that health is 200.
- `/health` returns HTTP 503 whenever any degraded reason exists, including `lock_wait_high`, `query_duration_high`, `broker_queue_backlog_high` and `slow_consumers_detected` (`scripts/eventbus/health_route.py`). A gate that requires `status == ok` would therefore also fail a healthy start on a transient capacity signal.
- The import-linter contract `eventbus-is-isolated` forbids `eventbus` from importing `db` (it may import `shared`). One shared validator therefore cannot simply live in `scripts/db/` or be called from `scripts/eventbus/schema.py` both ways: the shared piece belongs in `shared/` (or the SQL is read by both with the validator in `shared/`).
- `scripts/eventbus/schema.sql` currently defines tables and indexes only (no triggers).
A schema version marker (`PRAGMA user_version`) was added by earlier compat-removal work; this issue covers shape validation beyond it. Aggregated from the memo's strict schema-shape validation and deployment fail-closed items.

## Problem
A correct version stamp does not prove that tables, indexes, constraints or triggers exist, so a malformed database can start and fail only when a route touches a missing object. Deployment can report success without proving that configuration, token maps, all database schemas, the EventBus process and the health endpoint are ready; HTTP 503, an immediate process exit or an incomplete database must not be summarized as success. Initialization validates some databases more strictly than others.

## Reason for Change
Runtime startup and deployment initialization must share one definition of a valid schema, and every boundary must fail closed with an actionable diagnostic.

## Implementation Intent
Build one reusable preflight and readiness chain: load and validate production configuration, build token maps, validate all required database schemas against a canonical fingerprint derived from `schema.sql`, start the process, then verify liveness and readiness with bounded polling. Report only verified states.

## Target Files or Areas
`scripts/eventbus/schema.py`, `scripts/eventbus/schema.sql`, `scripts/db/create_schema.py`, `scripts/db/schema_sql.py`, a new shared validator under `shared/` (location is a decision, see Unresolved Questions), `scripts/eventbus/config.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/health_route.py`, `deploy/init_db.sh`, `deploy/setup_services.sh`, `deploy/load_env.sh`, `.importlinter`, tests `tests/eventbus/test_eventbus_schema_version.py`, `test_eventbus_db_migration.py`, `test_eventbus_startup.py`, deployment shell tests.

## Required Changes
- Create a canonical EventBus schema fingerprint from `schema.sql` (tables, columns, types, nullability, defaults, primary keys, indexes, unique constraints, triggers, foreign keys as applicable) and validate it even when `user_version` matches.
- Use the same strict validator in runtime startup and `init_db.sh`; validate every required database, not only Workflow.
- Preflight production configuration through token-map generation.
- Add bounded process and health polling to `setup_services.sh`: process exit, connection failure, non-200 or `status != ok` is fatal; clean up the failed child, print the last health response and the log location.
- Report only verified states in the deployment summary.

## Constraints
A database stamped with another version stays refused (recreate, never migrate). Deployment scripts must stay non-interactive and must not print secrets.
The import-linter contracts (`eventbus` must not import `db`; `eventbus` may import `shared`) must keep passing. The deployment readiness gate must use a readiness signal that does not fail on transient capacity degradation (see M-02's liveness/readiness/integrity split), not the full `/health` `status == ok`.
The import-linter contracts (`eventbus` must not import `db`; `eventbus` may import `shared`) must keep passing. The deployment readiness gate must use a readiness signal that does not fail on transient capacity degradation (see M-02's liveness/readiness/integrity split), not the full `/health` `status == ok`.

## Acceptance Criteria
- A correctly stamped but malformed database is rejected and runtime and deployment validation give equivalent results.
- HTTP 503 is never treated as deployment success and an immediate EventBus process crash is detected.
- An incomplete database blocks service startup; a successful deployment is followed by a usable EventBus API.
- The deployment readiness gate does not fail a healthy start on transient capacity degradation (`lock_wait_high`, `slow_consumers_detected`).

## Testing Expectations
Matching version with a missing table, a changed column and a missing index; unstamped matching and mismatching databases; configuration or token-map preflight failure; immediate process crash; health 503 and health timeout; valid end-to-end startup. Shell integration tests where scripts change.

## Documentation Impact
Yes: the schema fingerprint policy, the startup and deployment readiness sequence, and the failure behavior of each gate.

## Out of Scope
Schema migration support; changes to the table design itself; the authorization loader fix (H-02) except the shared preflight call.

## Dependencies
Depends on H-02 for a correct configuration load before the token-map preflight is meaningful, and on the readiness definition in M-02 for the deployment gate. Both are open issues in `issues/` (`eventbus002`, `eventbus007`). No other open issue overlaps.

## Unresolved Questions
- Where does the shared validator live (`shared/` is the only location both `eventbus` and `db` may import)? Needs confirmation against `.importlinter`.
- Which constructs belong in the schema fingerprint (tables, columns, types, nullability, defaults, primary keys, indexes, unique constraints, foreign keys; triggers only if `schema.sql` gains any)? Owner decision.
- Which health condition is the deployment readiness gate (database reachable and DLQ task running, versus full `status == ok`)? Depends on M-02.
- Should `create_eventbus_schema()` keep its current idempotent repair behavior (adds missing tables on re-run) or fail on a malformed stamped database? Needs confirmation; a silent repair conflicts with the fail-closed goal.

## AI Implementation Instruction
- Read the listed implementation, tests, and design documents before editing; keep changes minimal and do not rewrite unrelated files.
- Preserve the existing public contract unless this issue explicitly names a contract change; an unresolved owner decision is reported, not guessed.
- Do not resolve an implementation defect by changing documentation alone.
- Keep transaction, locking, authorization, durability and fail-closed boundaries explicit.
- Add or update automated tests for every acceptance criterion; do not implement out-of-scope items.

## Traceability
- **Workflow phase**: `issue-creator` (converted from `memo-issue.md`, task `H-03`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-154326
- **Related target files**: `scripts/eventbus/schema.py`, `scripts/eventbus/schema.sql`, `deploy/init_db.sh`, `deploy/setup_services.sh`
