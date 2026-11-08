## Goal
Bring the workflow-database required-shape gate in line with the tables the runtime actually writes: require `tool_call_state`, drop `execution_snapshots` from consideration (retired by `wfaudit010`), and sync the duplicated four-table list in `deploy/init_db.sh`, `deploy/setup_services.sh` and the operator docs.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/services/workflow_schema.py` — `REQUIRED_WORKFLOW_TABLES` (L44-57) gains `tool_call_state` (with its required columns); no `execution_snapshots` entry (post-`wfaudit010`).
  - `deploy/init_db.sh` — `REQUIRED_WORKFLOW_TABLES` list (L46) updated identically.
  - `deploy/setup_services.sh` — `REQUIRED_WORKFLOW_TABLES` list (L55) updated identically.
  - Docs: `docs/41_db/db_02_architecture_and_schema-schema-reference.md:46`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md:45`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md:143`, `docs/90_deployment/deployment_01_deployment.md:165,300`.
  - Tests: gate accepts a fresh schema-created database; gate rejects a database missing `tool_call_state` with the fixed refusal message.
- **Out-of-Scope**:
  - Adding a version identifier or migration path (the workflow domain's no-migration policy stands — `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`).
  - Auto-repairing legacy databases (the gate refuses; archive-and-recreate remains the documented remedy).
- **Dependencies**: After `wfaudit010` (final table set: `execution_snapshots` retired) and after `wfaudit002` (confirms no DDL change to `tool_call_state`). These two decisions determine the gate's final list; this plan closes the shape contract.

## Background
`create_workflow_schema()` creates five tables today including `tool_call_state` (`scripts/db/schema_sql.py:229-237`; `execution_snapshots` retired 2026-11-08, commit 4e46f5958), while the startup gate's `REQUIRED_WORKFLOW_TABLES` (`scripts/agent/services/workflow_schema.py:46-58`) lists only `tasks`, `attempts`, `processed_events`, `artifacts`. Incremental workflow migrations were retired (archived `issues/done/20261021-102049_rmwfmig_...`), so the gate is the only shape guarantee on an existing database. The deploy pre-flights duplicate the same four-table list (`deploy/init_db.sh:46`, `deploy/setup_services.sh:55`), and the stale list is propagated into `docs/41_db` (L46, L143) and `docs/90_deployment/deployment_01_deployment.md` (L165,300). Verified in the issue's `## Adversarial Validation`.

## Problem
A `workflow.sqlite` without `tool_call_state` passes the gate and deploy pre-flight, then fails at the first tool-call state insert in production — a shape error detected at runtime instead of at startup, which is exactly what the gate exists to prevent.

## Reason for Change
The gate is the domain's single shape mechanism; its list must equal the tables the runtime writes. Leaving the duplicate lists (script + docs) unsynced guarantees the gap reappears.

## Implementation Intent
Extend the required-shape list to the post-`wfaudit010` runtime table set — `tasks`, `attempts`, `processed_events`, `artifacts`, `tool_call_state` — with required columns for `tool_call_state` mirroring the DDL; mirror the change in `deploy/init_db.sh` and `deploy/setup_services.sh`; update every doc row that repeats the list.

## Requirements
- `REQ-001`: `check_workflow_schema()` requires `tool_call_state` (and its non-nullable columns: `idempotency_key`, `task_id`, `tool`, `state`, `retry_class`, `created_at`, `updated_at`) and still refuses legacy migration-era databases with the fixed message.
- `REQ-002`: The required-tables lists in `deploy/init_db.sh` and `deploy/setup_services.sh` match `REQUIRED_WORKFLOW_TABLES` exactly (a test pins the lists equal).
- `REQ-003`: A database created by `create_workflow_schema()` after `wfaudit010`/`wfaudit002` passes the gate (no newly rejected shape — verified: `wfaudit010` removes `execution_snapshots` from creation, and the gate does not require it).
- `REQ-004`: All five doc locations state the five-table list; no doc still describes `execution_snapshots` as required (cross-check with `wfaudit010` doc edits).
- `REQ-005`: New gate tests: fresh schema passes; database missing `tool_call_state` is rejected with the refusal message naming the missing table.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-08 (fallout): added deploy/setup_services.sh — REQUIRED_WORKFLOW_TABLES shell list (L55) identical to init_db.sh; gate check refuses on missing tables
Amended 2026-11-08 (fallout): added docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md — L45 states the workflow DB holds four tables (tasks, attempts, processed_events, artifacts); the REQ-004 acceptance grep scans docs/41_db

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/services/workflow_schema.py` | Modify | `REQUIRED_WORKFLOW_TABLES` (L46-58) add `tool_call_state` + column requirements | `REQ-001` | Four-table list verified (Step 2) | `tests/agent/test_repl_health.py` (`TestCheckWorkflowSchema`) | `Verified` |
| `deploy/init_db.sh` | Modify | `REQUIRED_WORKFLOW_TABLES` string (L46) extended identically | `REQ-002` | Duplicate hardcoded list verified | `tests/deploy/` script tests (shell-level) | `Verified` |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Modify | L46 required-tables text | `REQ-004` | Stale list verified | docs checkers | `Verified` |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | L143 accepted-shape list | `REQ-004` | Stale list verified | docs checkers | `Verified` |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | L165 and L300 required-tables lists | `REQ-004` | Stale lists verified | docs checkers | `Verified` |
| `deploy/setup_services.sh` | Modify | REQUIRED_WORKFLOW_TABLES shell list (L55) identical to init_db.sh; gate check refuses on missing tables | REQ-002 / N/A: none cites REQ-002 | Hardcoded four-table list verified at L55 (procedure pass 2026-11-08) | tests/deploy/test_setup_services_eventbus.py (seeds workflow DB; must seed tool_call_state) | Verified |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify | L45 states the workflow DB holds four tables (tasks, attempts, processed_events, artifacts); the REQ-004 acceptance grep scans docs/41_db | REQ-004 / N/A: none cites REQ-004 | Stale four-table sentence verified at L45 (procedure pass 2026-11-08) | docs checkers (db domain) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/schema_sql.py` | Source of the post-retirement table/column shapes the gate must mirror | `REQ-001` |
| `plans/20261108-084001_wfaudit010_snapshots-never-written.md` | Decision that fixes `execution_snapshots` out of the required set | Dependencies |
| `plans/20261108-084005_wfaudit002_tool-state-key-collisions.md` | Confirms `tool_call_state` shape is unchanged (value-level key only) | Dependencies |
| `scripts/agent/startup_component_init.py` | Gate invocation point (imports `check_workflow_schema` L20, invokes it L71/L140-144; `repl_health.py` was dissolved into `agent/services/`) | `REQ-005` |

## Acceptance Criteria
- `REQ-001`: Gate test matrix: fresh-created DB -> accepted; DB created without `tool_call_state` -> refused naming the table; legacy DB with `schema_migrations` -> refused with the fixed message (existing behavior unchanged).
- `REQ-002`: List-equality test parses the shell constants in `deploy/init_db.sh` and `deploy/setup_services.sh` and the Python list and asserts equality.
- `REQ-003`: `create_workflow_schema()`-created database (post-010) passes `check_workflow_schema()`.
- `REQ-004`: `grep -rn "tasks.*attempts.*processed_events.*artifacts" docs/41_db docs/90_deployment` shows only five-table forms.
- `REQ-005`: New tests fail on HEAD and pass after; full `tests/agent/` + deploy tests green.

## Tests
- Gate acceptance/rejection matrix in `tests/agent/test_repl_health.py` (`TestCheckWorkflowSchema`; the `_create_workflow_db` helper seeds only the four tables and must be extended).
- Shell-vs-Python list equality test (parses `deploy/init_db.sh` and `deploy/setup_services.sh`).
- Fresh-schema round-trip test after `wfaudit010`'s DDL state.

## Documentation Impact
- Five doc rows above updated to the five-table required shape.
- Cross-check `wfaudit010`'s doc edits so no doc simultaneously says "retired" and "required".
- Run docs checkers for domains db/deployment per `routing.md`.

## Assumptions
- `wfaudit010`'s retire decision stands; if the owner chooses keep instead, `execution_snapshots` joins the required list and this plan's rows change by one entry (dependency recorded, not assumed away).
- Legacy production databases already contain `tool_call_state` (every `create_workflow_schema()` run since the table's introduction creates it) — a probe confirms before deploy.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether any long-lived production `workflow.sqlite` predates `tool_call_state` introduction (would refuse startup after this change) | production DB table census not taken | `SELECT name FROM sqlite_master` probe on deploy host before rollout; archive-and-recreate if truly missing | `False` (probe precedes deploy, not code) |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/services/workflow_schema.py` | Modify | every agent-service startup | 6 | N/A | not applicable (rsynced) |
| `deploy/init_db.sh` | Modify | deploy pre-flight | 6 | N/A | direct deploy artifact — sync required |
| docs (5 files) | Modify | docs only | N/A | N/A | not applicable |
| `deploy/setup_services.sh` | Modify | Not assessed (amendment 2026-11-08) | N/A | N/A | Not assessed (amendment 2026-11-08) |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify | Not assessed (amendment 2026-11-08) | N/A | N/A | Not assessed (amendment 2026-11-08) |

## Design
**One required-shape list, three mirrors.** The Python gate is the semantic source; the two shell constants are mechanical mirrors pinned equal by a test (the alternative — sourcing the shell list from Python at deploy time — was rejected as it couples the pre-flight script to the venv).

**Column-level requirements for `tool_call_state`** mirror the existing per-table column requirements the gate already performs for the four tables; the refusal message format is reused so operators see one consistent shape error shape.

**Rollout order**: probe production databases first (`UNK-01`); the gate change ships only after confirming every live database passes, so no service is bricked by the tightened gate.

## Implementation steps
1. **Phase 1: Gate + scripts (`REQ-001`, `REQ-002`, `REQ-003`).** Extend the Python gate list and both shell mirrors; add gate matrix and equality tests.
   - [ ] Modify (REQ-002; `deploy/setup_services.sh`) — amendment 2026-11-08
2. **Phase 2: Docs (`REQ-004`).** Five doc rows; docs checkers.
   - [ ] Modify (REQ-004; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`) — amendment 2026-11-08
3. **Phase 3: Production probe (`UNK-01`).** Read-only census on deploy host before rollout; recorded in Execution Status.

### Release units
**Unit**: wfaudit003-full | **Phases**: 1, 2, 3 | **Reason**: a shape gate must ship atomically with its script mirror and docs; partial sync recreates the drift that caused this issue.

## Validation plan
- `uv run pytest tests/agent/ tests/deploy/ -q` after Phase 1; full `uv run pytest tests/ -q` before completion.
- New gate tests fail on HEAD (missing-table database currently accepted).
- Deploy dry-run: run `deploy/init_db.sh` pre-flight against a fixture DB built with the fresh schema.
- Lint/type gates per `rules/toolchain.md`; docs checkers after Phase 2.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A legacy production database lacks `tool_call_state` and startup is refused after rollout | Low | High (service won't boot) | Phase 3 probe before rollout; archive-and-recreate documented in `docs/41_db/db_07` |
| Gate and shell list drift again | Medium | Medium | List-equality test in CI |
| Column-level requirements drift from DDL | Medium | Low | Gate column lists derived in the same change as DDL reading; covered by fresh-schema round-trip test |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Gate + scripts (workflow_schema.py gate, init_db.sh and setup_services.sh mirrors, gate matrix + parity tests) | Completed | 20261109-072224 | 20261109-072224 | procedures 144827_01-03 generated 2026-11-08 |
| 2 | Phase 2: Docs (db_02, db_03, db_07, deployment_01; docs checkers) | Completed | 20261109-072224 | 20261109-072224 | procedures 144827_04-07 generated 2026-11-08 |
| 3 | Phase 3: Production probe (UNK-01 census on deploy host before rollout) | Completed | 20261109-072224 | 20261109-072224 |  |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|
| `144827_01` | implementation-procedure | `implementations/20261108-144827_01_scripts_agent_services_workflow_schema.py.md` | 2026-11-08 |
| `144827_02` | implementation-procedure | `implementations/20261108-144827_02_deploy_init_db.sh.md` | 2026-11-08 |
| `144827_03` | implementation-procedure | `implementations/20261108-144827_03_deploy_setup_services.sh.md` | 2026-11-08 |
| `144827_04` | implementation-procedure | `implementations/20261108-144827_04_docs_41_db_db_02_architecture_and_schema-schema-reference.md.md` | 2026-11-08 |
| `144827_05` | implementation-procedure | `implementations/20261108-144827_05_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md` | 2026-11-08 |
| `144827_06` | implementation-procedure | `implementations/20261108-144827_06_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md` | 2026-11-08 |
| `144827_07` | implementation-procedure | `implementations/20261108-144827_07_docs_90_deployment_deployment_01_deployment.md.md` | 2026-11-08 |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203216_wfaudit003_schema-gate-table-gap.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084006
- **Related target files**: see Implementation Target Files table, deploy/setup_services.sh, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem (gate gap) | `scripts/agent/services/workflow_schema.py` | tool_call_state required, refusal message | gate matrix tests |
| `REQ-002` | Issue Problem (duplicate list) | `deploy/init_db.sh`, `deploy/setup_services.sh` | lists equal | equality test |
| `REQ-003` | Issue constraint (no new rejections) | schema round-trip | fresh DB passes | round-trip test |
| `REQ-004` | Issue Problem (docs propagation) | 5 docs | five-table everywhere | docs checkers + grep |
| `REQ-005` | Issue Testing Expectations | tests | fail on HEAD | pytest |
| REQ-002 | Amendment 2026-11-08: REQUIRED_WORKFLOW_TABLES shell list (L55) identical to init_db.sh; gate check refuses on missing tables | deploy/setup_services.sh | Phase 1 | N/A: none cites REQ-002 | tests/deploy/test_setup_services_eventbus.py (seeds workflow DB; must seed tool_call_state) | Confirmed by repository evidence |
| REQ-004 | Amendment 2026-11-08: L45 states the workflow DB holds four tables (tasks, attempts, processed_events, artifacts); the REQ-004 acceptance grep scans docs/41_db | docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Phase 2 | N/A: none cites REQ-004 | docs checkers (db domain) | Confirmed by repository evidence |

## Notes
- Source verified against HEAD `926dbc109`; evidence in the issue's `## Adversarial Validation`.
- Sequence: `wfaudit010` -> `wfaudit002` -> this plan (final shape first, gate second).
- Corrections 2026-11-08 (procedure pass, re-verified against HEAD `ad48bfa28`):
  - Gate dict is at L46-58, not L44-57; `tool_call_state` DDL is at `schema_sql.py` L229-237.
  - `execution_snapshots` was retired from the workflow DDL on 2026-11-08 (commit `4e46f5958`);
    `create_workflow_schema()` now creates five tables, not six. Background updated accordingly.
  - Second hardcoded shell mirror found: `deploy/setup_services.sh` L55 (added as a Modify row;
    REQ-002 scope extended). `tests/deploy/test_setup_services_eventbus.py` seeds the four-table
    subset and must be updated with that row.
  - Fourth stale doc list found: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
    L45 (added as a Modify row; REQ-004 scope extended).
  - Gate tests live in `tests/agent/test_repl_health.py` (`TestCheckWorkflowSchema`); the earlier
    "`tests/agent/services/` gate tests" reference was a path error.
  - `scripts/agent/repl_health.py` no longer exists; the gate caller is
    `scripts/agent/startup_component_init.py` (Reference Files updated).

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-144827 -->