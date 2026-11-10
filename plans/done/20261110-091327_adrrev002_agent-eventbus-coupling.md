## Goal
- Make "the Agent does not touch eventbus.sqlite or publish through `EventBusClient`" true in code, configuration, deploy scripts, and documentation: delete the unused `EventBusClient`, remove every Agent-side (`scripts/db/`, `config/agent.toml`) creation, configuration, rotation, and drill handling of eventbus.sqlite, and give the EventBus service side (`scripts/eventbus/`, `config/eventbus.toml`) the only creator and path owner, with `deploy/init_db.sh` calling that EventBus-side entry.

## Priority
High

## Scope
- **In-Scope**: Delete `scripts/agent/eventbus_client.py` and `tests/agent/test_eventbus_client.py`; add an EventBus-side database tool (`scripts/eventbus/db_tools.py`) for create/validate, rotate, and verify, resolving the path from `config/eventbus.toml` only; switch `deploy/init_db.sh` and `tools/check_db_separation.py` to it; remove `DbTarget.EVENTBUS`, `create_eventbus_schema`, `build_eventbus_schema_sql`, `rotate_eventbus_db`, the eventbus domain of `recovery_drill`, and `eventbus_db_path` from `scripts/db/`, `scripts/shared/`, `scripts/agent/production_config_validator.py`, and `config/agent.toml`; update the tests that use them; update ADR-013 (Review Triggers), ADR-008 (Decision Detail, Recovery Policy Matrix backup retention, Target APIs, Implementation References), the DB, deployment, agent, and EventBus reference documents, the dependency graphs, and the generated references.
- **Out-of-Scope**: `scripts/agent/eventbus_subscriber.py` and `scripts/agent/eventbus_topic_admin_client.py` (same dead-code status, not named by the Issue; see UNK-02); the EventBus schema, authorization, and roles; fingerprint-based schema validation work (`issues/20261109-112715_adrrev005_schema-fingerprint-unify.md`); the future EventBus integration and its fail-closed client design; the decision to keep or retire the EventBus (`issues/20261109-112739_adrrev006_eventbus-future-decision.md`).
- **Dependencies**: Depends on none. Blocks `issues/20261109-112922_adrrev009_adr008-recovery-align.md` and `issues/20261109-112952_adrrev010_eventbus-authz-harden.md`. Sequencing: `plans/20261110-090758_adrrev001_eventbus-route-handlers.md` edits ADR-013 `Current State`; this Plan edits ADR-013 `Review Triggers` only, so the two are compatible in either order.
  - **Depends on**: N/A: none

## Background
- Source: `memo-issue.md` items H-02 and H-04, re-verified on 2026-11-10 (see Requirement Traceability `Status`).
- `Confirmed by repository evidence`: `scripts/agent/eventbus_client.py` defines `EventBusClientConfig` (`publisher_token: str = ""`, line 43) and `EventBusClient` (Bearer header from that token, line 74). No file under `scripts/` imports it; only `tests/agent/test_eventbus_client.py` does. It stamps `published_at` with an isoformat `+00:00` value; the EventBus writes `Z` (`scripts/eventbus/json_utils.py:21` `now_iso`, `scripts/eventbus/dlq.py:377`). The `eventbus_client` hits under `tests/eventbus/` and `tests/deploy/` are `make_eventbus_client` (a test helper), not the Agent client.
- `Refuted`/`narrowed` (Issue claim: eventbus.sqlite creation is reachable only through the Agent and may be deleted): `deploy/init_db.sh` runs `scripts/db/create_schema.py`, whose `create_schema()` calls `create_eventbus_schema()`; the same script then fails with `[FATAL] EventBus database is missing` if `eventbus.sqlite` does not exist and runs the `shared.eventbus_schema_fingerprint` shape gate. The EventBus service also creates the schema itself on open (`scripts/eventbus/db_conn.py:open_db` → `scripts/eventbus/schema.py:_init_schema`, the same create-or-validate semantics). Deleting the Agent-side branch alone would break a fresh deploy at that gate. This is the production path the Issue marked `Needs confirmation`; the answer is "yes, reached".
- `Confirmed by repository evidence`: `eventbus_db_path` is read in `scripts/db/config.py` (field with default, empty-value check, `build_db_config`), `scripts/db/helper.py:121`, `scripts/db/rotation.py:101`, `scripts/db/recovery_drill.py:157`, `scripts/shared/execution_snapshot.py:54`, `scripts/agent/production_config_validator.py:198` (the allowed-key list), and `config/agent.toml:20`; `config/eventbus.toml:4` holds the EventBus's own `db_path`. Both point to `/opt/llm/db/eventbus.sqlite`, and nothing checks that they are equal.
- `Confirmed by repository evidence` (wider than the Issue's target list): `build_eventbus_schema_sql` is also used by `tools/check_db_separation.py:124` and by tests in `tests/deploy/`, `tests/eventbus/test_eventbus_startup.py`, and `tests/db/`; `tests/conftest.py:101` calls `create_schema.create_eventbus_schema()` and `:144` lists `eventbus_db_path`; DbConfig is built with `eventbus_db_path=` in `tests/agent/test_repl.py`, `tests/integration/test_session_recovery.py`, `tests/db/test_sqlite_helper.py`, and `tests/db/test_recovery_drill.py`.
- `Confirmed by repository evidence`: `.importlinter` contracts forbid `eventbus` importing `db` and forbid `db` and `shared` importing `eventbus`; `shared` is a leaf. The EventBus-side tool therefore cannot reuse `scripts/db/rotation.py` or `scripts/db/recovery.py` (both import `db.helper` and `db.config`); it uses the standard library and `shared.eventbus_schema_fingerprint`.
- `Confirmed by repository evidence`: besides `EventBusClient`, `scripts/agent/eventbus_subscriber.py` and `scripts/agent/eventbus_topic_admin_client.py` exist, are imported only by their own tests, and are described together with the client in `docs/23_agent/agent_02_runtime-architecture.md` and `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`. The Issue names only the publish client.
- `Needs confirmation`: which component rotates and backs up eventbus.sqlite in production. No caller of `rotate_all_dbs` or `rotate_eventbus_db` exists in `deploy/`, `scripts/`, `tools/`, `config/`, or `.github/`; `deploy/init_db.sh` only prints a hint naming `rotate_all_dbs`, so the operation is operator-invoked (UNK-01).

## Problem
- Dead production code with a fail-open default (`publisher_token = ""` yields `Authorization: Bearer `) is maintained and documented, contradicting the ADR-004 principle that an empty token is rejected.
- Two components can create or operate on eventbus.sqlite (the Agent-side DB tooling run by `deploy/init_db.sh`, and the EventBus service), and the two configured paths are independent keys in two files with no equality check (ADR-002 requires each process to read only its own configuration).
- ADR-013 `Review Triggers` (line 272) assumes "the single trusted Agent process" as the only caller, which contradicts the system overview, which says the Agent neither publishes nor subscribes. The Issue's claim that ADR-013 `Context` states this is refuted: the ADR contains no other reference to the Agent.

## Reason for Change
- Dead code matches the governance definition of an Unused Feature. A path mismatch silently creates two databases and lets rotation or backup act on the wrong file. No external deadline; the change unblocks the ADR-008 alignment and EventBus authorization hardening Issues.

## Implementation Intent
- Owner decision (maintainer, 2026-11-10): move eventbus.sqlite creation, rotation, and verification to EventBus-side tooling; the path comes from `config/eventbus.toml` `db_path` only.
- Sequence for a safe cut-over: add the EventBus-side tool and tests first (additive), switch the deploy script and the ADR-008 checker to it, then remove the Agent-side support and the config key, then delete the client, then update documents.
- Preserve rotation and recovery capability for eventbus.sqlite; do not redesign the EventBus or its schema; keep the EventBus's own `_init_schema` semantics (create when absent, accept only the current schema).

## Requirements
- `REQ-001`: Delete `scripts/agent/eventbus_client.py` and `tests/agent/test_eventbus_client.py`, regenerate the references that list them, and leave no `EventBusClient`/`EventBusClientConfig`/`EventBusPublish*` symbol in `scripts/`, `tests/`, `config/`, `docs/`.
- `REQ-002`: Provide `scripts/eventbus/db_tools.py` with create-or-validate, rotate (consistent copy with integrity and fingerprint verification), and verify entry points; the database path is read only from the `db_path` key of the file `eventbus.config.get_config_path()` returns, parsed with the standard library inside the tool (not through `eventbus.config.load_config`, which resolves token references and rejects an empty `auth_token`, and `deploy/init_db.sh` sets no EventBus token variables); it imports only `eventbus` and `shared` modules and the standard library.
- `REQ-003`: `deploy/init_db.sh` creates, shape-gates, and (when `RUN_RECOVERY_DRILL=1`) verifies eventbus.sqlite through the EventBus-side tool; a fresh deploy still ends with the file present and matching the canonical schema.
- `REQ-004`: Remove `DbTarget.EVENTBUS`, the EventBus branch of `create_schema()` (`create_eventbus_schema`), `build_eventbus_schema_sql`, `rotate_eventbus_db` (and the eventbus element of `rotate_all_dbs`), the eventbus domain of `recovery_drill`, and the eventbus target of `recover_corruption` from `scripts/db/`; no `scripts/db/` module reads an eventbus path.
- `REQ-005`: Remove `eventbus_db_path` from `config/agent.toml`, `DbConfig`, `build_db_config`, `execution_snapshot` db-path mapping, and the allowed-key list of `production_config_validator.py`; an `agent.toml` containing the key fails validation (test added).
- `REQ-006`: `tools/check_db_separation.py` keeps enforcing ADR-008 for four databases, taking the eventbus DDL from `scripts/eventbus/schema.sql` and the eventbus path from `config/eventbus.toml`; `uv run python tools/check_db_separation.py` passes.
- `REQ-007`: Update the tests and test infrastructure that used the removed symbols so they use the EventBus-side tool or `scripts/eventbus/schema.sql` directly (`tests/conftest.py`, `tests/db/`, `tests/deploy/`, `tests/eventbus/test_eventbus_startup.py`, `tests/shared/`, `tests/tools/`, `tests/test_production_isolation.py`, `tests/agent/test_repl.py`, `tests/integration/test_session_recovery.py`).
- `REQ-008`: Update ADR-013 (`Review Triggers`), ADR-008 (the `rotate_all_dbs()` backup statements, the Recovery Policy Matrix backup-retention row, `Target APIs or processing paths`, and the implementation references; the ADR has no `Affected Components` heading), `db_01`, `db_02`, `db_03`, `db_07`, `db_08`, `deployment_01`, `eventbus_06`, `agent_02`, `agent_10_01`, `governance_05`, and the generated `agent_13`; record any remaining unconfirmed caller through `governance_03`, not as inline prose.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-10 (fallout): added tests/eventbus/test_eventbus_schema_version.py — Import the schema version helper from the EventBus-side tool; found by the consumer re-scan in plan-to-implementation-procedure Step 3a
Amended 2026-11-10 (fallout): added registry/manifests/db_schema_versions.yaml — Regenerate the generated manifest after eventbus_db_path leaves DbConfig; found by the consumer re-scan in plan-to-implementation-procedure Step 3a
Amended 2026-11-10 (fallout): added docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md — Reword the archive sentence that names rotate_eventbus_db(); found by the consumer re-scan in plan-to-implementation-procedure Step 3a

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/eventbus_client.py` | Delete the unused client | Delete: no `scripts/` importer; fail-open `publisher_token = ""` default | REQ-001 / AC-01 | `scripts/agent/eventbus_client.py:43,74`; `rg` finds importers only in `tests/agent/test_eventbus_client.py` (checked in Step 2) | `tests/agent/test_eventbus_client.py` (deleted with it) | Verified |
| `tests/agent/test_eventbus_client.py` | Delete the client's tests | Delete: tests only the removed module | REQ-001 / AC-01 | File exists; sole importer of `agent.eventbus_client` (checked in Step 2) | `uv run pytest tests/agent -v` | Verified |
| `scripts/eventbus/db_tools.py` | EventBus-owned create/rotate/verify entry points | New file; path from `eventbus.config` only; stdlib and `shared` imports only | REQ-002 / AC-02 | `scripts/eventbus/schema.py:_init_schema`, `scripts/shared/eventbus_schema_fingerprint.py:201,210`, `.importlinter` contracts (checked in Step 3) | `tests/eventbus/test_eventbus_db_tools.py` | Verified |
| `tests/eventbus/test_eventbus_db_tools.py` | New file: tests for the EventBus-side tool | New file: fresh create, existing-current validation, refusal of a stale or unstamped database, rotate with verification, path taken from `eventbus.toml` | REQ-002 / AC-02 | Analogues: `tests/db/test_create_schema.py:827`, `tests/db/test_db_maintenance.py:1119` (checked in Step 3) | `uv run pytest tests/eventbus/test_eventbus_db_tools.py -v` | Verified |
| `deploy/init_db.sh` | Create and gate eventbus.sqlite through the EventBus tool | Replace the eventbus part of the `create_schema.py` call, the shape gate, and the drill hook with calls to the EventBus-side tool | REQ-003 / AC-03 | `deploy/init_db.sh:34` (create_schema.py), `:89-117` (existence check and `assert_matches` gate), `:137` (`recovery_drill.py --domain all`) (checked in Step 3) | `tests/deploy/test_init_db_eventbus_schema.py`, `tests/deploy/test_init_db_schema_gate.py` | Verified |
| `scripts/db/helper.py` | Remove the eventbus target | Remove `DbTarget.EVENTBUS`, the `"eventbus"` literal branch, and the `eventbus_db_path` lookup | REQ-004 / AC-04 | `scripts/db/helper.py:52,100-104,121` (checked in Step 3) | `tests/db/test_sqlite_helper.py` | Verified |
| `scripts/db/create_schema.py` | Remove EventBus schema creation | Delete `create_eventbus_schema()` and its call in `create_schema()`; drop the `build_eventbus_schema_sql` import | REQ-004 / AC-04 | `scripts/db/create_schema.py:29,84-131,134-140` (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `scripts/db/schema_sql.py` | Remove EventBus DDL accessors | Delete `build_eventbus_schema_sql`, `EVENTBUS_SCHEMA_SQL_PATH`, and the module-docstring entry; keep `eventbus_schema_version` only if the tool needs it elsewhere (otherwise delete) | REQ-004 / AC-04 | `scripts/db/schema_sql.py:14,245-264` (checked in Step 3) | `tests/db/test_create_schema.py`, `tests/eventbus/test_eventbus_startup.py` | Verified |
| `scripts/db/config.py` | Remove the eventbus path from `DbConfig` | Delete the field, its empty-value check, its entry in the validated path list, and the `build_db_config` read | REQ-004, REQ-005 / AC-04, AC-05 | `scripts/db/config.py:28,41-42,51,73` (checked in Step 3) | `tests/db/test_sqlite_helper.py`, `tests/test_production_isolation.py` | Verified |
| `scripts/db/rotation.py` | Remove eventbus rotation | Delete `rotate_eventbus_db`; `rotate_all_dbs` returns three paths; fix the docstring on `_verify_archive` | REQ-004 / AC-04 | `scripts/db/rotation.py:64-70,97-114` (checked in Step 3) | `tests/db/test_db_maintenance.py` | Verified |
| `scripts/db/recovery_drill.py` | Remove the eventbus domain | Remove `"eventbus"` from `DOMAINS`, `_verify_eventbus`, the live-path entry, and the `shared.eventbus_schema_fingerprint` import | REQ-004 / AC-04 | `scripts/db/recovery_drill.py:29,47,125-139,157,211` (checked in Step 3) | `tests/db/test_recovery_drill.py` | Verified |
| `scripts/db/recovery.py` | Remove the eventbus recovery target | Remove `"eventbus"` from the target documentation and the `("workflow", "eventbus")` no-recovery branch | REQ-004 / AC-04 | `scripts/db/recovery.py:489-521` (checked in Step 3) | `tests/db/test_db_recovery.py` | Verified |
| `scripts/db/__init__.py` | Stop exporting the removed function | Remove `rotate_eventbus_db` from the import and `__all__` | REQ-004 / AC-04 | `scripts/db/__init__.py:44,95` (checked in Step 3) | `tests/db/test_db_maintenance.py` | Verified |
| `scripts/shared/execution_snapshot.py` | Stop reading `eventbus_db_path` | Remove the `eventbus` entries of the db-path key and default maps; the snapshot then reports three databases | REQ-005 / AC-05 | `scripts/shared/execution_snapshot.py:48-62` (checked in Step 3) | `tests/shared/test_execution_snapshot.py` | Verified |
| `scripts/shared/mcp_dedup.py` | Correct a comment that names the removed key | Reword the comment so it no longer cites `eventbus_db_path` | REQ-005 / AC-05 | `scripts/shared/mcp_dedup.py:31` (checked in Step 3) | `tests/shared/test_mcp_dedup.py` | Verified |
| `scripts/agent/production_config_validator.py` | Reject the removed key | Remove `"eventbus_db_path"` from the allowed-key set so the key fails validation | REQ-005 / AC-05 | `scripts/agent/production_config_validator.py:198` (checked in Step 3) | `tests/agent/test_production_config_validator.py` | Verified |
| `config/agent.toml` | Remove the key | Delete the `eventbus_db_path` line | REQ-005 / AC-05 | `config/agent.toml:20` (checked in Step 3) | `tests/agent/test_production_config_validator.py`, `tests/test_production_isolation.py` | Verified |
| `tools/check_db_separation.py` | ADR-008 check without the Agent-side accessors | Read the eventbus DDL from `scripts/eventbus/schema.sql` and the eventbus default path from `config/eventbus.toml`; keep the four-database checks | REQ-006 / AC-06 | `tools/check_db_separation.py:118-126,180-196` (checked in Step 3) | `tests/tools/test_check_db_separation.py` | Verified |
| `tests/tools/test_check_db_separation.py` | Keep the checker tests valid | Build the eventbus DDL through the checker's new source instead of `db.schema_sql` | REQ-006, REQ-007 / AC-06 | `tests/tools/test_check_db_separation.py:15-25` uses `mod._schema_ddl()` and the `"eventbus"` key (checked in Step 3) | `uv run pytest tests/tools/test_check_db_separation.py -v` | Verified |
| `tests/agent/test_production_config_validator.py` | Lock the removed key | Add a test that an `agent.toml` with `eventbus_db_path` is rejected | REQ-005 / AC-05 | File exists; validator tests live here (checked in Step 3) | `uv run pytest tests/agent/test_production_config_validator.py -v` | Verified |
| `tests/conftest.py` | Stop creating eventbus.sqlite through `create_schema` | Replace the `create_eventbus_schema()` call and the `eventbus_db_path` isolation field with the EventBus-side tool against an isolated path | REQ-007 / AC-07 | `tests/conftest.py:101,144` (checked in Step 3) | `uv run python tools/check_conftest_integrity.py`, `uv run pytest tests/db tests/eventbus -v` | Verified |
| `tests/test_production_isolation.py` | Drop the removed key | Remove `eventbus_db_path` from the isolated-field list and the printed config | REQ-007 / AC-07 | `tests/test_production_isolation.py:45,130` (checked in Step 3) | `uv run pytest tests/test_production_isolation.py -v` | Verified |
| `tests/db/test_create_schema.py` | Remove EventBus creation tests from the Agent-side suite | Remove the eventbus target helpers and cases; their behavior moves to `tests/eventbus/test_eventbus_db_tools.py` | REQ-007 / AC-07 | `tests/db/test_create_schema.py:24,194-198,827` (checked in Step 3) | `uv run pytest tests/db/test_create_schema.py -v` | Verified |
| `tests/db/test_db_maintenance.py` | Remove eventbus rotation tests | Remove `rotate_eventbus_db` import, the `eventbus_db_path` setup, and the happy-path test (moved) | REQ-007 / AC-07 | `tests/db/test_db_maintenance.py:30,69,1119-1127` (checked in Step 3) | `uv run pytest tests/db/test_db_maintenance.py -v` | Verified |
| `tests/db/test_db_recovery.py` | Remove the eventbus recovery target cases | Remove the `eventbus_db_path` mock and the `recover_corruption(target="eventbus")` cases | REQ-007 / AC-07 | `tests/db/test_db_recovery.py:27,350,594,623` (checked in Step 3) | `uv run pytest tests/db/test_db_recovery.py -v` | Verified |
| `tests/db/test_recovery_drill.py` | Three-domain drill | Remove the eventbus domain fixtures and the `eventbus_db_path` config lines | REQ-007 / AC-07 | `tests/db/test_recovery_drill.py:277,286,304` (checked in Step 3) | `uv run pytest tests/db/test_recovery_drill.py -v` | Verified |
| `tests/db/test_sqlite_helper.py` | Drop the removed constructor argument and target | Remove `eventbus_db_path=` and the `("eventbus", False)` case | REQ-007 / AC-07 | `tests/db/test_sqlite_helper.py:247,286,298,332` (checked in Step 3) | `uv run pytest tests/db/test_sqlite_helper.py -v` | Verified |
| `tests/deploy/test_init_db_eventbus_schema.py` | Follow the deploy script change | Use `scripts/eventbus/schema.sql` for the fixture DDL and assert the EventBus-tool path of `init_db.sh` | REQ-003, REQ-007 / AC-03, AC-07 | `tests/deploy/test_init_db_eventbus_schema.py:25,60` (checked in Step 3) | `uv run pytest tests/deploy/test_init_db_eventbus_schema.py -v` | Verified |
| `tests/deploy/test_init_db_schema_gate.py` | Follow the deploy script change | Replace `build_eventbus_schema_sql` fixture use | REQ-003, REQ-007 / AC-03, AC-07 | `tests/deploy/test_init_db_schema_gate.py:27,73` (checked in Step 3) | `uv run pytest tests/deploy/test_init_db_schema_gate.py -v` | Verified |
| `tests/deploy/test_setup_services_eventbus.py` | Replace the removed DDL accessor | Replace `build_eventbus_schema_sql` fixture use | REQ-007 / AC-07 | `tests/deploy/test_setup_services_eventbus.py:25,137` (checked in Step 3) | `uv run pytest tests/deploy/test_setup_services_eventbus.py -v` | Verified |
| `tests/eventbus/test_eventbus_startup.py` | Replace the removed DDL accessor and version helper | Read the DDL from `scripts/eventbus/schema.sql` and take the version from the EventBus-side source | REQ-007 / AC-07 | `tests/eventbus/test_eventbus_startup.py:18,298,313,325` (checked in Step 3) | `uv run pytest tests/eventbus/test_eventbus_startup.py -v` | Verified |
| `tests/shared/test_execution_snapshot.py` | Three-database snapshot | Remove `eventbus_db_path` config lines and eventbus labels from expectations | REQ-005, REQ-007 / AC-05, AC-07 | `tests/shared/test_execution_snapshot.py:67,75,211,224` (checked in Step 3) | `uv run pytest tests/shared/test_execution_snapshot.py -v` | Verified |
| `tests/shared/test_mcp_dedup.py` | Drop the removed field name | Remove `"eventbus_db_path"` from the field-name filter | REQ-005, REQ-007 / AC-05, AC-07 | `tests/shared/test_mcp_dedup.py:338` (checked in Step 3) | `uv run pytest tests/shared/test_mcp_dedup.py -v` | Verified |
| `tests/agent/test_repl.py` | Drop the removed constructor argument | Remove the three `eventbus_db_path=` arguments | REQ-007 / AC-07 | `tests/agent/test_repl.py:1034,1091,1120` (checked in Step 3) | `uv run pytest tests/agent/test_repl.py -v` | Verified |
| `tests/integration/test_session_recovery.py` | Drop the removed constructor argument | Remove the `eventbus_db_path=` argument | REQ-007 / AC-07 | `tests/integration/test_session_recovery.py:49` (checked in Step 3) | `uv run pytest tests/integration/test_session_recovery.py -v` | Verified |
| `tests/agent/memory/test_memory_vec_session.py` | Drop the removed constructor argument | Remove the `eventbus_db_path=` argument | REQ-007 / AC-07 | `tests/agent/memory/test_memory_vec_session.py:36` (checked in Step 3) | `uv run pytest tests/agent/memory/test_memory_vec_session.py -v` | Verified |
| `tests/rag/test_fts_sync.py` | Drop the removed attribute assignment | Remove the `cfg.eventbus_db_path = ...` line | REQ-007 / AC-07 | `tests/rag/test_fts_sync.py:66` (checked in Step 3) | `uv run pytest tests/rag/test_fts_sync.py -v` | Verified |
| `registry/manifests/agent_api.yaml` | Generated manifest | Regenerate with `tools/generate_reference_table.py --manifests` after the deletion (not hand-edited) | REQ-001, REQ-008 / AC-01 | `registry/manifests/agent_api.yaml:147-157` lists `scripts/agent/eventbus_client.py` (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | Generated reference | Regenerate the guarded block (not hand-edited) | REQ-001, REQ-008 / AC-01 | File lists `EventBusClient` (`rg` hit, checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `docs/23_agent/agent_02_runtime-architecture.md` | Describe the remaining client modules accurately | Remove `eventbus_client.py` and `EventBusClient` from the "EventBus Client Modules" section | REQ-008 / AC-08 | `docs/23_agent/agent_02_runtime-architecture.md:155-157` (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Dependency graph statement | Remove `eventbus_client.py` from the "no runtime component calls the Event Bus" note and state the database ownership edge | REQ-008 / AC-08 | `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md:125-128` (checked in Step 3) | `uv run python tools/check_docs_quality.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Actual caller model | Rewrite the `Review Triggers` item (line 272) that assumes a single trusted Agent caller | REQ-008 / AC-08 | ADR-013 line 272 (the only Agent reference in the ADR) vs `docs/24_eventbus/eventbus_01_system-overview.md` (checked in Step 3) | `uv run python tools/check_adr_preservation.py`, `check_adr_authority.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Ownership of eventbus.sqlite | Update the `rotate_all_dbs()` backup statements (lines 68, 101), `Target APIs or processing paths` (line 146), and the implementation references (line 404) for EventBus-owned creation, rotation, and verification | REQ-008 / AC-08 | ADR-008 lines 68, 101, 146, 404 name `rotate_all_dbs()`, `rotate_eventbus_db()`, and `DbConfig.eventbus_db_path` (checked in Step 3) | `uv run python tools/check_adr_preservation.py`, `check_adr_authority.py` | Verified |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Config ownership text | Remove `EVENTBUS` from the `DbTarget` description | REQ-008 / AC-08 | `db_01` line 48 lists `DbTarget` members including `EVENTBUS` (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Schema reference ownership | Remove the Agent-side creation reference for eventbus.sqlite | REQ-008 / AC-08 | One hit for the removed symbols (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Rotation and recovery operations | Describe eventbus.sqlite rotation and verification through the EventBus-side tool | REQ-008 / AC-08 | Six hits including `eventbus_db_path` (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_08_active_databases.md` | Active database inventory | Remove `eventbus_db_path` as the eventbus path source | REQ-008 / AC-08 | Two hits including `eventbus_db_path` (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `docs/90_deployment/deployment_01_deployment.md` | Deploy procedure text | Update the init_db description (EventBus-side creation and gate) | REQ-008 / AC-08 | Five hits including `eventbus_db_path` (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain deployment` | Verified |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Schema ownership statement | Describe creation and rotation as EventBus-owned | REQ-008 / AC-08 | Two hits for the removed symbols (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Retention note names the removed function | Reword the note on archives written by `rotate_eventbus_db()` | REQ-008 / AC-08 | `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:118` (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Creation and rotation ownership | Rewrite the `create_eventbus_schema()` sentence (line 49) and the `rotate_eventbus_db()` table cell (line 83) | REQ-008 / AC-08 | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md:49,83` (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain db` | Verified |
| `tests/eventbus/test_eventbus_schema_version.py` | Import the schema version helper from the EventBus-side tool | Import the schema version helper from the EventBus-side tool; found by the consumer re-scan in plan-to-implementation-procedure Step 3a | REQ-007 / N/A: none cites REQ-007 | tests/eventbus/test_eventbus_schema_version.py:28 imports eventbus_schema_version from db.schema_sql, removed with the Agent-side accessors (checked in Step 3a) | uv run pytest tests/eventbus/test_eventbus_schema_version.py -v | Verified |
| `registry/manifests/db_schema_versions.yaml` | Regenerate the generated manifest after eventbus_db_path leaves DbConfig | Regenerate the generated manifest after eventbus_db_path leaves DbConfig; found by the consumer re-scan in plan-to-implementation-procedure Step 3a | REQ-005 / N/A: none cites REQ-005 | registry/manifests/db_schema_versions.yaml:2 lists config_key eventbus_db_path as a db_path entry (checked in Step 3a) | uv run python tools/generate_reference_table.py --check | Verified |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Reword the archive sentence that names rotate_eventbus_db() | Reword the archive sentence that names rotate_eventbus_db(); found by the consumer re-scan in plan-to-implementation-procedure Step 3a | REQ-008 / N/A: none cites REQ-008 | docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md:199 names rotate_eventbus_db() (checked in Step 3a) | uv run python tools/check_docs_consistency.py --domain eventbus | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/schema.py` | `_init_schema` create-or-validate semantics the tool must preserve | REQ-002 |
| `scripts/eventbus/db_conn.py` | `open_db` and pragma setup the tool reuses | REQ-002 |
| `scripts/eventbus/config.py` | `load_config`, `get_config_path`, `db_path` validation | REQ-002 |
| `scripts/shared/eventbus_schema_fingerprint.py` | `assert_matches` and `validate_canonical` used by the gate and the tool | REQ-002, REQ-003 |
| `config/eventbus.toml` | The EventBus-owned `db_path` | REQ-002, REQ-006 |
| `scripts/eventbus/schema.sql` | Canonical DDL and `user_version` stamp | REQ-002, REQ-006, REQ-007 |
| `.importlinter` | `db`/`shared`/`eventbus` import contracts | REQ-002 |
| `scripts/agent/eventbus_subscriber.py` | Remains; confirm it does not import the deleted client | REQ-001 |
| `scripts/agent/eventbus_topic_admin_client.py` | Remains; confirm it does not import the deleted client | REQ-001 |
| `tests/eventbus/eventbus_helpers.py` | `make_eventbus_client` helper (name collision with the deleted client, no change needed) | REQ-001 |
| `rules/env.md` | Architecture and `deploy/deploy.sh` effects of a `config/*.toml` change | REQ-003, REQ-005 |
| `deploy/deploy.sh` | Copies `config/agent.toml` and rsyncs `scripts/`; no line to add or remove | REQ-003, REQ-005 |

## Acceptance Criteria
- `AC-01` (REQ-001): `rg -n "\bEventBusClient\b|EventBusClientConfig|EventBusPublish|agent/eventbus_client|agent\.eventbus_client" scripts/ tests/ config/ docs/ registry/` returns no match.
- `AC-02` (REQ-002): `tests/eventbus/test_eventbus_db_tools.py` passes; the tool reads its path only from the EventBus configuration (a test asserts an `agent.toml` value is not consulted); `PYTHONPATH=scripts uv run lint-imports` keeps all contracts.
- `AC-03` (REQ-003): the init_db integration tests pass and show a fresh database created by the EventBus-side tool, an existing current database accepted, and a stale or unstamped database refused unchanged.
- `AC-04` (REQ-004): `rg -n "DbTarget\.EVENTBUS|build_eventbus_schema_sql|create_eventbus_schema|rotate_eventbus_db|eventbus_db_path" scripts/db/ scripts/shared/ scripts/agent/` returns no match.
- `AC-05` (REQ-005): `agent.toml` containing `eventbus_db_path` fails validation (test); `config/agent.toml` has no such key; the execution snapshot reports three databases.
- `AC-06` (REQ-006): `uv run python tools/check_db_separation.py` passes and `tests/tools/test_check_db_separation.py` passes.
- `AC-07` (REQ-007): `uv run pytest tests/db tests/eventbus tests/agent tests/shared tests/tools tests/deploy tests/integration -v` passes; `uv run python tools/check_conftest_integrity.py` passes.
- `AC-08` (REQ-008): `check_docs_consistency.py` for `agent`, `db`, `eventbus`, and `deployment`, `check_adr_authority.py`, `check_adr_preservation.py`, `check_docs_content_policy.py --strict`, and `generate_reference_table.py --check` pass.
- The only remaining named matches for `eventbus_db_path`-like keys are the EventBus's own `db_path`; the Implementation procedure and PR name them.

## Tests
- `REQ-002`: new `tests/eventbus/test_eventbus_db_tools.py` (fresh, current, stale version, unstamped, malformed shape, rotate verified, path source).
- `REQ-003`: `tests/deploy/test_init_db_eventbus_schema.py` and `tests/deploy/test_init_db_schema_gate.py`, updated.
- `REQ-004`, `REQ-007`: the updated `tests/db/` suite, `tests/conftest.py` isolation, and `tests/eventbus/test_eventbus_startup.py`.
- `REQ-005`: new rejection test in `tests/agent/test_production_config_validator.py`; `tests/shared/test_execution_snapshot.py`.
- `REQ-006`: `tests/tools/test_check_db_separation.py` and the live run of the checker.
- `REQ-001`, `REQ-008`: grep acceptance checks and the documentation checkers.

## Documentation Impact
- Required (REQ-008): ADR-013 (`Review Triggers`), ADR-008 (backup statements, `Recovery Policy Matrix`, `Target APIs or processing paths`, implementation references), `db_01`, `db_02`, `db_03`, `db_07`, `db_08`, `deployment_01`, `eventbus_06`, `agent_02`, `agent_10_01`, `governance_05`, and the generated `agent_13`. Docs are written in English and follow `skills/DESIGN.md` Docs content policy: intent, boundaries, and failure behavior, not symbol inventories.
- A remaining unconfirmed caller or operator procedure is recorded as a Needs Confirmation item through `governance_03` (`tools/check_needs_confirmation_inventory.py`), not as inline prose.

## Assumptions
- Overlap with the rows added by the Step 3a amendments (judged 2026-11-10): `registry/manifests/db_schema_versions.yaml` and `tests/eventbus/test_eventbus_schema_version.py` are also targets of `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md`: sequencing dependency, this Plan first (plan 005 already records plan 002 as its predecessor); `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` has no other Frozen Plan.
- Step 3a correction (2026-11-10): `eventbus.config.load_config` resolves `${ENV:...}` token references and raises when `auth_token` is empty (`scripts/eventbus/config.py:365-373`), and `deploy/init_db.sh` does not export the EventBus token variables, so the tool reads `db_path` with its own minimal reader. Falsifiable by `tests/deploy/test_init_db_eventbus_schema.py` running without token variables.
- Step 3a additions (fallout rows added by `tools/amend_plan.py` on 2026-11-10): `tests/eventbus/test_eventbus_schema_version.py` (imports `db.schema_sql.eventbus_schema_version`, removed with the Agent-side accessors; the version helper moves to the EventBus-side tool), `registry/manifests/db_schema_versions.yaml` (generated; lists `eventbus_db_path` as a `db_path` entry), `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (names `rotate_eventbus_db()` at line 199). `eventbus_schema_version` is removed from `scripts/db/schema_sql.py` and exposed by `scripts/eventbus/db_tools.py` as `schema_version`.
- The maintainer's decision (2026-11-10) fixes the design: EventBus-side tooling owns creation, rotation, and verification; the Agent-side `scripts/db/` loses all eventbus handling.
- The EventBus-side tool is an operator and deploy entry point, not part of the service request path; it may be invoked as `python -m eventbus.db_tools` from `deploy/init_db.sh` with `PYTHONPATH=${DEPLOY_SCRIPTS}`. Falsifiable by the `tests/deploy/test_init_db_*` integration tests.
- The execution snapshot reporting three databases instead of four is an accepted observability change (the snapshot cannot read `eventbus.toml` without a second configuration read in a shared leaf). Falsifiable by the owner; see UNK-03.
- `tools/check_db_separation.py` is repository tooling, not a process under ADR-002, so it may read `config/eventbus.toml` directly.
- Overlap with other Frozen Plans: `tools/check_plan_target_overlaps.py` reports none for these rows other than the ADR-013 sequencing note above (checked in Step 8b).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which component or operator procedure rotates and backs up eventbus.sqlite in production, under which configuration file | No caller of `rotate_all_dbs`/`rotate_eventbus_db` in `deploy/`, `scripts/`, `tools/`, `config/`, `.github/`; operator runbooks outside the repository are not visible | Maintainer confirms; the Implementation procedure keeps a rotate entry in the EventBus-side tool so an operator invocation has a replacement; record any external procedure through `governance_03` | False |
| UNK-02 | Whether `scripts/agent/eventbus_subscriber.py` and `scripts/agent/eventbus_topic_admin_client.py` (same unused status) should also be deleted | An owner decision; the Issue names only the publish client and the maintainer plans a future integration | Owner decides; if yes, file a follow-up Issue (this Plan leaves both in place and documents them accurately) | False |
| UNK-03 | Parity of the eventbus recovery drill: today `recovery_drill.py` produces RPO/RTO audit artifacts for the eventbus domain; the EventBus-side tool will verify integrity and fingerprint but not reproduce the artifact format | Whether operators consume the eventbus drill artifact | Maintainer confirms; the Plan accepts verify-only parity (integrity and fingerprint, matching `_verify_eventbus`) | False |
| UNK-04 | Whether the snapshot (`execution_snapshot`) consumers need an eventbus entry | Consumers of `schema_versions`/`db_paths` outside `tests/shared/test_execution_snapshot.py` | Run `rg` over `scripts/` and `docs/` for the snapshot keys during the procedure; if a consumer needs it, add a row by Plan amendment | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/eventbus_client.py` | delete | Low: no `scripts/` importer; listed in generated references | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_eventbus_client.py` | delete | Low: tests of the deleted module only | N/A | N/A | not applicable (rsynced) |
| `scripts/eventbus/db_tools.py` | create | Medium: new deploy-path entry point | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_db_tools.py` | create | Low: new tests | N/A | N/A | not applicable (rsynced) |
| `deploy/init_db.sh` | modify | High: first-deploy gate; `tests/deploy/test_init_db_*` | N/A | N/A | not applicable (rsynced) |
| `scripts/db/helper.py` | modify | High: `SQLiteHelper` is used by every `db` caller | N/A | N/A | not applicable (rsynced) |
| `scripts/db/create_schema.py` | modify | High: run by `deploy/init_db.sh` and `tests/conftest.py` | N/A | N/A | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | modify | High: DDL accessors used by tools and tests | N/A | N/A | not applicable (rsynced) |
| `scripts/db/config.py` | modify | High: `DbConfig` constructed in six test modules | N/A | N/A | not applicable (rsynced) |
| `scripts/db/rotation.py` | modify | Medium: `rotate_all_dbs` return arity changes | N/A | N/A | not applicable (rsynced) |
| `scripts/db/recovery_drill.py` | modify | Medium: run by `init_db.sh` with `RUN_RECOVERY_DRILL=1` | N/A | N/A | not applicable (rsynced) |
| `scripts/db/recovery.py` | modify | Medium: `recover_corruption` target set | N/A | N/A | not applicable (rsynced) |
| `scripts/db/__init__.py` | modify | Low: export list | N/A | N/A | not applicable (rsynced) |
| `scripts/shared/execution_snapshot.py` | modify | Medium: snapshot shape (four to three databases) | N/A | N/A | not applicable (rsynced) |
| `scripts/shared/mcp_dedup.py` | modify | Low: comment only | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/production_config_validator.py` | modify | Medium: startup validation of `agent.toml` | N/A | N/A | not applicable (rsynced) |
| `config/agent.toml` | modify | Medium: a deployed file that still has the key would now fail validation | N/A | N/A | not applicable (rsynced) |
| `tools/check_db_separation.py` | modify | Medium: CI `lint` job and deploy pre-check | N/A | N/A | not applicable (rsynced) |
| `tests/tools/test_check_db_separation.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_production_config_validator.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/conftest.py` | modify | High: autouse isolation for the whole suite | N/A | N/A | not applicable (rsynced) |
| `tests/test_production_isolation.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_db_maintenance.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_db_recovery.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_recovery_drill.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_sqlite_helper.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/deploy/test_init_db_eventbus_schema.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/deploy/test_init_db_schema_gate.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/deploy/test_setup_services_eventbus.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_startup.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_execution_snapshot.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_mcp_dedup.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_repl.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/integration/test_session_recovery.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/memory/test_memory_vec_session.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_fts_sync.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `registry/manifests/agent_api.yaml` | modify | Low: generated | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_13_reference-api-generated.md` | modify | Low: generated | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_02_runtime-architecture.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | modify | Medium: ADR preservation checks | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | modify | Medium: ADR preservation checks | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_08_active_databases.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/90_deployment/deployment_01_deployment.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_schema_version.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `registry/manifests/db_schema_versions.yaml` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |

## Design
- **Ownership decision** (maintainer, 2026-11-10; alternatives: keep `DbTarget.EVENTBUS` and read `eventbus.toml` from `scripts/db` through a shared reader; or split into two Plans): EventBus-side tooling. The shared-reader option was rejected because `db` would then read another process's configuration, which ADR-002 forbids; the split option was rejected by the maintainer. Compatibility impact: `scripts/db/` loses eventbus support (`rotate_all_dbs` returns three paths, `recovery_drill --domain all` covers three domains, `SQLiteHelper("eventbus")` is rejected), and `agent.toml` containing `eventbus_db_path` fails validation after this change, so a deployed `/opt/llm/config/agent.toml` must carry the removal before the validator reaches production (deploy order is in Phase 6).
- **EventBus-side tool**: `scripts/eventbus/db_tools.py` offers `ensure` (create when absent, accept only the current schema, refuse and leave a stale or unstamped database unchanged: the `_init_schema` semantics and the refusal text already in `scripts/eventbus/schema.py`), `rotate` (sqlite backup-API copy to a timestamped archive, then `PRAGMA integrity_check` and `assert_matches`), and `verify` (integrity plus fingerprint, the checks of today's `_verify_eventbus`). It imports `eventbus.*`, `shared.eventbus_schema_fingerprint`, and the standard library only, which `.importlinter` allows; it cannot reuse `db.rotation`/`db.recovery` (they import `db.helper`). `deploy/init_db.sh` calls it through `python -m eventbus.db_tools` with `EVENTBUS_CONFIG_PATH` honoring the existing override.
- **Consumer scan** (`tools/scan_change_consumers.py --seed eventbus_db_path --seed build_eventbus_schema_sql --seed DbTarget.EVENTBUS --seed rotate_eventbus_db`, 145 candidates): reconciled with `rg` for the four symbols; every consumer is a target row above or a reference row; `not affected`: `docs/10_adr/adr_01_index.md`, the ADR-001/005/009 files, `tests/agent/test_repl_health.py`, `tests/agent/test_session_memory_boundary.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/eventbus/test_eventbus_schema_version.py`, `tests/integration/conftest.py`, `tests/integration/test_session_sqlite.py`, `tools/check_chunks_fts_invariant.py` and `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (matches without any of the four symbols; they use `DbConfig` defaults or other wording); `not affected: scripts/shared/eventbus_schema_fingerprint.py` (its eventbus path is a path to `schema.sql`, not a database path), `not affected: scripts/eventbus/*` other than the new tool (the service already owns its path), `not affected: tests/eventbus/eventbus_helpers.py` (`make_eventbus_client` is a test helper). The scan lists candidates only (text search); indirect users are not detected.
- **Path B analysis** (Step 5): architecture: `.importlinter` contracts (`shared-is-leaf`, `db-only-uses-shared`, `eventbus-is-isolated`) shape the tool; `PYTHONPATH=scripts uv run lint-imports` reports 6 contracts kept, 0 broken today. Dependency graph: importers of the removed symbols are in the target rows above (about 50 files including tests). Historical: `git log --since=30.days` shows active EventBus churn (`scripts/eventbus/delivery_repo.py` 13, `app.py` 12); churn and bus factor for `scripts/db/*` were not measured individually (`N/A`). Operational: no port or process change; eventbus.sqlite is touched only by `deploy/init_db.sh` and the EventBus service; stop the EventBus service before rotation (the rotate entry uses the backup API and does not require it, but the operator procedure keeps the stop). `ss`, `fuser`, and `pip-audit` were not run (no dependency change; the production DB is not inspected by this analysis). Persisted schema check (`rules/persisted-schema-change.md`): the DDL and `user_version` are unchanged (`scripts/eventbus/schema.sql` is not a target), so only the creator changes; recorded in Risks.
- **Validation quality baseline**: `radon`, `vulture`, and `bandit` baselines were recorded for the sibling Plan in this session; the `scripts/db/` modules are the same files for `vulture` (`scripts/` run: findings only in `scripts/rag/` and `scripts/shared/runtime_paths.py`, none in these targets) and `bandit` (3 High findings in `scripts/eventbus`, pre-existing, not in the new file's scope). diff-cover baseline: `N/A: no code diff yet`; implementation raises diff coverage to the `rules/toolchain.md` threshold.
- **Path classification**: Path B (more than 3 files; changes a runtime and deploy interface and configuration).

## Implementation steps
1. **Phase 1: Add the EventBus-side tool (additive, no removal)**
   - [ ] Create `scripts/eventbus/db_tools.py` (`ensure`, `rotate`, `verify`; path from `eventbus.config`) and `tests/eventbus/test_eventbus_db_tools.py` (REQ-002; `scripts/eventbus/db_tools.py`, `tests/eventbus/test_eventbus_db_tools.py`).
2. **Phase 2: Switch deploy and the ADR-008 checker to the new owner**
   - [ ] Change `deploy/init_db.sh` so eventbus.sqlite is created, gated, and drilled through the tool, and keep `create_schema.py` creating the other three databases (REQ-003; `deploy/init_db.sh`, `tests/deploy/test_init_db_eventbus_schema.py`, `tests/deploy/test_init_db_schema_gate.py`).
   - [ ] Switch `tools/check_db_separation.py` to `scripts/eventbus/schema.sql` and `config/eventbus.toml` (REQ-006; `tools/check_db_separation.py`, `tests/tools/test_check_db_separation.py`).
3. **Phase 3: Remove Agent-side eventbus support and the config key**
   - [ ] Remove the eventbus code from `scripts/db/helper.py`, `create_schema.py`, `schema_sql.py`, `config.py`, `rotation.py`, `recovery_drill.py`, `recovery.py`, `__init__.py`; remove the `eventbus_db_path` mapping from `scripts/shared/execution_snapshot.py` and the comment in `scripts/shared/mcp_dedup.py` (REQ-004, REQ-005).
   - [ ] Remove `eventbus_db_path` from `scripts/agent/production_config_validator.py` and `config/agent.toml`; add the rejection test to `tests/agent/test_production_config_validator.py` (REQ-005).
   - [ ] Update `tests/conftest.py`, `tests/test_production_isolation.py`, `tests/db/test_create_schema.py`, `tests/db/test_db_maintenance.py`, `tests/db/test_db_recovery.py`, `tests/db/test_recovery_drill.py`, `tests/db/test_sqlite_helper.py`, `tests/deploy/test_setup_services_eventbus.py`, `tests/eventbus/test_eventbus_startup.py`, `tests/shared/test_execution_snapshot.py`, `tests/shared/test_mcp_dedup.py`, `tests/agent/test_repl.py`, `tests/integration/test_session_recovery.py`, `tests/agent/memory/test_memory_vec_session.py`, `tests/rag/test_fts_sync.py` (REQ-007). This phase is one release unit (see below).
   - [ ] Import the schema version helper from the EventBus-side tool (REQ-007; `tests/eventbus/test_eventbus_schema_version.py`) — amendment 2026-11-10
   - [ ] Regenerate the generated manifest after eventbus_db_path leaves DbConfig (REQ-005; `registry/manifests/db_schema_versions.yaml`) — amendment 2026-11-10
4. **Phase 4: Delete the unused client**
   - [ ] Delete `scripts/agent/eventbus_client.py` and `tests/agent/test_eventbus_client.py`; regenerate `registry/manifests/agent_api.yaml` and `docs/23_agent/agent_13_reference-api-generated.md` with `tools/generate_reference_table.py` (REQ-001).
5. **Phase 5: Documentation**
   - [ ] Update ADR-013, ADR-008, `db_01`, `db_02`, `db_03`, `db_07`, `db_08`, `deployment_01`, `eventbus_06`, `agent_02`, `agent_10_01`, `governance_05`; register any Needs Confirmation item through `governance_03` (REQ-008; the twelve document rows of `Implementation Target Files`).
   - [ ] Reword the archive sentence that names rotate_eventbus_db() (REQ-008; `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`) — amendment 2026-11-10
6. **Phase 6: Deployment and verification**
   - [ ] Run the full validation sequence in `rules/toolchain.md`. After the change is committed and pushed (the user's decision), hand off to `skills/deploy/SKILL.md`: `scripts/`, `config/agent.toml`, and `deploy/init_db.sh` changed, so deploy copies the new `agent.toml` without the key and runs `init_db.sh` on the existing databases (REQ-003, REQ-005; `deploy/init_db.sh`, `config/agent.toml`).

### Release units
**Unit**: db-eventbus-removal | **Phases**: 3 | **Reason**: removing `DbConfig.eventbus_db_path`, `build_eventbus_schema_sql`, and `create_eventbus_schema` breaks every test and fixture that uses them until the matching test updates land in the same change; the sub-tasks of Phase 3 cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/db_tools.py` | Unit and integration against temporary databases | `uv run pytest tests/eventbus/test_eventbus_db_tools.py -v` | Passes (create, current, stale, unstamped, malformed, rotate, path source) |
| `deploy/init_db.sh` | Integration with sandboxed `DEPLOY_SCRIPTS`/`DEPLOY_DB` | `uv run pytest tests/deploy -v` | Passes for fresh, current, and stale databases |
| `scripts/db/`, `scripts/shared/`, `scripts/agent/` | Unit and integration | `uv run pytest tests/db tests/eventbus tests/agent tests/shared tests/integration -v` | All pass |
| Whole repository | Full validation sequence | `rules/toolchain.md`: `uv run ruff format`, `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, full `uv run pytest` | No new findings; all pass |
| Impact radius | Search | `rg -l '\bDbTarget\b\|eventbus_db_path' tests/ scripts/` before removal; the AC-01 and AC-04 greps after | Every hit reviewed; the greps return no match |
| ADR-008 | Repository check | `uv run python tools/check_db_separation.py` | Passes |
| Config rejection | Unit | `uv run pytest tests/agent/test_production_config_validator.py -v` | Key `eventbus_db_path` rejected |
| Tools and conftest | Repository checks | `uv run python tools/check_conftest_integrity.py`, `uv run python tools/check_module_size.py`, `uv run python tools/check_mock_patch_targets.py` | Pass |
| Documents | Documentation checks | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent\|db\|eventbus\|deployment`, `check_adr_preservation.py`, `check_adr_authority.py`, `check_needs_confirmation_inventory.py` | All pass |
| Generated references | Drift check | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Diff coverage | Coverage | `rules/toolchain.md` section 7 diff-cover sequence | At or above the Completion checklist threshold |

## Risks
- **Risk**: A fresh deploy fails at `init_db.sh` because eventbus.sqlite is no longer created by `create_schema.py` → **Mitigation**: Phase 2 switches the script to the EventBus-side tool before Phase 3 removes the Agent-side branch; the deploy integration tests cover fresh, current, and stale databases.
- **Risk**: `/opt/llm/config/agent.toml` still has `eventbus_db_path` when the new validator reaches production, so the Agent refuses to start → **Mitigation**: the deploy copies the repository `agent.toml` (`deploy/deploy.sh:147`) in the same step as `scripts/`; the Phase 6 hand-off states the order and the rollback is `git revert` of the change.
- **Risk**: The two creators race during the transition (init_db tool and service startup) → **Mitigation**: both use the same create-or-validate semantics on the same file and the service runs after `init_db.sh` (`deploy/setup_services.sh` follows it); the tool refuses a stale database instead of altering it.
- **Risk**: Operators lose the eventbus drill artifact (RPO/RTO) and `rotate_all_dbs` arity changes → **Mitigation**: UNK-01 and UNK-03 to the maintainer; the tool's `rotate` and `verify` give a replacement; documented in `db_07`.
- **Risk**: The snapshot loses the eventbus entry, hiding a schema-version mismatch in the snapshot → **Mitigation**: UNK-04; the EventBus startup (`_init_schema`) and the init_db gate remain the checks of record.
- **Risk**: A migration-free change of the schema creator hides a drift between `scripts/eventbus/schema.sql` and the live file → **Mitigation**: the DDL, `user_version`, and fingerprint are unchanged; the persisted-schema checklist outcome is that no schema is altered.
- **Risk**: Removing the tests of Agent-side eventbus creation loses coverage → **Mitigation**: each removed case has a counterpart in `tests/eventbus/test_eventbus_db_tools.py` (Phase 1 lands first).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the EventBus-side tool (additive, no removal) | In Progress | — | — |  |
| 2 | Switch deploy and the ADR-008 checker to the new owner | In Progress | — | — |  |
| 3 | Remove Agent-side eventbus support and the config key | In Progress | — | — |  |
| 4 | Delete the unused client | In Progress | — | — |  |
| 5 | Documentation | In Progress | — | — |  |
| 6 | Deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261110-102050_01_scripts_agent_eventbus_client.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261110-102050_03_scripts_eventbus_db_tools.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261110-102050_04_tests_eventbus_test_eventbus_db_tools.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261110-102050_05_deploy_init_db.sh.md | 2 | Procedure | Pending | — | — |
| implementations/20261110-102050_06_scripts_db_helper.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_07_scripts_db_create_schema.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_08_scripts_db_schema_sql.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_09_scripts_db_config.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_10_scripts_db_rotation.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_11_scripts_db_recovery_drill.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_12_scripts_db_recovery.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_13_scripts_db___init__.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_14_scripts_shared_execution_snapshot.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_15_scripts_shared_mcp_dedup.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_16_scripts_agent_production_config_validator.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_17_config_agent.toml.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_18_tools_check_db_separation.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261110-102050_20_tests_agent_test_production_config_validator.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_21_tests_conftest.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_22_tests_test_production_isolation.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_23_tests_db_test_create_schema.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_24_tests_db_test_db_maintenance.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_27_tests_db_test_sqlite_helper.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_30_tests_deploy_test_setup_services_eventbus.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_34_tests_agent_test_repl.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_35_tests_integration_test_session_recovery.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_36_tests_agent_memory_test_memory_vec_session.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_37_tests_rag_test_fts_sync.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_38_registry_manifests_agent_api.yaml.md | 4 | Procedure | Pending | — | — |
| implementations/20261110-102050_39_docs_23_agent_agent_13_reference-api-generated.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261110-102050_40_docs_23_agent_agent_02_runtime-architecture.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_41_docs_00_governance_governance_05_change-impact-and-dependency-graphs.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_42_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_43_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_44_docs_41_db_db_01_architecture_and_schema-overview-and-config.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_45_docs_41_db_db_02_architecture_and_schema-schema-reference.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_46_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_47_docs_41_db_db_08_active_databases.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_48_docs_90_deployment_deployment_01_deployment.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_49_docs_24_eventbus_eventbus_06_persistence_schema_and_replay.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_50_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_51_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261110-102050_52_tests_eventbus_test_eventbus_schema_version.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_53_registry_manifests_db_schema_versions.yaml.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-102050_54_docs_24_eventbus_eventbus_05_dlq_offsets_and_delivery_semantics.md.md | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-112538_adrrev002_agent-eventbus-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261110-091327
- **Related target files**: `scripts/agent/eventbus_client.py`, `tests/agent/test_eventbus_client.py`, `scripts/eventbus/db_tools.py`, `tests/eventbus/test_eventbus_db_tools.py`, `deploy/init_db.sh`, `scripts/db/helper.py`, `scripts/db/create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/config.py`, `scripts/db/rotation.py`, `scripts/db/recovery_drill.py`, `scripts/db/recovery.py`, `scripts/db/__init__.py`, `scripts/shared/execution_snapshot.py`, `scripts/shared/mcp_dedup.py`, `scripts/agent/production_config_validator.py`, `config/agent.toml`, `tools/check_db_separation.py`, `tests/tools/test_check_db_separation.py`, `tests/agent/test_production_config_validator.py`, `tests/conftest.py`, `tests/test_production_isolation.py`, `tests/db/test_create_schema.py`, `tests/db/test_db_maintenance.py`, `tests/db/test_db_recovery.py`, `tests/db/test_recovery_drill.py`, `tests/db/test_sqlite_helper.py`, `tests/deploy/test_init_db_eventbus_schema.py`, `tests/deploy/test_init_db_schema_gate.py`, `tests/deploy/test_setup_services_eventbus.py`, `tests/eventbus/test_eventbus_startup.py`, `tests/shared/test_execution_snapshot.py`, `tests/shared/test_mcp_dedup.py`, `tests/agent/test_repl.py`, `tests/integration/test_session_recovery.py`, `tests/agent/memory/test_memory_vec_session.py`, `tests/rag/test_fts_sync.py`, `registry/manifests/agent_api.yaml`, `docs/23_agent/agent_13_reference-api-generated.md`, `docs/23_agent/agent_02_runtime-architecture.md`, `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/41_db/db_08_active_databases.md`, `docs/90_deployment/deployment_01_deployment.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `tests/eventbus/test_eventbus_schema_version.py`, `registry/manifests/db_schema_versions.yaml`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: delete the client; evidence `scripts/agent/eventbus_client.py:43,74` | `scripts/agent/eventbus_client.py` | 4 | AC-01 | AC-01 grep | Confirmed by repository evidence |
| REQ-001 | Required Changes: delete its tests | `tests/agent/test_eventbus_client.py` | 4 | AC-01 | `uv run pytest tests/agent -v` | Confirmed by repository evidence |
| REQ-001 | Documentation Impact: generated references | `registry/manifests/agent_api.yaml` | 4 | AC-01 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-001 | Documentation Impact: generated references | `docs/23_agent/agent_13_reference-api-generated.md` | 4 | AC-01 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-002 | Implementation Intent: EventBus owns the DB; owner decision 2026-11-10 | `scripts/eventbus/db_tools.py` | 1 | AC-02 | `tests/eventbus/test_eventbus_db_tools.py` | Derived from confirmed evidence |
| REQ-002 | Implementation Intent: EventBus owns the DB | `tests/eventbus/test_eventbus_db_tools.py` | 1 | AC-02 | `uv run pytest tests/eventbus/test_eventbus_db_tools.py -v` | Derived from confirmed evidence |
| REQ-003 | Unresolved Questions: creation path reached by `deploy/init_db.sh` (resolved: yes) | `deploy/init_db.sh` | 2, 6 | AC-03 | `tests/deploy/test_init_db_*` | Confirmed by repository evidence |
| REQ-003 | Testing Expectations: deploy tests | `tests/deploy/test_init_db_eventbus_schema.py` | 2 | AC-03, AC-07 | `uv run pytest tests/deploy -v` | Confirmed by repository evidence |
| REQ-003 | Testing Expectations: deploy tests | `tests/deploy/test_init_db_schema_gate.py` | 2 | AC-03, AC-07 | `uv run pytest tests/deploy -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes: remove `DbTarget.EVENTBUS`, create branch, schema builder | `scripts/db/helper.py` | 3 | AC-04 | `tests/db/test_sqlite_helper.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: remove the create branch | `scripts/db/create_schema.py` | 3 | AC-04 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: remove `build_eventbus_schema_sql` | `scripts/db/schema_sql.py` | 3 | AC-04 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: remove the key from the Agent DB config | `scripts/db/config.py` | 3 | AC-04, AC-05 | `tests/db/test_sqlite_helper.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: rotation resolves from EventBus config only | `scripts/db/rotation.py` | 3 | AC-04 | `tests/db/test_db_maintenance.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: recovery of eventbus.sqlite | `scripts/db/recovery_drill.py` | 3 | AC-04 | `tests/db/test_recovery_drill.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: recovery of eventbus.sqlite | `scripts/db/recovery.py` | 3 | AC-04 | `tests/db/test_db_recovery.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: removed export | `scripts/db/__init__.py` | 3 | AC-04 | `tests/db/test_db_maintenance.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes: remove `eventbus_db_path` | `scripts/shared/execution_snapshot.py` | 3 | AC-05 | `tests/shared/test_execution_snapshot.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes: remove `eventbus_db_path` (comment) | `scripts/shared/mcp_dedup.py` | 3 | AC-05 | `tests/shared/test_mcp_dedup.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes: reject the key as unknown | `scripts/agent/production_config_validator.py` | 3 | AC-05 | `tests/agent/test_production_config_validator.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes: remove the key from `config/agent.toml` | `config/agent.toml` | 3, 6 | AC-05 | `tests/test_production_isolation.py` | Confirmed by repository evidence |
| REQ-005 | Testing Expectations: add a config-load test | `tests/agent/test_production_config_validator.py` | 3 | AC-05 | `uv run pytest tests/agent/test_production_config_validator.py -v` | Explicit in issue |
| REQ-005 | Required Changes: remove the key; snapshot test | `tests/shared/test_execution_snapshot.py` | 3 | AC-05, AC-07 | `uv run pytest tests/shared/test_execution_snapshot.py -v` | Confirmed by repository evidence |
| REQ-005 | Required Changes: remove the key; field filter | `tests/shared/test_mcp_dedup.py` | 3 | AC-05, AC-07 | `uv run pytest tests/shared/test_mcp_dedup.py -v` | Confirmed by repository evidence |
| REQ-006 | Acceptance Criteria: `check_db_separation.py` passes (reaches the removed accessors, new finding) | `tools/check_db_separation.py` | 2 | AC-06 | `uv run python tools/check_db_separation.py` | Confirmed by repository evidence |
| REQ-006 | Acceptance Criteria: `check_db_separation.py` passes | `tests/tools/test_check_db_separation.py` | 2 | AC-06 | `uv run pytest tests/tools/test_check_db_separation.py -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations: update the db, eventbus, deploy tests (wider list found) | `tests/conftest.py` | 3 | AC-07 | `tools/check_conftest_integrity.py` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations | `tests/test_production_isolation.py` | 3 | AC-07 | `uv run pytest tests/test_production_isolation.py -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations | `tests/db/test_create_schema.py` | 3 | AC-07 | `uv run pytest tests/db -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations | `tests/db/test_db_maintenance.py` | 3 | AC-07 | `uv run pytest tests/db -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations | `tests/db/test_db_recovery.py` | 3 | AC-07 | `uv run pytest tests/db -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations | `tests/db/test_recovery_drill.py` | 3 | AC-07 | `uv run pytest tests/db -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations | `tests/db/test_sqlite_helper.py` | 3 | AC-07 | `uv run pytest tests/db -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations: `tests/deploy/test_setup_services_eventbus.py` | `tests/deploy/test_setup_services_eventbus.py` | 3 | AC-07 | `uv run pytest tests/deploy -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations: `tests/eventbus/test_eventbus_startup.py` | `tests/eventbus/test_eventbus_startup.py` | 3 | AC-07 | `uv run pytest tests/eventbus -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations | `tests/agent/test_repl.py` | 3 | AC-07 | `uv run pytest tests/agent -v` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations | `tests/integration/test_session_recovery.py` | 3 | AC-07 | `uv run pytest tests/integration -v` | Confirmed by repository evidence |
| REQ-007 | Evidence: `eventbus_db_path=` in a session-memory test (new finding) | `tests/agent/memory/test_memory_vec_session.py` | 3 | AC-07 | `uv run pytest tests/agent/memory -v` | Derived from confirmed evidence |
| REQ-007 | Evidence: `cfg.eventbus_db_path` assignment (new finding) | `tests/rag/test_fts_sync.py` | 3 | AC-07 | `uv run pytest tests/rag/test_fts_sync.py -v` | Derived from confirmed evidence |
| REQ-008 | Documentation Impact: agent_02 and dependency graphs | `docs/23_agent/agent_02_runtime-architecture.md` | 5 | AC-08 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact: dependency graphs | `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | 5 | AC-08 | `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes: ADR-013 Review Triggers (Context has no such statement) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | 5 | AC-08 | `check_adr_preservation.py` | Explicit in issue |
| REQ-008 | Required Changes: ADR-008 Affected Components, Recovery Policy Matrix | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 5 | AC-08 | `check_adr_preservation.py` | Explicit in issue |
| REQ-008 | Required Changes: `db_01` | `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | 5 | AC-08 | `check_docs_consistency.py --domain db` | Explicit in issue |
| REQ-008 | Required Changes: `db_02` | `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | 5 | AC-08 | `check_docs_consistency.py --domain db` | Explicit in issue |
| REQ-008 | Required Changes: `db_07` | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | 5 | AC-08 | `check_docs_consistency.py --domain db` | Explicit in issue |
| REQ-008 | Evidence: `eventbus_db_path` in the active-database inventory | `docs/41_db/db_08_active_databases.md` | 5 | AC-08 | `check_docs_consistency.py --domain db` | Derived from confirmed evidence |
| REQ-008 | Evidence: `eventbus_db_path` in the deployment document | `docs/90_deployment/deployment_01_deployment.md` | 5 | AC-08 | `check_docs_consistency.py --domain deployment` | Derived from confirmed evidence |
| REQ-008 | Required Changes: `eventbus_06` | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | 5 | AC-08 | `check_docs_consistency.py --domain eventbus` | Explicit in issue |
| REQ-008 | Evidence: retention note names `rotate_eventbus_db()` | `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | 5 | AC-08 | `check_docs_consistency.py --domain agent` | Derived from confirmed evidence |
| REQ-008 | Evidence: creation and rotation sentences name removed functions | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | 5 | AC-08 | `check_docs_consistency.py --domain db` | Derived from confirmed evidence |
| REQ-007 | Amendment 2026-11-10: Import the schema version helper from the EventBus-side tool; found by the consumer re-scan in plan-to-implementation-procedure Step 3a | tests/eventbus/test_eventbus_schema_version.py | Phase 3 | N/A: none cites REQ-007 | uv run pytest tests/eventbus/test_eventbus_schema_version.py -v | Confirmed by repository evidence |
| REQ-005 | Amendment 2026-11-10: Regenerate the generated manifest after eventbus_db_path leaves DbConfig; found by the consumer re-scan in plan-to-implementation-procedure Step 3a | registry/manifests/db_schema_versions.yaml | Phase 3 | N/A: none cites REQ-005 | uv run python tools/generate_reference_table.py --check | Confirmed by repository evidence |
| REQ-008 | Amendment 2026-11-10: Reword the archive sentence that names rotate_eventbus_db(); found by the consumer re-scan in plan-to-implementation-procedure Step 3a | docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md | Phase 5 | N/A: none cites REQ-008 | uv run python tools/check_docs_consistency.py --domain eventbus | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261110-102050 -->