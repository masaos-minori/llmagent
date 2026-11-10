# Remove all Agent-side EventBus coupling (unused client and Agent-side eventbus.sqlite handling)

## Priority
High

## Summary
Make "the Agent does not use the EventBus" true in code, configuration, and documentation: delete the unused `EventBusClient`, remove the Agent-side creation and configuration of `eventbus.sqlite`, and leave the EventBus service as the only creator and owner of its database path.

## Background
- Source: `memo-issue.md` items H-02 and H-04, re-checked against current source on 2026-11-09.
- `Explicit in code`: `scripts/agent/eventbus_client.py` defines `EventBusClientConfig` and `EventBusClient`. Under `scripts/` nothing imports it; only `tests/agent/test_eventbus_client.py` (and EventBus test helpers that reference the name) use it. `publisher_token` defaults to an empty string and the client builds a `Bearer` header from it. The client stamps `published_at` with `datetime.now(UTC).isoformat()` (a `+00:00` suffix). `Needs confirmation`: the suffix the EventBus itself writes (the memo says `Z`).
- `Explicit in code`: `DbTarget.EVENTBUS` exists in `scripts/db/helper.py`; `eventbus_db_path` is read in `scripts/db/config.py`, `scripts/db/rotation.py`, `scripts/db/recovery_drill.py`, `scripts/db/helper.py`, `scripts/agent/production_config_validator.py`, `scripts/shared/execution_snapshot.py`, `scripts/shared/mcp_dedup.py`, and `config/agent.toml`.
- `Explicit in code`: the EventBus service creates its own schema from `scripts/eventbus/schema.sql`. `Needs confirmation`: whether the Agent's `create_schema()` EventBus branch (`scripts/db/create_schema.py`, `build_eventbus_schema_sql()` in `scripts/db/schema_sql.py`) is still reached by any production start path (the memo asserts it is only reachable through the Agent).
- `Documentation only`: `eventbus_01_system-overview.md` states the Agent runtime neither publishes to nor subscribes from the EventBus; ADR-013 Review Triggers assume "the Agent is the sole caller"; ADR-008 makes the EventBus service the owner of eventbus.sqlite.
- Recently archived related work: `rmebmig_remove-the-eventbus.sqlite-schema-migrations`, `compat002`/`rmoffimp` (legacy offset import), `ebdocwording_align-eventbus-facade-wording` under `issues/done/`. Re-verify this issue against current source; some Agent-side EventBus wiring may already have changed.

## Problem
- Dead production code (client used only by tests) with a fail-open default (an empty bearer token) is maintained, reviewed, and documented.
- The EventBus database path and its creation are reachable from the Agent side, so two components can create or operate on one database, and nothing checks that the Agent's configured path equals the EventBus service's own configured path (ADR-002 requires each process to read only its own configuration).
- The ADR-013 caller model ("the Agent is the sole caller") is contradicted by the system overview.

## Reason for Change
- Dead code matches the governance definition of an Unused Feature. A latent empty-token default conflicts with the ADR-004 principle that an empty token is rejected, and would be exposed the moment someone wires the client.
- A mismatch between the two configured paths silently creates two databases, and rotation or backup can then act on the wrong file. Timing: no external deadline; it unblocks the schema-validation and ADR-008 alignment issues in this batch.

## Implementation Intent
- The EventBus service owns eventbus.sqlite: one creator, one configured path, defined in the EventBus configuration only.
- Remove what only the unused client or the Agent-side EventBus path used. Preserve rotation and backup capability for eventbus.sqlite by resolving the path from the EventBus configuration (or by moving those operations into the EventBus service tooling).
- Keep the change at the responsibility level: do not redesign the EventBus or its schema here.

## Target Files or Areas
- `scripts/agent/eventbus_client.py`, `tests/agent/test_eventbus_client.py`, and any config keys, dataclasses, or wiring used only by the client
- `scripts/db/helper.py`, `scripts/db/create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/config.py`, `scripts/db/rotation.py`, `scripts/db/recovery_drill.py`
- `scripts/agent/production_config_validator.py`, `scripts/shared/execution_snapshot.py`, `scripts/shared/mcp_dedup.py`
- `config/agent.toml`, `config/eventbus.toml`
- `tests/db/`, `tests/eventbus/`, `tests/deploy/test_setup_services_eventbus.py`
- ADR-013 (`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`), ADR-008 (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`), `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, dependency graphs

## Required Changes
- Delete `scripts/agent/eventbus_client.py`, its tests, and any config keys, dataclasses, and wiring used only by it (for example the publish URL, publisher token, and timeouts).
- Remove `DbTarget.EVENTBUS`, the EventBus branch of `create_schema()`, and `build_eventbus_schema_sql()` from `scripts/db/`, after confirming they are not used by an EventBus service start path.
- Remove `eventbus_db_path` from `config/agent.toml`, the Agent DB config dataclass, and its validators, so the key is rejected as unknown.
- Make rotation, backup, and recovery of eventbus.sqlite resolve the path from the EventBus configuration only, or move these operations into EventBus service tooling.
- Update ADR-013 (Context, Review Triggers) to describe the actual caller model, or reference the outcome of the EventBus decision issue in this batch.
- Update ADR-008 (Affected Components, Recovery Policy Matrix), `db_01`, `db_02`, `db_07`, `eventbus_06`, and the dependency graphs.

## Constraints
- Preserve the ability to rotate and recover eventbus.sqlite; do not drop operations that operators rely on without a replacement.
- Per ADR-002, each process reads only its own configuration file.
- The deploy path (`deploy/deploy.sh`, `rules/env.md` Architecture) must remain valid if a `config/*.toml` file changes.
- Run the impact-radius check from `rules/toolchain.md` before removing widely referenced symbols (`rg -l '\bDbTarget\b|eventbus_db_path' tests/ scripts/`).

## Acceptance Criteria
- `rg -n "eventbus_client|EventBusClient|DbTarget.EVENTBUS|eventbus_db_path|build_eventbus_schema_sql" scripts/ tests/ config/ docs/` returns no match for the Agent-side symbols (EventBus-owned references to its own path key under a different name are allowed and must be named in the PR).
- An `agent.toml` containing `eventbus_db_path` fails config load.
- Rotation and backup tests resolve the eventbus.sqlite path through the EventBus configuration.
- `uv run python tools/check_db_separation.py` passes.

## Testing Expectations
- Update `tests/db/test_db_recovery.py`, `tests/db/test_db_maintenance.py`, `tests/eventbus/test_eventbus_startup.py`, and `tests/deploy/test_setup_services_eventbus.py` for the new path resolution.
- Add a config-load test that rejects the removed key.
- `uv run pytest tests/db tests/eventbus tests/agent -v`, then the standard validation sequence in `rules/toolchain.md` (ruff, mypy, lint-imports, bandit, full pytest).
- Documentation checks: `check_docs_consistency.py --domain db` and `--domain eventbus`, `check_adr_authority.py`, `check_docs_content_policy.py --strict`.

## Documentation Impact
- Update ADR-013 and ADR-008 to describe the actual ownership and caller model (intent, boundaries, failure behavior); update the DB and EventBus reference documents and the dependency graphs.
- Record any remaining unconfirmed caller as a Needs Confirmation item through `governance_03`, not as inline prose.

## Out of Scope
- Designing the future EventBus integration (the EventBus is kept; the maintainer plans to integrate it later). A future publisher or consumer client is designed then, with a fail-closed token default.
- Fingerprint-based schema validation of eventbus.sqlite (schema validation issue in this batch).
- Changes to EventBus authorization or roles.

## Dependencies
- Depends on: none.
- Blocks: `issues/20261109-112922_adrrev009_adr008-recovery-align.md` (ADR-008 alignment) and `issues/20261109-112952_adrrev010_eventbus-authz-harden.md` (EventBus authorization hardening); both restate ownership facts established here.
- Related, recently archived: `rmebmig_remove-the-eventbus.sqlite-schema-migrations` and `ebdocwording_align-eventbus-facade-wording` under `issues/done/`.

## Unresolved Questions
- `Needs confirmation`: is the EventBus branch of `create_schema()` reached by any production or deploy path (for example `deploy/` setup scripts or `scripts/eventbus/schema.py`)? If yes, move the logic to the EventBus side instead of deleting it.
- `Needs confirmation`: which component currently performs rotation and backup of eventbus.sqlite in production, and under which configuration file.
- `Explicit in code`: the EventBus writes timestamps with a `Z` suffix (`scripts/eventbus/json_utils.py`, `scripts/eventbus/dlq.py`), while the client writes `+00:00`; removing the client removes the divergent producer.
- Assumption to confirm with the maintainer: because the EventBus is kept for planned future integration, deleting the unused client now and designing a new fail-closed client at integration time is preferred over keeping the current client (its empty-token default is fail-open).

## AI Implementation Instruction
- Verify each caller with `rg` before deleting a symbol; stop and report if a production caller exists.
- Do not redesign the EventBus, its schema, or its authorization.
- Do not edit config files outside the keys named here; follow `rules/env.md` for `deploy/deploy.sh` effects.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112538
- **Related target files**: `scripts/agent/eventbus_client.py`, `scripts/db/helper.py`, `scripts/db/create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/config.py`, `scripts/db/rotation.py`, `scripts/db/recovery_drill.py`, `scripts/agent/production_config_validator.py`, `scripts/shared/execution_snapshot.py`, `scripts/shared/mcp_dedup.py`, `config/agent.toml`, `config/eventbus.toml`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/41_db/`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
