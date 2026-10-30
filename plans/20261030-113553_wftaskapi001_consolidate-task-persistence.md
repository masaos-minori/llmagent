# Plan: Consolidate workflow task persistence and rename the random task key

**Task Classification:** Path B (more than 3 files; changes the `TaskRecord` model and the `StateStore` public surface; renames a `workflow.sqlite` column). Path B analysis applied (`skills/issue-to-plan/workflow-path-b.md`).

## Goal
- Make one module own workflow task persistence (row mapping, lookup, status update), delete the task lookup APIs that have no production caller, and rename `tasks.idempotency_key` to a name that states its real guarantee (a unique opaque value, not request deduplication), with the column rename delivered through the forward-only migration mechanism.

## Priority
Low

## Scope
- **In-Scope**: choose `agent/workflow/task_ops.py` as the canonical task-persistence implementation and make `StateStore` task methods thin delegates; delete duplicated SQL and the duplicate `_row_to_task`; delete `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, and `list_tasks` (both layers) after a zero-caller re-check; record the decision that task creation does not deduplicate caller requests and rename the key to `task_nonce` (model, DDL, schema version, migration step, tests); update the two documents that describe the key; test duplicate-creation behavior.
- **Out-of-Scope**: task status vocabulary and transitions, attempt numbering, event ledger, recovery (`issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`); attempt-operation duplication in `StateStore` (`start_attempt`, `finish_attempt`, `count_attempts`); the EventBus `idempotency_key`; the MCP `X-Idempotency-Key`; dropping the column.
- **Dependencies**: (1) Phase 3 (the rename) depends on `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3 (workflow domain wiring), because `scripts/db/create_schema.py` and `scripts/agent/services/workflow_schema.py` refuse a database whose schema version differs; Phases 1, 2, and 4 do not depend on it. (2) This Plan blocks, by recommended order, `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` (it takes the canonical-module decision from this Plan). (3) `scripts/db/schema_sql.py`, `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/db/test_create_schema.py`, and `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` are also targets of other Frozen Plans (`plans/20261029-214108_dbmig001_forward-only-db-migrations.md`, `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`, `plans/20261030-013620_ragcorpus001_rag-corpus-identity.md`); `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` also refers to `tasks.idempotency_key` by name (its REQ-010), so it must adopt `task_nonce` if it lands after this Plan's Phase 3; see Assumptions for the judgments.

## Background
`StateStore` (`scripts/agent/workflow/state_store.py`) re-implements `update_task_status`, `_row_to_task`, `get_task_by_id`, `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, and `list_tasks` with the same SQL as the functions in `scripts/agent/workflow/task_ops.py`; only `create_task` is delegated (checked in Step 3). `task_ops.create_task()` assigns `idempotency_key = str(uuid.uuid4())` per row (`task_ops.py:30`), so the column never deduplicates a caller request; its docstring (`task_ops.py:21-28`) and two docs already say so. The four lookup APIs and their `StateStore` copies have no caller under `scripts/`; only tests call the key lookup (`tests/agent/workflow/test_workflow_engine.py:94,125,142,296`, `test_workflow_state_store.py:88-131`). Production uses `task_ops.create_task` and `task_ops.get_task_by_id` (`scripts/agent/workflow_engine_adapter.py:38`) and `StateStore.update_task_status` (`scripts/agent/workflow/workflow_engine.py:121-132`); `scripts/agent/session_persister.py:88` uses only diagnostic count queries. Closed work removed the derived key (`issues/done/20261021-093421_turn001_*`, `issues/done/20261024-105743_workflow001_*`) but not the duplication or the name.

## Problem
A task schema, validation, or transition change must be written in two places, which can diverge silently; the name `idempotency_key` implies deduplication that does not exist; four lookup APIs and their tests have no production caller.

## Reason for Change
The state-machine issue adds transition validation to task updates; writing it against two copies would duplicate it. Independent of that, the risk is maintenance, hence Low priority. Landing consolidation first lets the later work change one module.

## Implementation Intent
- `task_ops` module functions are canonical because every production call site except the engine's status writes already uses them; `StateStore` keeps only thin delegates for methods that a production or test caller needs.
- No caller needs caller-request deduplication, so the key is renamed to a nonce; a caller-stable key is not added.
- The rename ships as one unit: model field, DDL, `WORKFLOW_SCHEMA_VERSION`, migration step, tests, docs. It does not land before the dbmig001 workflow registry exists.
- Preserve `create_task`, `get_task_by_id`, and `update_task_status` behavior as seen by the adapter and engine.

## Requirements
- `REQ-001`: `agent/workflow/task_ops.py` is the single implementation of task row mapping, lookup, and status update; `StateStore` task methods only delegate to it; the task aggregates `get_task_count` and `get_workflow_count` (`state_store.py:178-190`) move to `task_ops` with `StateStore` delegates kept for `session_persister`; the cross-table diagnostics `get_execute_attempt_count` and `get_artifact_uris` (task subselects at `state_store.py:201,209`) stay in `StateStore` as the only task SQL allowed there.
- `REQ-002`: Delete `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, and `list_tasks` from `task_ops.py` and `StateStore`, and the tests that exercise only them, after a zero-caller `rg` re-check (`rules/coding.md` Deprecation policy); stop and report if a caller outside `tests/` appears.
- `REQ-003`: Rename `tasks.idempotency_key` to `task_nonce` in `TaskRecord`, `create_task`, row mapping, the workflow DDL, and every test that references it; the contract (unique opaque UUID4 per row, never caller-derived) is unchanged and documented.
- `REQ-004`: Deliver the rename through a registered `workflow.sqlite` migration step (`ALTER TABLE tasks RENAME COLUMN idempotency_key TO task_nonce`), bump `WORKFLOW_SCHEMA_VERSION` from `1.1.0`, and prove it preserves existing rows; the step lands only after the dbmig001 workflow registry exists.
- `REQ-005`: Update `docs/41_db/db_02_architecture_and_schema-schema-reference.md` (section 7 key paragraph) and `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (StateStore scope paragraph and the "fresh, unique task keys" bullet) to the new name and contract, stating the difference among task identity, task-request deduplication, and stage-event idempotency, without restating code.
- `REQ-006`: Duplicate task-creation behavior is explicitly defined and tested: two `create_task` calls with identical arguments create two rows with distinct `task_id` and `task_nonce`.
- `REQ-007`: Before removing any API, run and record a repository-wide caller search for each removed name and for `idempotency_key` on tasks (`scripts/`, `tests/`, `tools/`, `docs/`, `deploy/`).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on 2026-10-30: every row exists, requires modification, cites checkable evidence, and links to a Requirement or Acceptance criterion; all paths confirmed present on branch `docs/issues-workflow-persistence`).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/task_ops.py` | Canonical task persistence; rename key; drop zero-caller lookups | Becomes the only owner of task SQL; `idempotency_key` literal at `:30,38,47,59,84`; lookup at `:99-101`, `:107-132` | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3 | `task_ops.py:30` uuid4 key; `:99` `get_task_by_idempotency_key`; `:107,116,127` session/latest/list (checked in Step 3) | `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| `scripts/agent/workflow/state_store.py` | Delegate task methods; delete duplicates | Duplicate SQL at `:49-122` (`update_task_status`, `_row_to_task`, `get_task_by_*`, `get_latest_task`, `list_tasks`); only `create_task` delegates (`:18,52`) | REQ-001, REQ-002 / AC-1, AC-2 | `state_store.py:49-122,178-190`; import `:18` (checked in Step 3) | `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_engine.py` | Verified |
| `scripts/agent/workflow/models.py` | Rename `TaskRecord.idempotency_key` | Field named for a guarantee it does not give | REQ-003 / AC-3 | `models.py:21` `idempotency_key: str` (checked in Step 3) | `tests/agent/workflow/test_workflow_models.py` | Verified |
| `scripts/db/schema_sql.py` | Rename DDL column; bump schema version | Workflow DDL `:179` and `WORKFLOW_SCHEMA_VERSION = "1.1.0"` at `:25` | REQ-003, REQ-004 / AC-3, AC-4 | `schema_sql.py:25,179`; version guard `scripts/db/create_schema.py:54-77` (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `tests/agent/workflow/test_workflow_state_store.py` | Remove tests of deleted APIs; rename key assertions; add duplicate-creation test | Key assertions `:75-84,120-124`; lookup tests `:86-93,105-131`; raw INSERTs `:105,264,416,466,509` | REQ-002, REQ-003, REQ-006 / AC-2, AC-3, AC-5 | `rg idempotency_key tests/agent/workflow` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_engine.py` | Replace key lookups with `get_task_by_id` | Import `:18`; uses `:94,125,142,296` | REQ-002 / AC-2 | `test_workflow_engine.py:18,94,125,142,296` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_stage_persistence.py` | Update raw task INSERT | Raw `INSERT INTO tasks (... idempotency_key ...)` at `:29` | REQ-003 / AC-3 | `test_workflow_stage_persistence.py:29` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_models.py` | Rename `TaskRecord` constructor argument | `idempotency_key="s1:3"` at `:25` | REQ-003 / AC-3 | `test_workflow_models.py:25` (checked in Step 3) | itself | Verified |
| `tests/db/test_create_schema.py` | Update DDL copy and uniqueness test; add migration test | DDL copy `:359`; `test_tasks_idempotency_key_unique` `:495` | REQ-003, REQ-004 / AC-3, AC-4 | `test_create_schema.py:359,495` (checked in Step 3) | itself | Verified |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Task-key contract | Section 7 key paragraph describes the UUID4 `idempotency_key` | REQ-005 / AC-6 | `db_02_...md:48` (checked in Step 3) | docs checkers (Validation plan) | Verified |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Task-key contract and StateStore scope | Scope paragraph `:71` and "fresh, unique task keys" bullet `:86` | REQ-005 / AC-6 | `agent_04_03_...md:71,86` (checked in Step 3) | docs checkers (Validation plan) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. No directory, glob, component name, file group, or vague phrase appears as a row.
- A test, configuration, schema, migration, deployment, or documentation file is its own row when it requires modification.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before the section is `Frozen`.

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Imports `create_task`, `get_task_by_id` from `task_ops` (`:38`); confirms no change is needed under the chosen canonical module | REQ-001 |
| `scripts/agent/workflow/workflow_engine.py` | Calls `StateStore.update_task_status` (`:121-132`); the delegate must keep this call working | REQ-001 |
| `scripts/agent/session_persister.py` | Uses `StateStore` diagnostic counts only (`:88-105`); confirms it is unaffected | REQ-001 |
| `scripts/db/create_schema.py` | Refuses a database with a different schema version (`:54-77`) | REQ-004 |
| `scripts/agent/services/workflow_schema.py` | Startup version comparison (`:114`) | REQ-004 |
| `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` | Defines the workflow migration registry and ledger this Plan's Phase 3 registers into | REQ-004 |
| `tools/check_db_separation.py` | Table-ownership inventory (names `tasks` at `:70`); run after the DDL change | REQ-004 |
| `deploy/init_db.sh` | Checks required workflow tables by name only; unaffected by a column rename | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): `rg "FROM tasks|UPDATE tasks|INSERT INTO tasks" scripts/agent/workflow` matches only `task_ops.py` and the two documented cross-table subselects in `state_store.py` (`get_execute_attempt_count`, `get_artifact_uris`); `StateStore` has no task row mapping, lookup, update, or count SQL.
- AC-2 (REQ-002, REQ-007): `rg "get_task_by_idempotency_key|get_task_by_session|get_latest_task|list_tasks" scripts tests tools docs deploy` finds no definition or caller; the caller-search record is attached to the change.
- AC-3 (REQ-003): `rg idempotency_key scripts/agent/workflow scripts/db tests/agent/workflow tests/db` finds no task-key reference; `TaskRecord` exposes `task_nonce`.
- AC-4 (REQ-004): a database created at the previous schema version with existing task rows opens after the migration with all rows preserved and `task_nonce` populated from the old values; `WORKFLOW_SCHEMA_VERSION` differs from `1.1.0`; a downgrade or unregistered path is still refused.
- AC-5 (REQ-006): a test creates two tasks with identical arguments and asserts distinct `task_id` and `task_nonce`.
- AC-6 (REQ-005): the two documents describe the nonce contract and the identity / request-deduplication / stage-event distinction, and pass the docs checkers.
- AC-7: existing adapter and engine tests pass with renames only.

## Tests
- `REQ-001`, `REQ-002`: behavioral tests through the canonical API (create, get, update) and through the `StateStore` delegates still used (`tests/agent/workflow/test_workflow_state_store.py`, `test_workflow_engine.py`).
- `REQ-003`, `REQ-006`: rename-aware model, DDL, and raw-INSERT tests; duplicate-creation test.
- `REQ-004`: migration test on a database containing existing task rows, plus a refused-downgrade test (`tests/db/test_create_schema.py`, and the dbmig001 harness).
- `REQ-005`: documentation checkers.

## Documentation Impact
Yes. `REQ-005` updates `docs/41_db/db_02_architecture_and_schema-schema-reference.md` and `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (located through `docs/00_index.md` "Document References by Task"): contract and boundaries only. `docs/23_agent/agent_13_reference-api-generated.md` is not a target (it mentions `idempotency_key` only as an `audit_tool_exec` parameter and lists no task API; `generate_reference_table.py --check` reported `No drift found` on 2026-10-30). ADR-001 INV-08 concerns the stage-event key and is unaffected.

## Assumptions
- `task_ops` is the canonical owner (UNK-01 records the owner's right to choose `StateStore` instead; the delegating design is the same either way for callers).
- No caller needs caller-request deduplication; none exists in `scripts/` (checked in Step 3).
- Tests that call `get_task_by_idempotency_key` verify only the lookup and may be removed with it.
- Sequencing on `scripts/db/schema_sql.py` (Step 8b: shared with the dbmig001 and toolexec001 plans): this Plan's rename step registers through the dbmig001 workflow registry and lands after dbmig001 Phase 3; toolexec001 Phase 4 also registers through it. The three designs touch different parts of the file (ledger DDL, new tables, one column), so they are compatible if landed in registry order; whichever lands first, the others rebase.
- Step 8b overlap judgments (`tools/check_plan_target_overlaps.py`, 2026-10-30): `state_store.py` and `test_workflow_engine.py` with toolexec001: compatible (toolexec001 adds tool-call state helpers and pending-detection tests; this Plan changes only task CRUD delegation and key lookups). `agent_04_03_...md` line 71 with toolexec001: sequencing dependency (both edit the same paragraph; toolexec001's REQ-010 preserves task-key semantics, which this Plan also preserves, but its text names `idempotency_key`; the later change reconciles the name). `schema_sql.py` with ragcorpus001: compatible (it adds a `rag_corpus_meta` DDL; this Plan changes one `tasks` column). `tests/db/test_create_schema.py` with dbmig001: compatible (additive tests).
- Schema version numbering (second-pass verification, 2026-10-30): this Plan, wfrecovery001, wflease001, wftaskapi001, and toolexec001 each bump `WORKFLOW_SCHEMA_VERSION` from `1.1.0`. Version numbers are not fixed in the Plans; they are assigned in landing order when the migration steps are registered, and each step's source version equals the previous step's target version (the dbmig001 registry records source and target versions per migration). Two Plans must not target the same version.
- Verification record (second pass, 2026-10-30): no Implementation Target Files row changed on `origin/master` since the merge base; every `path:line` citation lies within its file; SQLite 3.46.1 `RENAME COLUMN` keeps the `UNIQUE` constraint and the unique index (tested), so Phase 3 needs no backfill; no caller of the four removable lookup APIs exists in `tools/`, `deploy/`, or `config/`.
- The migration registration module is defined by the dbmig001 plan (`scripts/db/migrations_workflow.py`, not yet present); it is not listed as a target here because it does not exist yet. When it lands, `plan-to-implementation-procedure` Step 2 revalidation amends this Plan with that row (UNK-04).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner's preferred canonical module (`task_ops` vs `StateStore`) | No recorded owner decision; production call sites favor `task_ops` | Default to `task_ops`; owner may reverse before Phase 2 | False |
| UNK-02 | Whether any external or planned caller needs caller-request deduplication | No such caller found in `scripts/`, `tools/`, `deploy/` | Default: rename path (REQ-003); revisit only if a caller is named | False |
| UNK-03 | Final column name (`task_nonce`) and whether the redundant second unique column should be dropped instead | `DROP COLUMN` is unsupported for a `UNIQUE` column in SQLite 3.46.1, so a drop needs a table rebuild; owner preference unknown | Default: `RENAME COLUMN`; a drop is a later, separate change | False |
| UNK-04 | Exact registration point and API of the dbmig001 workflow migration registry | `scripts/db/migrations_workflow.py` is planned in the dbmig001 plan but absent from the repository | Open dependency: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3; Phase 3 of this Plan starts only after it; revalidate target files at procedure-generation time | False |
| UNK-05 | Whether the retained production `workflow.sqlite` holds rows the migration must preserve | Production database is not inspected during planning (`rules/ai-execution.md` Repository Tool Usage item 7) | Migration test uses fixture rows; the dbmig001 pre-migration backup gate covers production | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/task_ops.py` | Modify | Medium: adapter imports `create_task`, `get_task_by_id`; `TaskRecord` consumers | 1 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/state_store.py` | Modify | Medium: `StateStore` has 84 references in 7 test files; engine and `session_persister` use it | 2 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/models.py` | Modify | Medium: `TaskRecord` used by engine, adapter, `__init__` export | 1 | High (single contributor) | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | Modify | High: startup version guards, sibling plans | 12 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | Low | 4 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | Low | 2 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_stage_persistence.py` | Modify | Low | 2 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_models.py` | Modify | Low | 0 | High (single contributor) | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | Modify | Low | 15 | High (single contributor) | not applicable (rsynced) |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Modify | Low | 21 | High (single contributor) | not applicable (rsynced) |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Modify | Low | 14 | High (single contributor) | not applicable (rsynced) |

## Design
- **Canonical owner.** Alternatives: (a) `task_ops` functions canonical, `StateStore` delegates; (b) a `StateStore`-owned repository, module functions removed. Chosen (a): production already imports `task_ops` directly (`workflow_engine_adapter.py:38`), `StateStore.create_task` already delegates, and (b) would change more call sites for no behavior gain. Compatibility: `StateStore` method names used by the engine and tests remain.
- **Key contract.** Alternatives: (a) accept a caller-stable key and deduplicate creation; (b) rename to a nonce; (c) drop the column. Chosen (b): no caller exists for (a), and (c) needs a table rebuild under SQLite 3.46.1. The renamed value stays a UUID4 and `UNIQUE NOT NULL`.
- **Migration.** `RENAME COLUMN` preserves rows and the unique index; no backfill is needed. The step is registered in the dbmig001 workflow registry with its pre-migration backup gate; the version bump and the DDL change ship in the same release as the code rename, because `create_schema.py:54-77` and `workflow_schema.py:114` reject a version mismatch.
- **Layering.** Import contract unchanged: `agent.workflow.state_store` imports `agent.workflow.task_ops`, not the reverse (lint-imports baseline: 6 contracts kept, 0 broken, 2026-10-30).

## Implementation steps
1. **Phase 1: Caller search and record**
   - [ ] Run the caller search for each name to be removed and for task `idempotency_key` over `scripts/`, `tests/`, `tools/`, `docs/`, `deploy/`; stop and report if a non-test caller appears (REQ-007; no file modified).
2. **Phase 2: Consolidate task persistence (independently revertable)**
   - [ ] Make `StateStore` task methods delegate to `task_ops` and delete the duplicated SQL and `_row_to_task` (REQ-001; `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/task_ops.py`).
   - [ ] Move the task aggregate counts to `task_ops` behind `StateStore` delegates (REQ-001; `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`).
   - [ ] Delete the four zero-caller lookup APIs in both layers (REQ-002; `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`).
   - [ ] Update tests: remove lookup-only tests, switch key lookups to `get_task_by_id` (REQ-002; `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_engine.py`).
3. **Phase 3: Rename the task key with its migration (starts after dbmig001 Phase 3; one release unit)**
   - [ ] Rename the field, DDL column, `create_task` and row-mapping use, and bump `WORKFLOW_SCHEMA_VERSION` (REQ-003, REQ-004; `scripts/agent/workflow/models.py`, `scripts/agent/workflow/task_ops.py`, `scripts/db/schema_sql.py`).
   - [ ] Register the `RENAME COLUMN` migration step in the dbmig001 workflow registry (REQ-004; registration module added to this Plan by amendment, UNK-04).
   - [ ] Update tests: model, raw INSERTs, DDL copy, uniqueness test, migration test, duplicate-creation test (REQ-003, REQ-004, REQ-006; `tests/agent/workflow/test_workflow_models.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/db/test_create_schema.py`).
4. **Phase 4: Documentation**
   - [ ] Update the key paragraph and StateStore scope text (REQ-005; `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`); run the docs checkers.
5. **Phase 5: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). Prerequisite: the dbmig001 migration step for the retained `/opt/llm/db/workflow.sqlite` has run with its backup gate; verify with the schema check and `uv run python tools/check_db_separation.py` (REQ-004; `scripts/db/schema_sql.py`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/task_ops.py`, `state_store.py` | Unit: canonical API and delegates | `uv run pytest tests/agent/workflow/ -v` | All pass; no task SQL in `state_store.py` |
| Orchestrator integration | Integration | `uv run pytest tests/agent/test_orchestrator.py -v` | Unchanged results |
| `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py` | Unit + migration with existing rows | `uv run pytest tests/db/ -v` | Rows preserved; downgrade refused |
| Schema ownership | Static | `uv run python tools/check_db_separation.py` | Pass |
| Source quality | Static | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean; lint-imports 6 kept |
| Changed-line coverage | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | at least 90% (baseline recorded without threshold: no covered lines in the current diff, which contains only documents) |
| Generated reference | Static | `uv run python tools/generate_reference_table.py --check` | `No drift found` |
| `docs/` changes | Static | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py` | Pass |

Baselines recorded 2026-10-30: radon cc on the target modules shows no grade C or worse in `task_ops.py`, `state_store.py`, `models.py`; `scripts/db/schema_sql.py` has none above B in the scanned set (`radon cc -n C` output lists only `workflow_loader.py`, `workflow_engine_adapter.py`, `workflow_schema.py`); vulture reports 16 findings, none in these files; bandit reports 0 medium or high findings repository-wide (51 low). Operational check: production database locks (`fuser`) not run; planning does not touch `/opt/llm/` (`rules/ai-execution.md` Repository Tool Usage item 7); `pip-audit` not applicable (no dependency change).

## Risks
- **Risk**: `StateStore` has 84 references in 7 test files, and `schema_sql.py` and `test_create_schema.py` are high-churn (12 and 15 commits in 30 days), so the rename touches widely used names (`rules/toolchain.md` Impact-radius check: above the 20-reference rule of thumb) → **Mitigation**: Phase 2 keeps `StateStore` method names; Phase 3 is gated and confined to the key; the blast radius is budgeted in the step list.
- **Risk**: bumping the schema version without a registered migration makes a retained `workflow.sqlite` fail startup → **Mitigation**: Phase 3 starts only after dbmig001 Phase 3 and ships DDL, version, and migration together; AC-4 tests it.
- **Risk**: the dbmig001 registry API differs from this Plan's assumption (UNK-04) → **Mitigation**: revalidate and amend target files at procedure generation; no registry code is assumed here.
- **Risk**: a removed API has an unseen caller (dynamic use, scripts outside `scripts/`) → **Mitigation**: Phase 1 caller search across `tools/`, `deploy/`, `docs/`, and a stop condition before deletion.
- **Risk**: another plan's migration step claims the same target version → **Mitigation**: version numbers assigned in landing order (Assumptions).
- **Risk**: single-contributor files (bus factor High) → **Mitigation**: small, independently revertable phases.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Caller search and record | Pending | — | — | |
| 2 | Phase 2: Consolidate task persistence | Pending | — | — | |
| 3 | Phase 3: Rename the task key with its migration | Pending | — | — | Starts after dbmig001 Phase 3 |
| 4 | Phase 4: Documentation | Pending | — | — | |
| 5 | Phase 5: Deployment & Verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-113553
- **Related target files**: `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/models.py`, `scripts/db/schema_sql.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/agent/workflow/test_workflow_models.py`, `tests/db/test_create_schema.py`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; Required Changes 2 | `scripts/agent/workflow/task_ops.py` | Phase 2 | AC-1 | `tests/agent/workflow/` | Confirmed by repository evidence |
| REQ-001 | Implementation Intent; Required Changes 2 | `scripts/agent/workflow/state_store.py` | Phase 2 | AC-1 | `tests/agent/workflow/` | Confirmed by repository evidence |
| REQ-002 | Required Changes 4; Background (callers) | `scripts/agent/workflow/task_ops.py` | Phase 1, Phase 2 | AC-2 | caller search; `tests/agent/workflow/` | Confirmed by repository evidence |
| REQ-002 | Required Changes 4 | `scripts/agent/workflow/state_store.py` | Phase 2 | AC-2 | caller search | Confirmed by repository evidence |
| REQ-002 | Required Changes 4 | `tests/agent/workflow/test_workflow_state_store.py` | Phase 2 | AC-2 | `uv run pytest tests/agent/workflow/` | Confirmed by repository evidence |
| REQ-002 | Required Changes 4 | `tests/agent/workflow/test_workflow_engine.py` | Phase 2 | AC-2 | `uv run pytest tests/agent/workflow/` | Confirmed by repository evidence |
| REQ-003 | Required Changes 3; Summary | `scripts/agent/workflow/models.py` | Phase 3 | AC-3 | `tests/agent/workflow/test_workflow_models.py` | Derived from confirmed evidence |
| REQ-003 | Required Changes 3 | `scripts/agent/workflow/task_ops.py` | Phase 3 | AC-3 | `uv run pytest tests/agent/workflow/` | Derived from confirmed evidence |
| REQ-003 | Required Changes 3 | `scripts/db/schema_sql.py` | Phase 3 | AC-3, AC-4 | `uv run pytest tests/db/` | Derived from confirmed evidence |
| REQ-003 | Background (second finding) | `tests/agent/workflow/test_workflow_stage_persistence.py` | Phase 3 | AC-3 | `uv run pytest tests/agent/workflow/` | Confirmed by repository evidence |
| REQ-003 | Background (second finding) | `tests/agent/workflow/test_workflow_models.py` | Phase 3 | AC-3 | `uv run pytest tests/agent/workflow/` | Confirmed by repository evidence |
| REQ-003 | Background (second finding) | `tests/db/test_create_schema.py` | Phase 3 | AC-3 | `uv run pytest tests/db/` | Confirmed by repository evidence |
| REQ-004 | Constraints (migration); Dependencies | `scripts/db/schema_sql.py` | Phase 3, Phase 5 | AC-4 | migration test; `check_db_separation.py` | Derived from confirmed evidence |
| REQ-004 | Testing Expectations | `tests/db/test_create_schema.py` | Phase 3 | AC-4 | `uv run pytest tests/db/` | Derived from confirmed evidence |
| REQ-005 | Documentation Impact | `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Phase 4 | AC-6 | docs checkers | Confirmed by repository evidence |
| REQ-005 | Documentation Impact | `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Phase 4 | AC-6 | docs checkers | Confirmed by repository evidence |
| REQ-006 | Acceptance Criteria 3; Testing Expectations | `tests/agent/workflow/test_workflow_state_store.py` | Phase 3 | AC-5 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-007 | Required Changes 1; AI Implementation Instruction 1 | N/A: no file is modified (search record only) | Phase 1 | AC-2 | caller-search record | Explicit in issue |
