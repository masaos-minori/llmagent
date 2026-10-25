# Plan: One shared EventBus schema fingerprint with fail-closed runtime/startup validation and a bounded process+health readiness gate

## Goal
Validate the EventBus schema shape (not only `PRAGMA user_version`) at runtime startup and in `deploy/init_db.sh` with one shared validator, preflight configuration and token maps, and make `deploy/setup_services.sh` prove process and health readiness before reporting success, so a malformed database, a broken config, an immediate process crash, or an HTTP 503 is never summarized as a successful start.

## Priority
High

## Scope
- **In-Scope**:
  - Create one canonical EventBus schema fingerprint validator under `scripts/shared/` that derives tables, columns (name/type/nullability/default/pk), indexes, table-level constraints, foreign keys, and triggers (if any) from `scripts/eventbus/schema.sql` via `PRAGMA` on a fresh in-memory apply and compares them against a target connection, raising on any mismatch.
  - Make `scripts/eventbus/schema.py::_init_schema()` validate shape against the shared fingerprint even when `user_version` matches, not only for an unstamped database.
  - Make `scripts/db/create_schema.py::create_eventbus_schema()` fail closed on a malformed database already stamped with the current version while keeping the v0 legacy repair path.
  - Make `deploy/init_db.sh` validate every required database (rag, session, workflow, EventBus) shape via the shared validator and abort on mismatch, replacing the bare `.tables` print for EventBus.
  - Make `deploy/setup_services.sh` prove EventBus process liveness and readiness with bounded polling: process exit, connection failure, non-200, or `status != ok` is fatal with child cleanup and last-response logging; exclude transient capacity-degradation signals.
  - Add a config/token-map preflight to `deploy/load_env.sh` that builds token maps via the existing `auth._populate_token_maps()` and cross-checks against config before startup, keeping `require_env_vars` as the presence gate.
  - Update the non-canonical patched EventBus shapes in `tests/db/test_create_schema.py` so strict validation passes, and fix the old-shape expectation under strict validation.
  - Add startup/readiness and deployment shell/integration tests for every acceptance criterion.
  - Correct the overstatement in `docs/90_deployment/deployment_01_deployment.md` that `init_db.sh` verifies all mandatory EventBus tables and the service refuses a different table shape.
- **Out-of-Scope**:
  - Schema migration support or any change to the table design itself.
  - The authorization loader fix (H-02, eventbus002) beyond reusing the shared preflight call.
  - Changing the `/health` contract or the degraded-reason taxonomy (`scripts/eventbus/health_route.py`).
  - Any change outside the frozen `Implementation Target Files` (see below).
- **Dependencies**:
  - H-02 (eventbus002, `config`/`auth` token roles) is CLOSED: its plan is frozen in `plans/`. The preflight reuses `load_config()` and `_populate_token_maps()`, both already correct. No action required.
  - M-02 (eventbus007, readiness definition) is OPEN and non-blocking: the readiness gate signal is provisionally defined here and will be finalized against M-02's liveness/readiness/integrity split once filed. See `Scope`/`Unknowns`.

## Background
Confirmed against HEAD by adversarial re-verification (Steps 2/3):
- Schema validation exists in two separate code paths. Runtime: `_init_schema()` in `scripts/eventbus/schema.py` returns as soon as `PRAGMA user_version` equals the expected value (the `found == expected` branch) without any shape check; `_matches_current_schema()` is columns-only and runs only for an unstamped database (version 0). Deployment: `deploy/init_db.sh` runs `scripts/db/create_schema.py`, whose `create_eventbus_schema()` compares only the version number and then runs `executescript(build_eventbus_schema_sql())` (all `CREATE ... IF NOT EXISTS`), which silently adds missing tables/indexes but never verifies shape; the script then only prints `sqlite3 ... .tables` for EventBus. The Workflow DB is the only one with a table-presence check in `init_db.sh`.
- `deploy/setup_services.sh` starts EventBus in the background (`python -m eventbus.app &`), records the PID, prints the output of one `sleep 2 && curl /health` (or `まだ起動中`) and then prints `Event Bus (:8015, PID ...): started` unconditionally. It never checks that the process is alive, that health returned 200, or that the child exited.
- `/health` returns HTTP 503 whenever any degraded reason exists, including `lock_wait_high`, `query_duration_high`, `broker_queue_backlog_high` and `slow_consumers_detected` (`scripts/eventbus/health_route.py`). A gate that requires `status == ok` would therefore also fail a healthy start on a transient capacity signal.
- The import-linter contract `eventbus-is-isolated` forbids `eventbus` from importing `db` (it may import `shared`); `shared-is-leaf` forbids `shared` from importing `db`. One shared validator therefore cannot live in `scripts/db/` or be called from `scripts/eventbus/schema.py` both ways; the shared piece belongs in `shared/` and reads `schema.sql` as text (like `db.schema_sql` does), never importing `db`.
- `scripts/eventbus/schema.sql` defines tables and indexes only (no triggers).
- `deploy/load_env.sh::require_env_vars` checks presence only; there is no token-map↔`agent.toml` cross-check. `auth._populate_token_maps()` exists (`scripts/eventbus/auth.py`) and is called from `scripts/eventbus/app.py` lifespan at startup, so the preflight can reuse it.
- Doc overstate: `docs/90_deployment/deployment_01_deployment.md:296-305` claims `init_db.sh` verifies all mandatory EventBus tables and aborts if any are missing, and that the EventBus service refuses a different table shape. Reality is a workflow-only table check plus a columns-only service check for unstamped databases. The doc must be corrected together with the implementation.
- Concrete test breakage: `tests/db/test_create_schema.py` patches `build_eventbus_schema_sql` to `_EVENTBUS_SCHEMA_NO_VEC0`, which adds an extra `events.consumer_delivery_failure_count` column not present in `schema.sql`; strict validation would reject these patched shapes, so this test file must be updated. `test_unstamped_old_shape_fails_explicitly` expects `sqlite3.OperationalError`, but strict shape validation raises `RuntimeError`.

## Problem
A correct version stamp does not prove that tables, columns, indexes, constraints or triggers exist, so a malformed database can start and fail only when a route touches a missing object. Deployment can report success without proving that configuration, token maps, all database schemas, the EventBus process and the health endpoint are ready; HTTP 503, an immediate process exit or an incomplete database must not be summarized as success. Initialization validates some databases more strictly than others.

## Reason for Change
Runtime startup and deployment initialization must share one definition of a valid schema, and every boundary must fail closed with an actionable diagnostic.

## Implementation Intent
Build one reusable preflight and readiness chain: load and validate production configuration, build token maps, validate all required database schemas against a canonical fingerprint derived from `schema.sql`, start the process, then verify liveness and readiness with bounded polling. Report only verified states. The shared validator lives in `shared/` and is used by both the runtime startup path and the deployment path so their results are equivalent.

## Requirements
- `REQ-001`: A canonical EventBus schema fingerprint validator under `scripts/shared/` derives tables, columns (name/type/nullability/default/pk), indexes, table-level constraints, foreign keys, and triggers (if any) from `scripts/eventbus/schema.sql` via `PRAGMA` on a fresh in-memory apply and compares them against a target connection, raising on any mismatch — even when `user_version` matches.
- `REQ-002`: `scripts/eventbus/schema.py::_init_schema()` validates shape against the shared fingerprint when `user_version` matches, not only for an unstamped database.
- `REQ-003`: `deploy/init_db.sh` validates every required database (rag, session, workflow, EventBus) shape via the shared validator and aborts on mismatch; EventBus verification replaces the bare `.tables` print.
- `REQ-004`: `deploy/setup_services.sh` proves EventBus process liveness and readiness with bounded polling; process exit, connection failure, non-200, or `status != ok` is fatal with child cleanup and last-response logging, excluding transient capacity-degradation signals.
- `REQ-005`: `deploy/load_env.sh` preflight builds token maps via the existing `auth._populate_token_maps()` and cross-checks against config before startup; `require_env_vars` remains the presence gate.
- `REQ-006`: The non-canonical patched EventBus shapes in `tests/db/test_create_schema.py` are made canonical (or moved to explicit rejection tests) so strict validation passes, and the old-shape case expects the strict exception.
- `REQ-007`: `docs/90_deployment/deployment_01_deployment.md` no longer claims `init_db.sh` verifies all mandatory EventBus tables or the service refuses a shape mismatch; it documents the shared-validator and readiness-gate behavior.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified` per `issue-to-plan` Step 8; see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/eventbus_schema_fingerprint.py` | Create | New shared validator: canonical fingerprint (tables/columns/types/nullability/defaults/pk, indexes, table-level UNIQUE/PK/CHECK, FKs via `PRAGMA foreign_key_list`, triggers-if-any) computed via `PRAGMA` on a fresh in-memory apply of `schema.sql` vs a target connection; raises on any mismatch. Location forced by `.importlinter`: `shared` is the only root_package both `eventbus` and `db` may import; `shared-is-leaf` forbids `shared` importing `db`, so it reads `schema.sql` as text like `db.schema_sql`. Uses stdlib `sqlite3` only, so `shared-is-leaf` and `eventbus-is-isolated` stay KEPT. | REQ-001 | New module per D1; location driven by `.importlinter` layering (checked in Step 3) | `tests/db/test_create_schema.py` (new fingerprint equivalence tests) | Verified |
| `scripts/eventbus/schema.py` | Modify | `_init_schema()` validates shape against the shared fingerprint when `user_version` matches (currently returns early at the version-equal branch without a shape check; `_matches_current_schema` runs only for v0). | REQ-002 | `_init_schema` returns at `found == expected` (schema.py) without a shape check; `_matches_current_schema` is columns-only and runs only for unstamped v0 (checked in Step 2) | `tests/eventbus/test_eventbus_startup.py`, `test_eventbus_db_migration.py` | Verified |
| `scripts/db/create_schema.py` | Modify | `create_eventbus_schema()` validates shape against the shared fingerprint after DDL and fails closed on a malformed database already stamped with the current version (currently version-only + silent `IF NOT EXISTS` repair that resets v0 legacy DBs to v0). | REQ-003 | `create_eventbus_schema` compares only `user_version` then `executescript` `IF NOT EXISTS`, resetting v0 legacy DBs to v0 (checked in Step 2) | `tests/db/test_create_schema.py` | Verified |
| `deploy/init_db.sh` | Modify | Validate every required database (rag/session/workflow/eventbus) shape via the shared validator and abort on mismatch; replace the bare `.tables` print for EventBus with a shape check. | REQ-003 | `init_db.sh` prints only `.tables` for EventBus (line 60-61); Workflow has the only table-presence check (lines 42-58) (checked in Step 2) | `tests/deploy/test_init_db_eventbus_schema.py` | Verified |
| `deploy/setup_services.sh` | Modify | Bounded process + health polling for EventBus: process exit, connection failure, non-200, or `status != ok` is fatal with child cleanup and last-response logging; exclude transient capacity-degradation signals (`lock_wait_high`, `slow_consumers_detected`, `query_duration_high`, `broker_queue_backlog_high`, `subscribers_at_capacity`). | REQ-004 | `setup_services.sh` starts EventBus `&`, prints one `sleep 2 && curl /health` unconditionally, never checks liveness/200/process-exit (lines 180-191) (checked in Step 2) | `tests/deploy/test_setup_services_eventbus.py` | Verified |
| `deploy/load_env.sh` | Modify | Add a token-map preflight that builds token maps via the existing `auth._populate_token_maps()` and cross-checks against config before startup; keep `require_env_vars` as the presence gate. | REQ-005 | `require_env_vars` checks presence only (load_env.sh:79-105); `auth._populate_token_maps` exists (auth.py:97) called from app.py lifespan (checked in Step 2) | `tests/deploy/test_load_env_gate.py` (extended) | Verified |
| `tests/db/test_create_schema.py` | Modify | Make the patched `_EVENTBUS_SCHEMA_NO_VEC0` canonical (drop the extra `events.consumer_delivery_failure_count` column absent from `schema.sql`) so strict validation passes; move `test_unstamped_old_shape_fails_explicitly`'s expectation from `sqlite3.OperationalError` to `RuntimeError` under strict validation. | REQ-006 | `_EVENTBUS_SCHEMA_NO_VEC0` adds `events.consumer_delivery_failure_count` absent from `schema.sql`; strict validation rejects it; `test_unstamped_old_shape_fails_explicitly` expects `sqlite3.OperationalError` but strict validation raises `RuntimeError` (checked in Step 2) | `scripts/db/create_schema.py` | Verified |
| `tests/eventbus/test_eventbus_startup.py` | Add/modify | Startup shape-validation and readiness-gate tests: malformed stamped DB rejected at startup; healthy start passes the provisional readiness signal. | REQ-002, REQ-004 | Startup path exercises `_init_schema` (checked in Step 2) | `scripts/eventbus/schema.py` | Verified |
| `tests/deploy/test_init_db_eventbus_schema.py` | Create | Shell/integration: `init_db.sh` aborts on a malformed eventbus DB and passes on a canonical one. | REQ-003 | No existing shell-test infra for deploy scripts; only `tests/deploy/test_load_env_gate.py` covers `require_env_vars` (checked in Step 2) | `deploy/init_db.sh` | Verified |
| `tests/deploy/test_setup_services_eventbus.py` | Create | Process-exit, connection-failure, non-200, `status != ok`, and healthy-start cases for the EventBus gate. | REQ-004 | No existing shell-test infra for deploy scripts (checked in Step 2) | `deploy/setup_services.sh` | Verified |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | Correct the overstatement that `init_db.sh` verifies all mandatory EventBus tables and the service refuses a different table shape; document the shared-validator + readiness-gate behavior. | REQ-007 | `deployment_01_deployment.md:296-305` claims `init_db.sh` verifies all mandatory EventBus tables + service refuses shape mismatch; reality is workflow-only table check + service columns-only (checked in Step 2) | (none; doc-only) | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/schema_sql.py` | `build_eventbus_schema_sql()` is the DDL source read by `create_schema` and by the shared validator; confirm the validator reading `schema.sql` directly stays equivalent. | `scripts/shared/eventbus_schema_fingerprint.py`, REQ-001 |
| `scripts/eventbus/config.py` | `load_config()` is the authoritative config path the preflight reuses; confirm no change is needed. | `deploy/load_env.sh`, REQ-005 |
| `scripts/eventbus/auth.py` | `_populate_token_maps()` is the token-map builder the preflight reuses; no change (owner decision). | `deploy/load_env.sh`, REQ-005 |
| `scripts/eventbus/app.py` | Production call sites: `load_config()` and `_populate_token_maps()` at lifespan (line 74); the preflight reuses them. | `deploy/load_env.sh`, REQ-005 |
| `scripts/eventbus/health_route.py` | `/health` `status`/`degraded` + HTTP 503 semantics the gate consumes; `degraded_reasons` include transient capacity signals. | `deploy/setup_services.sh`, REQ-004 |
| `config/eventbus.toml` | Config read by `load_config()`; the commented authorization example added by eventbus002. | `deploy/load_env.sh`, REQ-005 |
| `tests/eventbus/conftest.py` | Shared fixtures; `conftest.py:93` provisions via real `create_eventbus_schema()` → canonical DB passes unchanged. | `tests/eventbus/test_eventbus_startup.py` |
| `tests/deploy/test_load_env_gate.py` | Existing deploy shell-test entry point to extend. | `deploy/load_env.sh`, REQ-005 |

## Acceptance Criteria
- A correctly stamped but malformed EventBus database is rejected at runtime startup and by `init_db.sh` with equivalent results. (REQ-002, REQ-003)
- The shared validator produces an identical fingerprint for a canonical database and rejects a database missing a column, index, or with a changed column type/nullability/default/pk. (REQ-001)
- HTTP 503 is never treated as deployment success; an immediate EventBus process crash, connection failure, non-200, or `status != ok` is detected and aborts `setup_services.sh` with child cleanup and last-response logging. (REQ-004)
- An incomplete database blocks service startup; a successful deployment is followed by a usable EventBus API. (REQ-004)
- The readiness gate does not fail a healthy start on transient capacity degradation (`lock_wait_high`, `slow_consumers_detected`). (REQ-004)
- Configuration loads through `load_config()` and token maps build via `_populate_token_maps()` during preflight; a broken config or token map aborts before startup. (REQ-005)
- The non-canonical patched shapes in `test_create_schema.py` no longer pass strict validation, and the old-shape case expects the strict exception. (REQ-006)
- The deployment doc no longer claims `init_db.sh` verifies all mandatory EventBus tables or the service refuses a shape mismatch. (REQ-007)

## Tests
- Fingerprint equivalence: the shared validator reports identical fingerprints for a fresh in-memory apply of `schema.sql` and a canonical database, and raises on a missing column, missing index, changed type/nullability/default/pk, and a missing table-level constraint/FK. (REQ-001)
- Runtime startup: a malformed stamped database is rejected at `_init_schema()` even when `user_version` matches; a canonical database passes. (REQ-002)
- Deployment strict validation: `create_eventbus_schema()` fails closed on a malformed database already stamped with the current version while keeping the v0 legacy repair path; `init_db.sh` aborts on a malformed EventBus DB and passes on a canonical one. (REQ-003)
- Readiness gate: process exit, connection failure, non-200, and `status != ok` each abort `setup_services.sh` with cleanup; a healthy start passes the provisional readiness signal without failing on transient capacity signals. (REQ-004)
- Config/token preflight: a valid config builds token maps and passes; a broken config or duplicate/missing token map aborts before startup; `require_env_vars` still enforces presence. (REQ-005)
- Test fixes: the patched `_EVENTBUS_SCHEMA_NO_VEC0` shapes are canonical and pass strict validation; `test_unstamped_old_shape_fails_explicitly` expects the strict exception. (REQ-006)
- Then ruff, mypy, bandit, `lint-imports`, the `tests/db` and `tests/eventbus` suites, the deploy test file, and diff-cover. (all REQs)

## Documentation Impact
Yes. `docs/90_deployment/deployment_01_deployment.md` §3.1 (Applying Schema) overstates that `init_db.sh` verifies all mandatory EventBus tables and that the service refuses a different table shape; it must document the shared-validator shape policy, the fail-closed behavior, and the bounded process+health readiness sequence. Driven by REQ-007. Target resolved via `docs/00_index.md` "Document References by Task" → the `deployment` area.

## Assumptions
- The fingerprint composition (tables/columns/types/nullability/defaults/pk, indexes, table-level UNIQUE/PK/CHECK, FKs, triggers-if-any) is sufficient to catch the malformed-DB breakage described; this resolves UNK-02.
- Triggers are included only if `schema.sql` gains any; currently `schema.sql` defines tables and indexes only (no triggers), so the trigger check is a no-op today.
- The readiness gate uses `db == ok` AND `dlq_task == running` as the provisional signal, tolerating capacity-only `degraded_reasons`; this resolves UNK-01 pending M-02.
- `create_eventbus_schema()` keeps its v0 legacy repair path but fails closed on a malformed database already stamped with the current version; this resolves the idempotent-repair-vs-fail-closed decision (D4).
- The shared validator uses stdlib `sqlite3` only, so `shared-is-leaf` and `eventbus-is-isolated` stay KEPT; `.importlinter` needs no change.
- `setup_services.sh` stays non-interactive; the bounded poll uses env-overridable retries/interval mirroring the existing `LLM_HEALTH_RETRIES`/`LLM_HEALTH_INTERVAL` pattern.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which `/health` condition is the deployment readiness gate (database reachable + DLQ task running versus full `status == ok`)? | Readiness definition is owned by M-02 (eventbus007), still open. | Provisional signal = `db == ok` AND `dlq_task == running`, tolerating capacity-only `degraded_reasons`; finalize against M-02's liveness/readiness/integrity split. | False |
| UNK-02 | Exact construct set in the schema fingerprint (columns, types, nullability, defaults, pk, indexes, unique, fk, triggers). | Owner decision; the issue leaves it open. | Resolved by REQ-001 (tables/columns/types/nullability/defaults/pk, indexes, table-level constraints, FKs, triggers-if-any). Documented in Assumptions. | False |
| UNK-03 | Should `create_eventbus_schema()` keep silent idempotent repair for a malformed database already stamped with the current version, or fail closed? | Owner decision; the issue flags the conflict with the fail-closed goal. | Provisional: fail closed on a malformed database stamped with the current version; keep the v0 legacy repair path. Documented in Assumptions. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/eventbus_schema_fingerprint.py` | Create | Medium — new shared module imported by both `eventbus` and `db`; a wrong boundary would fail `lint-imports`. | 0 (new) | Multiple contributors across `shared/`; git-fame not run | not applicable (rsynced) |
| `scripts/eventbus/schema.py` | Modify | High — `_init_schema()` runs on every DB open; ~16 test files open DBs, but the validator only rejects MALFORMED schemas so canonical test DBs pass unchanged. | 9 commits | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `scripts/db/create_schema.py` | Modify | Medium — `create_eventbus_schema()` is called by `create_schema()` and `init_db.sh`; only malformed stamped DBs now raise. | N/A (< lowest shown) | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `deploy/init_db.sh` | Modify | Low — deployment entry point; adds a shape check, aborts only on mismatch. | N/A (< lowest shown) | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `deploy/setup_services.sh` | Modify | Medium — deployment entry point; changes the EventBus readiness path from unconditional to gated. | 8 commits | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `deploy/load_env.sh` | Modify | Low — sourced library; adds a preflight function, keeps `require_env_vars`. | N/A (< lowest shown) | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | Modify | Low — test-only; high churn means re-run to confirm no regression. | N/A (< lowest shown) | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_startup.py` | Add/modify | Low — test-only. | N/A (< lowest shown) | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `tests/deploy/test_init_db_eventbus_schema.py` | Create | Low — new test-only. | 0 (new) | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `tests/deploy/test_setup_services_eventbus.py` | Create | Low — new test-only. | 0 (new) | Multiple contributors over time; not flagged | not applicable (rsynced) |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | Low — documentation only. | N/A (< lowest shown) | Multiple contributors over time; not flagged | not applicable (rsynced) |

## Design
Path B (affects more than 3 files, creates a new shared module, and changes runtime startup validation and the deployment readiness interface). Full four-dimension analysis performed:

- **Architecture**: `scripts/eventbus/schema.py` imports only stdlib (`re`, `sqlite3`, `pathlib`); `scripts/db/create_schema.py` imports `db.*` and `db.helper`. The new `scripts/shared/eventbus_schema_fingerprint.py` will import stdlib `sqlite3` and read `schema.sql` as text — no `db`/`eventbus` import — so `shared-is-leaf` and `eventbus-is-isolated` stay KEPT. `lint-imports` reported 6/6 KEPT at baseline (checked in Step 3).
- **Dependency graphing**: `_init_schema()` runs on every DB open (via `open_db`); `create_eventbus_schema()` is called from `create_schema()` and `init_db.sh`. The shared validator is called from `_init_schema()` and from `init_db.sh`/`create_eventbus_schema()`. No external service reaches these symbols.
- **Historical** (30-day churn above): `schema.py` 9, `setup_services.sh` 8, `schema.sql` 7; other targets below the top-20 threshold. Moderate ownership; `test_create_schema.py` is test-only.
- **Operational**: no process holds DB locks or a listener during this change; `_init_schema()`/`create_eventbus_schema()` run at startup only. `ss`/`fuser` not needed (no port or DB file touched by the validation logic at plan time).

Key decisions:
- **Shared validator location.** Place the validator in `scripts/shared/eventbus_schema_fingerprint.py`. `shared` is the only root_package both `eventbus` and `db` may import per `.importlinter`; `shared-is-leaf` forbids `shared` importing `db`, so the validator reads `schema.sql` as text (like `db.schema_sql.EVENTBUS_SCHEMA_SQL_PATH`) and never imports `db.schema_sql`. Uses stdlib `sqlite3` only. This resolves UNK-01's location question without changing `.importlinter`.
- **Fingerprint composition.** Tables (columns as name/type/nullability/default/pk-flag), indexes (name/unique/expression), table-level constraints (UNIQUE/PK/CHECK), foreign keys (`PRAGMA foreign_key_list`), and triggers if any. Computed via `PRAGMA` on a fresh in-memory apply of `schema.sql` vs the target connection. This resolves UNK-02.
- **Runtime gate.** `_init_schema()` calls the shared fingerprint after the `found == expected` early return, so a correctly stamped but malformed database is refused. Unstamped v0 behavior is unchanged.
- **Deployment strictness.** `create_eventbus_schema()` validates shape after DDL and fails closed on a malformed database already stamped with the current version; the v0 legacy repair path is kept. `init_db.sh` runs the shared validator for each required DB. This resolves UNK-03.
- **Readiness signal.** Provisionally require `db == ok` AND `dlq_task == running`, excluding capacity-only `degraded_reasons`; finalize against M-02. This resolves UNK-01.
- **Config/token preflight.** Reuse `load_config()` and `_populate_token_maps()` (both correct after eventbus002); add a shell wrapper in `load_env.sh` that builds token maps and cross-checks against config. `require_env_vars` stays the presence gate.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Shared fingerprint validator** (`scripts/shared/eventbus_schema_fingerprint.py`)
   - [ ] Derive the canonical fingerprint (tables/columns/types/nullability/defaults/pk, indexes, table-level constraints, FKs, triggers-if-any) from `schema.sql` via `PRAGMA` on a fresh in-memory apply (REQ-001).
   - [ ] Compare against a target connection and raise on any mismatch; add equivalence + rejection unit tests (REQ-001).
2. **Phase 2: Runtime startup shape validation** (`scripts/eventbus/schema.py`)
   - [ ] Call the shared fingerprint in `_init_schema()` when `user_version` matches, before returning (REQ-002).
   - [ ] Add startup rejection + canonical-pass tests (REQ-002).
3. **Phase 3: Deployment strict validation** (`scripts/db/create_schema.py`, `deploy/init_db.sh`)
   - [ ] `create_eventbus_schema()` validates shape after DDL and fails closed on a malformed stamped database, keeping the v0 repair path (REQ-003).
   - [ ] `init_db.sh` validates every required database shape via the shared validator and aborts on mismatch; replace the bare `.tables` print for EventBus (REQ-003).
   - [ ] Add `tests/deploy/test_init_db_eventbus_schema.py` (REQ-003).
4. **Phase 4: Test fixes** (`tests/db/test_create_schema.py`)
   - [ ] Make the patched `_EVENTBUS_SCHEMA_NO_VEC0` shapes canonical and fix `test_unstamped_old_shape_fails_explicitly` to expect the strict exception (REQ-006).
5. **Phase 5: Readiness gate** (`deploy/setup_services.sh`)
   - [ ] Add bounded process + health polling: process exit, connection failure, non-200, `status != ok` fatal with child cleanup and last-response logging; exclude transient capacity signals; env-overridable retries/interval (REQ-004).
   - [ ] Add `tests/deploy/test_setup_services_eventbus.py` (REQ-004).
6. **Phase 6: Config/token preflight** (`deploy/load_env.sh`)
   - [ ] Add a token-map preflight that builds maps via `_populate_token_maps()` and cross-checks against config; keep `require_env_vars` as the presence gate (REQ-005).
   - [ ] Extend `tests/deploy/test_load_env_gate.py` (REQ-005).
7. **Phase 7: Startup/readiness integration tests** (`tests/eventbus/test_eventbus_startup.py`)
   - [ ] Malformed-stamped rejection at startup and healthy-start provisional-readiness-pass cases (REQ-002, REQ-004).
8. **Phase 8: Documentation** (`docs/90_deployment/deployment_01_deployment.md`)
   - [ ] Correct the overstatement and document the shared-validator + readiness-gate behavior (REQ-007).
9. **Phase 9: Deployment & Verification**
   - [ ] Run ruff, mypy, bandit, `lint-imports`, the `tests/db` and `tests/eventbus` suites, the deploy test file, and diff-cover; confirm the architecture contracts stay KEPT (all REQs). Deployment is a hand-off to `skills/deploy/SKILL.md`: commit and push first; deploying is the user's decision.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/eventbus_schema_fingerprint.py` | Unit: fingerprint equivalence + rejection of missing column/index/constraint/FK | `uv run pytest tests/db/test_create_schema.py` | identical fingerprint for canonical DB; raises on malformed |
| `scripts/eventbus/schema.py` | Unit: malformed stamped DB rejected at `_init_schema()` when version matches; canonical passes | `uv run pytest tests/eventbus/test_eventbus_startup.py` | malformed refused; canonical passes |
| `scripts/db/create_schema.py` | Unit: fail-closed on malformed stamped DB; v0 repair kept | `uv run pytest tests/db/test_create_schema.py` | malformed raises; v0 legacy repaired |
| `deploy/init_db.sh` | Integration: abort on malformed EventBus DB, pass on canonical | `uv run pytest tests/deploy/test_init_db_eventbus_schema.py` | abort on malformed; pass on canonical |
| `deploy/setup_services.sh` | Integration: process-exit/connection-failure/non-200/status!=ok fatal; healthy start passes; no capacity-signal false positive | `uv run pytest tests/deploy/test_setup_services_eventbus.py` | each fatal case aborts; healthy start passes |
| `deploy/load_env.sh` | Integration: valid config builds token maps and passes; broken config aborts; presence gate intact | `uv run pytest tests/deploy/test_load_env_gate.py` | valid passes; broken aborts |
| `scripts/shared/eventbus_schema_fingerprint.py`, `scripts/eventbus/*`, `scripts/db/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | clean; all 6 contracts KEPT |

## Risks
- **Risk**: Changing `_init_schema()`/`create_eventbus_schema()` strictness could affect ~16 test files that open DBs. → **Mitigation**: the validator only rejects MALFORMED schemas; canonical test DBs provisioned via `conftest.py:93` (real `create_eventbus_schema()`) pass unchanged; targeted run of `tests/db` and `tests/eventbus` post-implementation.
- **Risk**: The shared validator reading `schema.sql` as text could drift from `build_eventbus_schema_sql()`. → **Mitigation**: both read the same `scripts/eventbus/schema.sql`; an equivalence test asserts identical fingerprints between the validator and the DDL source.
- **Risk**: `setup_services.sh` is sourced by `deploy.sh`; a wrong fatal path could break production deploy. → **Mitigation**: bounded, env-overridable polling; new deploy tests cover each fatal case; `shellcheck`.
- **Risk**: Non-canonical patched shapes in `test_create_schema.py` start failing once strict. → **Mitigation**: update those tests to canonical shape or move to explicit rejection tests (REQ-006).
- **Risk**: The open M-02 dependency could change the readiness signal after implementation begins. → **Mitigation**: the provisional signal is isolated behind one gate predicate, trivial to swap once M-02 lands.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Shared fingerprint validator (`scripts/shared/eventbus_schema_fingerprint.py`) | In Progress | — | — | Path B |
| 2 | Runtime startup shape validation (`scripts/eventbus/schema.py`) | In Progress | — | — | Path B |
| 3 | Deployment strict validation (`scripts/db/create_schema.py`, `deploy/init_db.sh`) | In Progress | — | — | Path B |
| 4 | Test fixes (`tests/db/test_create_schema.py`) | In Progress | — | — | Path B |
| 5 | Readiness gate (`deploy/setup_services.sh`) | In Progress | — | — | Path B |
| 6 | Config/token preflight (`deploy/load_env.sh`) | In Progress | — | — | Path B |
| 7 | Startup/readiness integration tests (`tests/eventbus/test_eventbus_startup.py`) | In Progress | — | — | Path B |
| 8 | Documentation (`docs/90_deployment/deployment_01_deployment.md`) | In Progress | — | — | Path B |
| 9 | Deployment & verification (ruff/mypy/bandit/lint-imports/pytest/diff-cover) | Pending | — | — | Path B |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261025-155039_01_scripts_shared_eventbus_schema_fingerprint.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261025-155039_02_scripts_eventbus_schema.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261025-155039_03_scripts_db_create_schema.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261025-155039_04_deploy_init_db.sh.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261025-155039_05_deploy_setup_services.sh.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261025-155039_06_deploy_load_env.sh.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261025-155039_07_tests_db_test_create_schema.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261025-155039_08_tests_eventbus_test_eventbus_startup.py.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261025-155039_09_tests_deploy_test_init_db_eventbus_schema.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261025-155039_10_tests_deploy_test_setup_services_eventbus.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261025-155039_11_docs_90_deployment_deployment_01_deployment.md` | 8 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-111552
- **Related target files**: `scripts/shared/eventbus_schema_fingerprint.py`, `scripts/eventbus/schema.py`, `scripts/db/create_schema.py`, `deploy/init_db.sh`, `deploy/setup_services.sh`, `deploy/load_env.sh`, `tests/db/test_create_schema.py`, `tests/eventbus/test_eventbus_startup.py`, `tests/deploy/test_init_db_eventbus_schema.py`, `tests/deploy/test_setup_services_eventbus.py`, `docs/90_deployment/deployment_01_deployment.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; Unresolved Questions (location + construct set); Constraints | `scripts/shared/eventbus_schema_fingerprint.py` | Step 1 | AC 2 | fingerprint equivalence + rejection | Confirmed by repository evidence |
| REQ-002 | Required Changes; Problem | `scripts/eventbus/schema.py` | Step 2 | AC 1, AC 8 | malformed stamped DB refused at startup | Confirmed by repository evidence |
| REQ-003 | Required Changes; Problem | `scripts/db/create_schema.py`, `deploy/init_db.sh` | Step 3 | AC 1, AC 4 | init_db.sh aborts on malformed; equivalent to runtime | Confirmed by repository evidence |
| REQ-004 | Required Changes; Problem; Constraints | `deploy/setup_services.sh` | Step 5 | AC 3, AC 4, AC 5 | process/health gating with capacity exclusion | Confirmed by repository evidence |
| REQ-005 | Required Changes; Unresolved Questions (token preflight) | `deploy/load_env.sh` | Step 6 | AC 6 | config/token preflight aborts on breakage | Derived from confirmed evidence |
| REQ-006 | Required Changes; Background (test breakage) | `tests/db/test_create_schema.py` | Step 4 | AC 7 | canonical patched shapes pass strict | Confirmed by repository evidence |
| REQ-007 | Documentation Impact; Background | `docs/90_deployment/deployment_01_deployment.md` | Step 8 | AC 8 | doc corrected | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261025-155039 -->