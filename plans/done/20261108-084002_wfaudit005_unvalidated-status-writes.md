## Goal
Declare the allowed status vocabulary per workflow table in one place, validate every status write in the three helpers that pass caller-supplied strings into SQL, and add CHECK constraints to the fresh-database DDL — ending the state machine that today exists only as scattered string literals.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/workflow/models.py` — declare `TASK_STATUSES` and `ATTEMPT_STATUSES` (and reuse the existing tool-call CHECK vocabulary as a shared constant).
  - `scripts/agent/workflow/task_ops.py` — `update_task_status` validates against `TASK_STATUSES` before SQL.
  - `scripts/agent/workflow/attempt_ops.py` — `finish_attempt` validates against `ATTEMPT_STATUSES`.
  - `scripts/agent/workflow/tool_call_state_ops.py` — `finalize_tool_call` validates against the tool-call vocabulary (mirroring the existing SQL CHECK).
  - `scripts/db/schema_sql.py` — CHECK constraints on `tasks.status` and `attempts.status` for fresh databases.
  - Tests: rejection cases for each helper; vocabulary-vs-writers consistency test.
- **Out-of-Scope**:
  - Enforcing CHECK constraints on existing databases (no ALTER/migration path exists in the workflow domain).
  - Renaming status values or collapsing the halt/failure semantics.
  - The recovery reconciliation writes (`wfaudit001`/`wfaudit007`) — they consume this vocabulary but change elsewhere.
- **Dependencies**: Blocks `wfaudit001` and `wfaudit007`: the reconciliation status values they write must come from the vocabulary declared here. Land this plan first.

## Background
`tasks.status` (`scripts/db/schema_sql.py:184`, default `'pending'`) and `attempts.status` (L194, default `'running'`) have no CHECK; `tool_call_state.state` (L237) does — the pattern to mirror. Writers pass raw strings: `update_task_status` (`scripts/agent/workflow/task_ops.py:68-74`), `finish_attempt` (`attempt_ops.py:80-94`), `finalize_tool_call` (`tool_call_state_ops.py:74-80`). Observed vocabularies (issue Adversarial Validation): `tasks.status` gets `pending` (DDL default), `running`, `halted`, `failed`, `completed` (engine `workflow_engine.py:213-224`; adapter writes only `halted` via `_status_for_exit`, `workflow_engine_adapter.py:230,273`); `attempts.status` gets `running` (`begin_stage_if_new`), `completed`, `failed` (`finish_attempt`, recovery `state_store.py:216-224`). No single declaration exists; each writer hardcodes literals.

## Problem
Any caller can write any string to a status column: a typo produces an invisible row that no reader recognizes, and readers (the halted-task guard at `workflow_engine_adapter.py:315`) silently miss it. The implicit state machine is undeclared, so consistency between writers, readers, docs, and future reconciliation writes cannot be checked.

## Reason for Change
The same table family already demonstrates the pattern (`tool_call_state.state` CHECK). Declaring the vocabulary is also a hard prerequisite for the recovery-reconciliation plans (`wfaudit001`, `wfaudit007`): without it, their new status values would be more scattered literals.

## Implementation Intent
Declare once, validate at every writer, constrain fresh DDL: Python frozensets in `models.py` as the single source of truth, helper-level validation raising `ValueError` for out-of-vocabulary statuses, and DDL CHECKs generated from (and pinned equal to) the same vocabularies. Existing databases are validated by code only; DDL constraints apply to newly created databases.

## Requirements
- `REQ-001`: `models.py` declares `TASK_STATUSES = {pending, running, completed, failed, halted}` and `ATTEMPT_STATUSES = {running, completed, failed}`, plus `TOOL_CALL_STATES = {pending, completed, failed, interrupted}` mirroring the existing CHECK.
- `REQ-002`: `update_task_status`, `finish_attempt`, and `finalize_tool_call` raise `ValueError` (naming the value and table) before executing SQL when the status is not in the declared set.
- `REQ-003`: Fresh-database DDL carries CHECK constraints on `tasks.status` and `attempts.status` whose allowed sets equal the Python declarations; a test pins SQL and Python to the same frozensets.
- `REQ-004`: Every status literal currently written in `scripts/` is in the declared vocabulary (consistency test greps-walk of writer call sites, or a static assertion list); recovery writes (`state_store.py`) map to `ATTEMPT_STATUSES`.
- `REQ-005`: New tests pin `REQ-002` rejections per helper and the DDL/Python equality; existing writer behavior for valid statuses unchanged.

## Implementation Target Files
**Freeze status**: Frozen (revalidated 20261108 against HEAD `50b5ac2c6` — see Notes; one Reference Files row corrected)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/models.py` | Modify | Add the three vocabulary frozensets (single source of truth) | `REQ-001` | No vocabulary declaration exists (grep) | `tests/agent/workflow/` | `Verified` |
| `scripts/agent/workflow/task_ops.py` | Modify | Validate `status` in `update_task_status` (L68-74); creation default stays `pending` | `REQ-002` | Writer takes arbitrary string (Step 2 validation) | `tests/agent/workflow/test_workflow_state_store.py` | `Verified` |
| `scripts/agent/workflow/attempt_ops.py` | Modify | Validate `status` in `finish_attempt` (L80-94) | `REQ-002` | Writer takes arbitrary string | `tests/agent/workflow/` | `Verified` |
| `scripts/agent/workflow/tool_call_state_ops.py` | Modify | Validate `state` in `finalize_tool_call` (L74-80) against `TOOL_CALL_STATES` | `REQ-002` | SQL CHECK exists, code-side validation does not | `tests/agent/workflow/` | `Verified` |
| `scripts/db/schema_sql.py` | Modify | Add CHECK clauses to `tasks.status` (L184) and `attempts.status` (L194) generated from the models constants | `REQ-003` | No CHECK today vs `tool_call_state` pattern (L237) | `tests/db/` schema tests | `Verified` |
| `tests/agent/workflow/` (state-store + ops tests) | Modify | Rejection cases (`ValueError`) per helper; DDL/Python vocabulary-equality test | `REQ-002`/`REQ-003`/`REQ-005` | Current tests assert happy paths only | self | `Verified` |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Modify | Add the allowed status vocabulary for `tasks.status` and `attempts.status` to the workflow tables section (row added at revalidation: the Documentation Impact requires a target; the doc carries no status text today) | `REQ-003`/`REQ-004` | Grep at revalidation: no `status` mention in the doc | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` | Enumerates the task statuses written today (L213-224) — feeds `REQ-001`/`REQ-004` | `REQ-001` |
| `scripts/agent/workflow_engine_adapter.py` | `_status_for_exit`/`_record_exit_status` writes `halted` only (L49-62,273) | `REQ-004` |
| `scripts/agent/workflow/state_store.py` | Recovery writes `failed` to attempts (`recover_stale_attempts` UPDATE at L225-226, WHERE-guarded on `status='running'`) — must remain vocabulary-valid | `REQ-004` |
| `scripts/agent/workflow/idempotency_ops.py` | `begin_stage_if_new` writes `running` on attempt insert (L63-80); no compensation status writes exist in this module (corrected at revalidation — `completed`/`failed` attempt writes live in `workflow_engine.py` `finish_attempt` call sites) | `REQ-004` |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Workflow table reference; carries NO status-vocabulary text today (corrected at revalidation) — the Documentation Impact step adds the allowed status values per column, so the doc becomes a Modify target row below | Documentation Impact |

## Acceptance Criteria
- `REQ-001`: The three frozensets exist in `models.py` and are imported by all three ops modules. `REQ-003`'s equality test (not a DDL import — see Design, contract `db-only-uses-shared`) connects them to the SQL CHECKs.
- `REQ-002`: `update_task_status(task, "done")`, `finish_attempt(id, "done")`, `finalize_tool_call(key, "done")` each raise `ValueError` and write nothing (test asserts row unchanged).
- `REQ-003`: Inserting an out-of-vocabulary status directly via SQL into a fresh database fails with a CHECK constraint error; the equality test proves DDL sets == Python sets.
- `REQ-004`: Consistency test passes: every status literal written in `scripts/agent/workflow*/` is in the corresponding frozenset.
- `REQ-005`: Full `tests/agent/ tests/db/` green; all existing engine/adapter flows unchanged for valid statuses.

## Tests
- Per-helper rejection tests (`ValueError`, no write).
- DDL-vs-constants equality test (`tests/db/`): parse the CHECK clause, compare to frozensets.
- Vocabulary-consistency test walking the known writer call sites.
- Regression: engine run paths already covered by existing stage tests stay green.

## Documentation Impact
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` — state allowed status values per column.
- Check `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` for status descriptions — confirmed at revalidation: it carries no `status` column text (only the `tool_call_state` row's state list, already matching the vocabulary); no edit needed.
- Run docs checkers for domains db/agent per `routing.md`.

## Assumptions
- The observed vocabularies are complete: no third-party or script writes other status strings today (validated by grep at HEAD; a production probe query is included in the validation plan to catch historical stray rows).
- Code-side validation is the enforcement that matters for existing databases; DDL CHECKs protect fresh databases only.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether production `workflow.sqlite` already contains stray status values written before validation (would only matter if a CHECK were later added to legacy DBs — it is not) | production DB not probed | one `SELECT DISTINCT status` probe per table during deploy validation | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/models.py` | Modify | imported by all workflow modules | 3 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/task_ops.py` | Modify | every task status write | 3 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/attempt_ops.py` | Modify | every attempt finish | 1 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/tool_call_state_ops.py` | Modify | tool-call finalize | 2 | N/A | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | Modify | fresh-database DDL only | 17 | N/A | not applicable (rsynced) |
| `tests/agent/workflow/` | Modify | tests only | N/A | N/A | not applicable (rsynced) |

## Design
**Single declaration (`models.py`), contract-safe pinning.** Frozensets live next to the existing dataclasses so ops modules import them without a new module. The DDL builder CANNOT import them: the import-linter contract `db-only-uses-shared` forbids `db` importing `agent` (`.importlinter`, corrected at revalidation). `schema_sql.py` writes the CHECK literals with a comment naming the `models.py` constants, and a `tests/db/` equality test pins the SQL sets to the Python frozensets — the drift guard required by `REQ-003` lives in the test, not in an import edge.

**Validate at the writer, not the caller.** The three helpers are the chokepoints every production status write already flows through (engine, adapter, recovery, idempotency compensation all call them). A `ValueError` naming the table and offending value is consistent with project typed-error convention; `execute_turn`'s best-effort status write (`_record_exit_status`, L262-275) already swallows exceptions in its own try, so a vocabulary bug there degrades observably instead of aborting a turn.

**Legacy databases.** No ALTER. Writers are validated in code, so legacy rows can only already contain in-vocabulary values written by current code; the probe query confirms no strays.

## Implementation steps
1. **Phase 1: Vocabulary + writer validation (`REQ-001`, `REQ-002`).** Add frozensets; validate the three helpers; add rejection tests.
2. **Phase 2: DDL CHECKs (`REQ-003`).** Generate CHECKs from the constants; add schema + equality tests.
3. **Phase 3: Consistency + docs (`REQ-004`).** Consistency test; docs updates; run docs checkers.

### Release units
**Unit**: wfaudit005-full | **Phases**: 1, 2, 3 | **Reason**: vocabulary declaration and enforcement are one contract; partial landing (declaration without writers validated) would leave the contract untestable.

## Validation plan
- `uv run pytest tests/agent/workflow/ tests/db/ -q` after each phase; full `uv run pytest tests/ -q` before completion.
- Production probe (read-only, deploy host): `SELECT DISTINCT status FROM tasks; SELECT DISTINCT status FROM attempts;` — record results in the Execution Status notes (`UNK-01`).
- New rejection tests must fail on HEAD (silent acceptance) and pass after Phase 1.
- Lint/type gates per `rules/toolchain.md`; docs checkers after Phase 3.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A writer passes a status the vocabulary misses (future `wfaudit001`/`wfaudit007` value) | Medium | Low (loud ValueError at the writer) | Those plans are sequenced after this one and must import the constants; consistency test catches drift in CI |
| DDL CHECK breaks a test fixture that writes a stray status directly via SQL | Medium | Low | Fixtures updated in Phase 2; fixtures are the only known direct writers |
| `finalize_tool_call` validation rejects a value the dispatcher-side store uses (different vocabulary) | Low | Medium | The dispatcher dedup store (`scripts/shared/mcp_dedup.py`) has its own state space; this validation covers only `tool_call_state` — verified boundary in Step 2 |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: vocabulary + writer validation (`REQ-001`, `REQ-002`) | Completed | 20261108-125000 | 20261108-125519 | procedures 01-04 landed: TASK_STATUSES/ATTEMPT_STATUSES/TOOL_CALL_STATES + guard-first ValueError in update_task_status/finish_attempt/finalize_tool_call |
| 2 | Phase 2: DDL CHECKs (`REQ-003`) | Completed | 20261108-125600 | 20261108-130138 | procedure 05 landed: CHECK on tasks.status/attempts.status + TestWorkflowStatusCheckConstraints (rejection + DDL-vs-python equality) |
| 3 | Phase 3: consistency + docs (`REQ-004`) | Completed | 20261108-130200 | 20261108-131819 | Production probe (`UNK-01`) recorded here at deploy validation procedures 06-07 landed: test_workflow_status_vocabulary.py + lifecycle rejection asserts + schema-reference prose; fail-on-HEAD proven (3 rejection tests failed pre-change); UNK-01 production probe: read-only SELECT DISTINCT on /opt/llm/db/workflow.sqlite returned 0 rows in tasks/attempts/tool_call_state (no retained rows violate the vocabularies); full suite 11847 passed 7 skipped; diff-cover 100% >= 90 |

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
- **Source issue**: `issues/20261107-203218_wfaudit005_unvalidated-status-writes.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084002
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem (undeclared state machine) | `scripts/agent/workflow/models.py` | Frozensets exist and are imported | import + equality tests |
| `REQ-002` | Issue Problem (unvalidated writes) | 3 ops modules | Out-of-vocabulary status raises, no write | per-helper rejection tests |
| `REQ-003` | Issue Required Changes (CHECK constraints) | `scripts/db/schema_sql.py` | Fresh-DB CHECK == Python sets | schema/equality tests |
| `REQ-004` | Plan Design (consistency) | writer call sites | All written literals vocabulary-valid | consistency test |
| `REQ-005` | Issue Testing Expectations | tests | New tests fail on HEAD | pytest |

## Notes
- Source verified against HEAD `926dbc109`; evidence in the issue's `## Adversarial Validation`.
- Downstream: `wfaudit001`/`wfaudit007` reconciliation writes must use `ATTEMPT_STATUSES`/`TASK_STATUSES` values only.
- Adversarial re-verification 2026-11-08 (memo2 batch) against HEAD `50b5ac2c6`: all code claims re-confirmed — `tasks.status` DEFAULT 'pending' with no CHECK (`schema_sql.py` L184), `attempts.status` DEFAULT 'running' with no CHECK (L194), `tool_call_state.state` CHECK pattern (L237), raw-string writers `update_task_status` (`task_ops.py` L68-74), `finish_attempt` (`attempt_ops.py` L81-94), `finalize_tool_call` (`tool_call_state_ops.py` L74-80), engine writes `running`/`halted`/`failed`/`completed` (`workflow_engine.py` L213-224) and `failed`/`completed` attempt finishes (L331-371), adapter writes only `halted` (`_status_for_exit` L49-62, writes at L230/L273, best-effort try in `_record_exit_status` L262-278), halted guard at adapter L315, recovery UPDATE `status='failed'` at `state_store.py` L225-226 (Background's L216-224 citation is approximate; the write is inside `recover_stale_attempts` L190-248). One correction applied: the `idempotency_ops.py` Reference Files row claimed compensation `completed`/`failed` writes — that module has only `is_event_processed` and `begin_stage_if_new` (writes `running` only); the claim now points at the real `workflow_engine.py` call sites. The four Plan Freeze criteria pass for every row — all rows `Verified`; the section was therefore marked `Frozen` (Draft at intake; freeze performed in this verification pass per the owner's memo2 instruction). Third correction (architecture): the Design's "DDL builder imports the constants" violates the import-linter contract `db-only-uses-shared` (`db` must not import `agent`); the plan now pins SQL/Python equality via a `tests/db/` test instead of an import edge, and a `docs/41_db/db_02` Modify target row was added because the Documentation Impact step had no target row (the doc carries no `status` text today; `agent_04_03` was confirmed to need no edit).

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-093720 -->