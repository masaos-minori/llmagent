## Goal
Bring the workflow-database required-shape gate in line with the tables the runtime actually writes: require `tool_call_state`, drop `execution_snapshots` from consideration (retired by `wfaudit010`), and sync the duplicated four-table list in `deploy/init_db.sh` and the operator docs.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/services/workflow_schema.py` — `REQUIRED_WORKFLOW_TABLES` (L44-57) gains `tool_call_state` (with its required columns); no `execution_snapshots` entry (post-`wfaudit010`).
  - `deploy/init_db.sh` — `REQUIRED_WORKFLOW_TABLES` list (L46) updated identically.
  - Docs: `docs/41_db/db_02_architecture_and_schema-schema-reference.md:46`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md:143`, `docs/90_deployment/deployment_01_deployment.md:165,300`.
  - Tests: gate accepts a fresh schema-created database; gate rejects a database missing `tool_call_state` with the fixed refusal message.
- **Out-of-Scope**:
  - Adding a version identifier or migration path (the workflow domain's no-migration policy stands — `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`).
  - Auto-repairing legacy databases (the gate refuses; archive-and-recreate remains the documented remedy).
- **Dependencies**: After `wfaudit010` (final table set: `execution_snapshots` retired) and after `wfaudit002` (confirms no DDL change to `tool_call_state`). These two decisions determine the gate's final list; this plan closes the shape contract.

## Background
`create_workflow_schema()` creates six tables today including `execution_snapshots` (`scripts/db/schema_sql.py:227`) and `tool_call_state` (L233-242), while the startup gate's `REQUIRED_WORKFLOW_TABLES` (`scripts/agent/services/workflow_schema.py:44-57`) lists only `tasks`, `attempts`, `processed_events`, `artifacts`. Incremental workflow migrations were retired (archived `issues/done/20261021-102049_rmwfmig_...`), so the gate is the only shape guarantee on an existing database. The deploy pre-flight duplicates the same four-table list (`deploy/init_db.sh:46`), and the stale list is propagated into `docs/41_db` (L46, L143) and `docs/90_deployment/deployment_01_deployment.md` (L165,300). Verified in the issue's `## Adversarial Validation`.

## Problem
A `workflow.sqlite` without `tool_call_state` passes the gate and deploy pre-flight, then fails at the first tool-call state insert in production — a shape error detected at runtime instead of at startup, which is exactly what the gate exists to prevent.

## Reason for Change
The gate is the domain's single shape mechanism; its list must equal the tables the runtime writes. Leaving the duplicate lists (script + docs) unsynced guarantees the gap reappears.

## Implementation Intent
Extend the required-shape list to the post-`wfaudit010` runtime table set — `tasks`, `attempts`, `processed_events`, `artifacts`, `tool_call_state` — with required columns for `tool_call_state` mirroring the DDL; mirror the change in `deploy/init_db.sh`; update every doc row that repeats the list.

## Requirements
- `REQ-001`: `check_workflow_schema()` requires `tool_call_state` (and its non-nullable columns: `idempotency_key`, `task_id`, `tool`, `state`, `retry_class`, `created_at`, `updated_at`) and still refuses legacy migration-era databases with the fixed message.
- `REQ-002`: `deploy/init_db.sh` required-tables list matches `REQUIRED_WORKFLOW_TABLES` exactly (a test pins the two lists equal).
- `REQ-003`: A database created by `create_workflow_schema()` after `wfaudit010`/`wfaudit002` passes the gate (no newly rejected shape — verified: `wfaudit010` removes `execution_snapshots` from creation, and the gate does not require it).
- `REQ-004`: All four doc locations state the five-table list; no doc still describes `execution_snapshots` as required (cross-check with `wfaudit010` doc edits).
- `REQ-005`: New gate tests: fresh schema passes; database missing `tool_call_state` is rejected with the refusal message naming the missing table.

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/services/workflow_schema.py` | Modify | `REQUIRED_WORKFLOW_TABLES` (L44-57) add `tool_call_state` + column requirements | `REQ-001` | Four-table list verified (Step 2) | `tests/agent/services/` gate tests | `Verified` |
| `deploy/init_db.sh` | Modify | `REQUIRED_WORKFLOW_TABLES` string (L46) extended identically | `REQ-002` | Duplicate hardcoded list verified | `tests/deploy/` script tests (shell-level) | `Verified` |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Modify | L46 required-tables text | `REQ-004` | Stale list verified | docs checkers | `Verified` |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | L143 accepted-shape list | `REQ-004` | Stale list verified | docs checkers | `Verified` |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | L165 and L300 required-tables lists | `REQ-004` | Stale lists verified | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/schema_sql.py` | Source of the post-retirement table/column shapes the gate must mirror | `REQ-001` |
| `plans/20261108-084001_wfaudit010_snapshots-never-written.md` | Decision that fixes `execution_snapshots` out of the required set | Dependencies |
| `plans/20261108-084005_wfaudit002_tool-state-key-collisions.md` | Confirms `tool_call_state` shape is unchanged (value-level key only) | Dependencies |
| `scripts/agent/repl_health.py` (or current startup caller of `check_workflow_schema`) | Gate invocation point for the acceptance test | `REQ-005` |

## Acceptance Criteria
- `REQ-001`: Gate test matrix: fresh-created DB -> accepted; DB created without `tool_call_state` -> refused naming the table; legacy DB with `schema_migrations` -> refused with the fixed message (existing behavior unchanged).
- `REQ-002`: List-equality test parses the shell constant and the Python frozenset and asserts equality.
- `REQ-003`: `create_workflow_schema()`-created database (post-010) passes `check_workflow_schema()`.
- `REQ-004`: `grep -rn "tasks.*attempts.*processed_events.*artifacts" docs/41_db docs/90_deployment` shows only five-table forms.
- `REQ-005`: New tests fail on HEAD and pass after; full `tests/agent/` + deploy tests green.

## Tests
- Gate acceptance/rejection matrix in `tests/agent/services/` (extend existing gate tests).
- Shell-vs-Python list equality test (parses `deploy/init_db.sh`).
- Fresh-schema round-trip test after `wfaudit010`'s DDL state.

## Documentation Impact
- Four doc rows above updated to the five-table required shape.
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
| docs (4 files) | Modify | docs only | N/A | N/A | not applicable |

## Design
**One required-shape list, two mirrors.** The Python gate is the semantic source; the shell constant is a mechanical mirror pinned equal by a test (the alternative — sourcing the shell list from Python at deploy time — was rejected as it couples the pre-flight script to the venv).

**Column-level requirements for `tool_call_state`** mirror the existing per-table column requirements the gate already performs for the four tables; the refusal message format is reused so operators see one consistent shape error shape.

**Rollout order**: probe production databases first (`UNK-01`); the gate change ships only after confirming every live database passes, so no service is bricked by the tightened gate.

## Implementation steps
1. **Phase 1: Gate + script (`REQ-001`, `REQ-002`, `REQ-003`).** Extend both lists; add gate matrix and equality tests.
2. **Phase 2: Docs (`REQ-004`).** Four doc rows; docs checkers.
3. **Phase 3: Production probe (`UNK-01`).** Read-only census on deploy host before rollout; recorded in Execution Status.

### Release units
**Unit**: wfaudit003-full | **Phases**: 1, 2, 3 | **Reason**: a shape gate must ship atomically with its script mirror and docs; partial sync recreates the drift that caused this issue.

## Validation plan
- `uv run pytest tests/agent/services/ tests/agent/workflow/ -q` after Phase 1; full `uv run pytest tests/ -q` before completion.
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
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: gate + script | Planned | engineer | | | |
| Phase 2: docs | Planned | engineer | | | |
| Phase 3: production probe | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203216_wfaudit003_schema-gate-table-gap.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084006
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem (gate gap) | `scripts/agent/services/workflow_schema.py` | tool_call_state required, refusal message | gate matrix tests |
| `REQ-002` | Issue Problem (duplicate list) | `deploy/init_db.sh` | lists equal | equality test |
| `REQ-003` | Issue constraint (no new rejections) | schema round-trip | fresh DB passes | round-trip test |
| `REQ-004` | Issue Problem (docs propagation) | 4 docs | five-table everywhere | docs checkers + grep |
| `REQ-005` | Issue Testing Expectations | tests | fail on HEAD | pytest |

## Notes
- Source verified against HEAD `926dbc109`; evidence in the issue's `## Adversarial Validation`.
- Sequence: `wfaudit010` -> `wfaudit002` -> this plan (final shape first, gate second).
