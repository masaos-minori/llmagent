## Goal
- Delete the unused `EventBusClient` module (REQ-001: no `scripts/` importer, fail-open empty-token default).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, Phase 4 of the Plan.
- Not in scope: any other file; a second file needed here is an additional-target discovery.
- Execution order follows the Plan's phases, not `seq`: Phase 1 (documents 03, 04), Phase 2 (05, 18), Phase 3 (the `scripts/db`, `scripts/shared`, validator, config, and test documents, one release unit), Phase 4 (01, 38, 39), Phase 5 (the document rows), Phase 6 verification.

## Assumptions
- Overlap with plans 003, 004, 005, 006 (judged in the Plan's Assumptions): sequencing or different keys; no contradiction on this file.
- The Plan's Step 3a corrections apply (EventBus tool reads `db_path` with its own reader; `eventbus_schema_version` and the DDL text accessor move to `scripts/eventbus/db_tools.py`).

## Design decisions
- Remove only what the Plan names for this file; keep every other behavior unchanged.

## Alternatives considered
N/A: the ownership decision (EventBus-side tooling, maintainer 2026-11-10) is fixed in the Plan's Design section.

## Implementation
### Target file
`scripts/agent/eventbus_client.py`

### Procedure
1. Re-run `rg -n "agent\.eventbus_client|from agent import eventbus_client|eventbus_client" scripts` and confirm there is no importer (stop and report if a production caller exists).
2. Delete `scripts/agent/eventbus_client.py` (and its companion test, below).
3. Run `uv run python tools/generate_reference_table.py --manifests` for the agent manifests so documents 38 and 39 refresh; `scripts/agent/eventbus_subscriber.py` and `scripts/agent/eventbus_topic_admin_client.py` stay (Plan UNK-02).

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- The module defines `EventBusClientConfig` (`publisher_token: str = ""`) and `EventBusClient`; `eventbus_subscriber.py` and `eventbus_topic_admin_client.py` import neither (checked in Step 3a: their imports are `httpx`, `orjson`, stdlib).
- Matches of `eventbus_client` in `tests/eventbus/` and `tests/deploy/` are the helper `make_eventbus_client`, not this module.

### Companion test files
- `tests/agent/test_eventbus_client.py`
  - Procedure: Delete the file (it tests only the removed module).
  - Validation: `uv run pytest tests/agent -v` passes and `rg -n "agent\.eventbus_client" tests` is empty.

## Compatibility considerations
- See Details; the removal is intentional and has no shim (`tools/check_compat_shims.py`).

## Security considerations
- No authentication or authorization behavior changes; the EventBus path and schema checks stay fail-closed.

## Rollback considerations
- Revert the phase's commit; Phases 1-2 keep the Agent-side path available until Phase 3 lands, so a revert of Phase 3 restores the old behavior.

## Validation plan
- `rg -n "EventBusClient|EventBusClientConfig|agent\.eventbus_client" scripts tests` returns no match after the companion test is deleted.
- `uv run pytest tests/agent -v`.
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- The module and its test are gone and nothing imports them.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `scripts/agent/eventbus_client.py` and `tests/agent/test_eventbus_client.py` after the importer check | Pending | — | — | |
| 2 | Run `uv run pytest tests/agent -v` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261109-112538_adrrev002_agent-eventbus-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-102050
- **Related target files**: `scripts/agent/eventbus_client.py`, `tests/agent/test_eventbus_client.py`
