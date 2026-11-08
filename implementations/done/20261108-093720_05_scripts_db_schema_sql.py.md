# Implementation procedure: `scripts/db/schema_sql.py` — CHECK constraints on `tasks.status` and `attempts.status`

## Goal
Constrain fresh-database status columns with CHECK clauses whose allowed sets equal the Python vocabularies, pinned by a test instead of an import (`REQ-003`).

## Scope
**Release unit**: wfaudit005-full

- Add CHECK clauses to `tasks.status` (L184) and `attempts.status` (L194) in the workflow DDL.
- Companion test file `tests/db/test_create_schema.py`: CHECK rejection tests + SQL-vs-Python equality test.

## Assumptions
- Import contract (corrected in the Plan Design at revalidation): import-linter contract `db-only-uses-shared` forbids `db` importing `agent`, so the DDL carries literal CHECK sets with a comment naming the `models.py` constants (sibling document `20261108-093720_01_scripts_agent_workflow_models.py.md`), and the companion equality test pins them together.
- Existing databases are untouched (Plan Out-of-Scope: no ALTER path).

## Design decisions
- CHECK text mirrors the `tool_call_state.state` pattern (Plan Background): `CHECK (status IN (...))` inline in the column definition.
- The equality test lives in `tests/db/` (tests may import both layers): it extracts the allowed names from the DDL string and compares them to the frozensets imported from `agent.workflow.models` — the only mechanism that satisfies "SQL and Python can never drift" without an import edge (`REQ-003`).

## Alternatives considered
- Moving the vocabularies to `scripts/shared/` so the DDL builder could import them: rejected in the sibling seq 01 document (domain data in the leaf layer); the test pinning is sufficient and keeps the contract clean.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Change the `tasks` column line to `status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'halted')),` with a short SQL comment naming the `agent/workflow/models.py` vocabulary as the pinned source.
2. Change the `attempts` column line to `status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),` with the same comment style.

### Method
- Two column-definition edits; defaults stay; `tool_call_state.state` CHECK pattern is the formatting model.

### Details
- Current state (verified at HEAD `11c20696a`): `tasks.status` (L184) and `attempts.status` (L194) have `DEFAULT` but no CHECK (line citations unchanged); `tool_call_state.state` (L231, was L237) shows the pattern.
- Cross-batch interaction: the sibling `wfaudit010` batch (`implementations/20261108-092904_01_scripts_db_schema_sql.py.md`) removed the `execution_snapshots` table and `snapshot_id` column from the same file and landed first (commit `4e46f5958`); these edits touch different statements and do not overlap.

### Companion test files
- `tests/db/test_create_schema.py`
  - Procedure: add tests that (a) inserting/updating a fresh database with an out-of-vocabulary status raises `sqlite3.IntegrityError` (CHECK) for both tables; (b) an equality test parses the allowed status names from the DDL SQL string and asserts set equality with `TASK_STATUSES` / `ATTEMPT_STATUSES` imported from `agent.workflow.models`; run the full `tests/db/` + `tests/agent/` suites and fix any direct-insert fixture writing an out-of-vocabulary status (direct fixtures re-verified at HEAD `11c20696a`: `tests/db/test_create_schema.py` L552-590 (was L537-572 before `4e46f5958`), `tests/agent/workflow/test_state_store.py` L84-89, `tests/agent/workflow/test_workflow_state_store.py` L112/282/549 — all currently write vocabulary-valid values `pending`/`running`/`failed`).
  - Validation: `uv run pytest tests/db/test_create_schema.py -q` — CHECK tests fail on pre-change HEAD (insert silently succeeds) and pass after the change.

## Compatibility considerations
- Fresh databases only: existing databases never gain the CHECK (Plan Assumptions: code-side validation is the enforcement there).
- Legacy-shape fixtures/tests are unaffected: adding a CHECK cannot invalidate reads, only out-of-vocabulary writes in test fixtures (companion procedure step above).

## Security considerations
- N/A: DDL constraint addition.

## Rollback considerations
- N/A: revert the commit; databases created meanwhile keep their CHECKs harmlessly (valid writers never trip them).

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/db/schema_sql.py` | schema unit (companion file) | `uv run pytest tests/db/test_create_schema.py -q` | CHECK + equality tests fail pre-fix, pass post-fix |
| fixture fallout | full suites | `uv run pytest tests/db/ tests/agent/ -q` | green; stray-status fixtures fixed if found |
| gates | static | `rules/toolchain.md` sequence incl. `PYTHONPATH=scripts uv run lint-imports` | clean, no new import edge |

## Completion criteria
- Fresh databases reject out-of-vocabulary status writes with a CHECK error, and the equality test proves DDL sets == Python sets (`Acceptance Criteria REQ-003`).

## Out of Scope
- Enforcing CHECKs on existing databases (Plan Out-of-Scope).
- Vocabulary tests in `tests/agent/workflow/` (sibling seq 06 document owns them).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261108-130138 | 20261108-130138 | Blocks wfaudit001 and wfaudit007; wfaudit010 batch on the same file lands first memo3 adversarial verification pass at HEAD 11c20696a: stale check clean; L184/L194 unchanged; pattern citation L231; fixture citations L552-590 re-verified vocabulary-valid CHECK clauses added to tasks.status/attempts.status with models.py pin comments |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | 20261108-130138 | 20261108-130138 | TestWorkflowStatusCheckConstraints added: 4 CHECK rejection tests + 2 DDL-vs-python equality tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-130138 | 20261108-130138 | ruff+format+mypy+lint-imports+check_db_separation pass; tests/db+tests/agent 4552 passed 3 skipped (REQ-005 no fixture fallout); stale_detector clean |

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
- **Requirement ID**: `REQ-003` (DDL CHECKs pinned equal to the Python vocabularies)
- **Source issue**: `issues/20261107-203218_wfaudit005_unvalidated-status-writes.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084002_wfaudit005_unvalidated-status-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-093720
- **Related target files**: `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`