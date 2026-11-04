## Goal
- Make the startup workflow-schema preflight stop creating an empty workflow database when it is missing: it checks the existence of the resolved database path (default path included) before any connection is opened, reports a distinct "not found" error, and no constant name contradicts its use.

## Priority
Medium

## Scope
- **In-Scope**:
  - In `check_workflow_schema`, apply the existence check to the path resolved by `SQLiteHelper` (explicit or default) before `open`, and return the existing "Workflow DB not found" result for a missing file.
  - Remove the misleading `_WORKFLOW_SCHEMA_READ_ONLY` constant and open the database with the read-style mode its name claims.
  - Tests for the default-path missing-database case (no file created), kept next to the existing schema tests.
- **Out-of-Scope**:
  - The required-table, column, and schema-version rules; the database ownership and path configuration (4DB separation); schema creation or migration inside the preflight.
  - `SQLiteHelper` behavior, the deploy scripts, other databases' startup checks, and the workflow definition preflight.
  - The pragma side effects of opening an already-existing database (see Assumptions).
- **Dependencies**: N/A: none. No open issue or in-flight Plan targets `scripts/agent/services/workflow_schema.py`.

## Background
`check_workflow_schema` guards against `sqlite3.connect()` creating files with `if db_path and not os.path.exists(db_path)`, so the guard runs only when a path is passed explicitly. The startup caller `ComponentInitializer._check_workflow_schema` passes none, so `SQLiteHelper(target="workflow")` resolves the default path and the file is created on open. `_WORKFLOW_SCHEMA_READ_ONLY = True` is passed as `write_mode`, which in `SQLiteHelper` only selects the foreign-key pragma (checked in Step 2).

## Problem
With the workflow database absent and no path argument, the preflight creates an empty file at the production path and then reports "Workflow schema missing table 'tasks'", which names the wrong cause. The Issue reproduced this with a throwaway script (file absent before, 4096 bytes afterward); the code path was re-read in Step 2 (guard condition, `SQLiteHelper._connect` calling `sqlite3.connect`, `open` applying the pragmas).

Verification corrections and findings:
1. The Issue's first unresolved question is answered: `create_workflow_schema` uses idempotent DDL (`IF NOT EXISTS`), records the schema version only when the version log is empty, and `ensure_baseline` is idempotent, so an empty pre-existing file does not break `deploy/init_db.sh`; the side effect is a stray file and a misleading message, not a deployment failure (read in Step 2; not run against a database).
2. `SQLiteHelper` already exposes the resolved path as the `DB_PATH` property for both explicit and default targets, so the guard needs no helper change; `scripts/db/helper.py` and `scripts/agent/startup_component_init.py` need no modification (the caller raises `RuntimeError(result.error)` and passes the new message through unchanged).
3. "Never creates the file or its WAL/SHM side files" holds only for an absent database: `open` runs `PRAGMA journal_mode=WAL`, so opening an existing database can still create or convert WAL side files. That behavior is unchanged and outside this Plan.
4. No document describes the preflight's missing-database message (a search of `docs/` for the message texts and the function name finds only ADR citations of the test class and operator messages of the deploy scripts), so no documentation change is needed.
5. The constant is also named in static text inside `tools/gen_wflease_procedures.py` (a generator of archived procedure text); it is a string, not an import, and is left as is.

## Reason for Change
A startup preflight must not modify the system it checks, and its error must name the real failure so the operator runs the right remediation. The constant name that contradicts its use invites a wrong later fix.

## Implementation Intent
Resolve the path through `db.DB_PATH`, return "not found" when the file is missing, and only then open. Drop the constant and pass `write_mode=False`, which matches a read-only check.

## Requirements
- `REQ-001`: `check_workflow_schema` MUST check the existence of the resolved database path (explicit or default) before opening a connection and MUST return `SchemaCheckResult(valid=False, error="Workflow DB not found: {path}")` for a missing file, creating no file at that path or its WAL/SHM side paths.
- `REQ-002`: The table, column, and schema-version checks and their error messages MUST NOT change; a valid database still passes and a database missing a table still names that table.
- `REQ-003`: `_WORKFLOW_SCHEMA_READ_ONLY` MUST be removed and the open call MUST pass `write_mode=False`, so no constant name contradicts its use.
- `REQ-004`: Tests MUST show that a missing database with no path argument yields the not-found error and leaves no file, using a temporary directory and no real workflow database; they MUST fail on the pre-change code and pass after it.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed: every row `Verified` — exists, requires modification, supporting evidence, linked to a Plan requirement; no path appears in both tables; no directory, glob, or vague row).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/services/workflow_schema.py` | Existence guard and constant | Move the existence check to the resolved path (`db.DB_PATH`) before `open`; remove `_WORKFLOW_SCHEMA_READ_ONLY`; open with `write_mode=False` (checked in Step 2) | REQ-001, REQ-002, REQ-003; AC-1, AC-2, AC-3, AC-4 | Guard is `if db_path and not os.path.exists(db_path)`; the constant is defined once and used once in `db.open(write_mode=...)`; `SQLiteHelper.DB_PATH` returns the resolved path (checked in Step 2) | `tests/agent/test_repl_health.py` | Verified |
| `tests/agent/test_repl_health.py` | New tests | Add default-path missing-database tests inside `TestCheckWorkflowSchema`, patching the helper's configuration builder to a temporary directory (checked in Step 2) | REQ-004; AC-1, AC-5 | `TestCheckWorkflowSchema` holds the valid, missing-table, missing-column, version, and explicit-path-not-found tests and the `_create_workflow_db` fixture; ADR-001 cites the class by name, so the class stays (checked in Step 2) | `tests/agent/test_repl_health.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/helper.py` | `SQLiteHelper` path resolution (`DB_PATH`), `_connect` creating files, and `open` pragmas; no change needed | REQ-001, REQ-003 |
| `scripts/agent/startup_component_init.py` | Calls `check_workflow_schema()` with no path and raises `RuntimeError(result.error)`; passes the new message through | REQ-001 |
| `tests/agent/test_startup_workflow_preflight.py` | Mocks `check_workflow_schema` at the caller; stays valid | REQ-001 |
| `scripts/db/create_schema.py` | `create_workflow_schema` is idempotent for an existing empty file (Step 2 evidence) | REQ-001 |
| `scripts/db/migrations_workflow.py` | `ensure_baseline` is idempotent (Step 2 evidence) | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-004): with the workflow database absent and no path argument, the preflight returns the not-found error and no file exists at that path or its WAL/SHM paths afterwards.
- AC-2 (REQ-001, REQ-002): with an explicit missing path, the existing not-found result is unchanged.
- AC-3 (REQ-002): a valid database passes; a database missing a required table or column still reports that table or column; the version mismatch message is unchanged.
- AC-4 (REQ-003): no constant name contradicts its use; the open call passes `write_mode=False`.
- AC-5 (REQ-004): the new tests fail on the pre-change code and pass after the change.

## Tests
- `REQ-004`: in `TestCheckWorkflowSchema`, patch `db.helper.build_db_config` to a configuration whose workflow path is inside `tmp_path` and absent; call `check_workflow_schema()`; assert `valid is False`, the error contains `Workflow DB not found`, and the directory contains no files.
- `REQ-002`: keep the existing valid, missing-table, missing-column, version, and explicit-path tests unchanged as the regression set.
- Regression: `tests/agent/test_repl_health.py`, `tests/agent/test_startup_workflow_preflight.py`, `uv run python tools/check_db_separation.py`.

## Documentation Impact
N/A: no document describes the preflight's missing-database message or its file side effect (rg over `docs/`, Step 2); the ADR citation of the test class stays valid.

## Assumptions
- Opening an already-existing database still applies `PRAGMA journal_mode=WAL` through `SQLiteHelper.open`; this is existing behavior and not changed here (read in Step 2).
- A failure to build the database configuration still raises from the `SQLiteHelper` constructor (a `RuntimeError`) instead of returning a result; that is existing behavior and out of scope.
- A file removed between the existence check and the open is not handled specially: the open would create it, which matches a deleted-during-startup race outside the preflight's contract.
- Overlap with other Frozen Plans: none reported by `tools/check_plan_target_overlaps.py` in Step 8b.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the preflight should also avoid the WAL pragma on an existing database (a fully read-only open). | The Issue asks only that a missing database is not created; a no-create open mode would need a `SQLiteHelper` change used by other databases, which the Issue says to stop on. | Separate Issue if the owner wants a read-only open mode. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/services/workflow_schema.py` | Modify | Low: one caller (`ComponentInitializer._check_workflow_schema`) and the repl-health tests | 4 | N/A | not applicable (rsynced) |
| `tests/agent/test_repl_health.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Decision 1, how to prevent creation. Alternatives: (a) apply the existing guard to the resolved path; (b) add a no-create open mode to `SQLiteHelper`. Chosen: (a). It needs no helper change, follows the Issue's stop condition about other databases, and keeps the "not found" message that tests already pin. Compatibility: the function signature, `SchemaCheckResult`, and every error text stay the same; the only new outcome is "not found" for the default path.

Decision 2, the constant. Remove it and pass `write_mode=False`: the only effect of `write_mode` is the foreign-key pragma, which a read-only check does not need.

Consumer scan (`uv run python tools/scan_change_consumers.py --seed _WORKFLOW_SCHEMA_READ_ONLY`, run in Step 3; candidates only): `scripts/agent/services/workflow_schema.py` (target); `tests/agent/test_repl_health.py` (import site; it imports the function, not the constant, `not affected` for the constant; target for the new tests); `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` (cites the test class, `not affected`); `tools/gen_wflease_procedures.py` (static text, `not affected`: no import); archived issues (`not affected`: history).

No persisted schema, public API, or shared constant of other modules is changed.

## Implementation steps
1. **Phase 1: Failing test first**
   - [ ] Add the default-path missing-database test and record that it fails on the current code (REQ-004; `tests/agent/test_repl_health.py`).
2. **Phase 2: Preflight change**
   - [ ] Resolve the path through `db.DB_PATH`, return not-found before `open`, remove the constant, and open with `write_mode=False` (REQ-001, REQ-002, REQ-003; `scripts/agent/services/workflow_schema.py`).
3. **Phase 3: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` change; prerequisite: the change is committed and pushed first, and deploying is the user's decision (approval gate). Run `uv run python tools/check_db_separation.py` and `uv run python tools/generate_reference_table.py --check` (REQ-001; `scripts/agent/services/workflow_schema.py`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/workflow_schema.py` | Unit with a temporary directory | `uv run pytest tests/agent/test_repl_health.py -v` | New test fails before Phase 2, passes after; existing schema tests pass |
| Caller regression | Unit | `uv run pytest tests/agent/test_startup_workflow_preflight.py -v` | All pass |
| Touched Python files | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean, no new errors |
| `scripts/agent/services/` | Security / architecture / DB separation | `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_db_separation.py` | No new findings |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent |
| Reference tables | Generated-doc drift | `uv run python tools/generate_reference_table.py --check` | Exit 0 |

Baseline (Step 5): `radon cc` reports `check_workflow_schema` at C (12), and the change MUST add no branch beyond the moved guard; `vulture` and `bandit` show no finding in the target file; diff-cover is recorded at implementation time.

## Risks
- **Risk**: A test patches the wrong module and touches the real workflow database → **Mitigation**: patch `db.helper.build_db_config` to a temporary directory and assert the directory is empty; the Issue's constraint to use a temporary directory is a test requirement.
- **Risk**: A caller depends on the default-path preflight creating the database → **Mitigation**: the only caller treats an invalid result as a startup failure, and `create_workflow_schema` handles a missing file itself (Step 2 evidence).
- **Risk**: Complexity of `check_workflow_schema` (grade C) grows → **Mitigation**: the guard is moved, not added to.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: failing default-path missing-database test | Pending | — | — | |
| 2 | Phase 2: existence guard on the resolved path and constant removal | Pending | — | — | |
| 3 | Phase 3: deployment hand-off and verification | Pending | — | — | |

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
- **Source issue**: issues/20261031-135607_wfschema001_schema-preflight-creates-database.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-103600
- **Related target files**: scripts/agent/services/workflow_schema.py, tests/agent/test_repl_health.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullets 1-2; `check_workflow_schema` guard | scripts/agent/services/workflow_schema.py | 2 | AC-1, AC-2 | New default-path test; explicit-path test | Confirmed by repository evidence |
| REQ-002 | Constraints bullet 1; Acceptance Criteria bullets 2-3 | scripts/agent/services/workflow_schema.py | 2 | AC-3 | Existing valid, table, column, and version tests | Explicit in issue |
| REQ-003 | Required Changes bullet 3 | scripts/agent/services/workflow_schema.py | 2 | AC-4 | `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` | Explicit in issue |
| REQ-004 | Required Changes bullet 4; Constraints bullet 4 | tests/agent/test_repl_health.py | 1 | AC-1, AC-5 | New default-path test | Explicit in issue |
