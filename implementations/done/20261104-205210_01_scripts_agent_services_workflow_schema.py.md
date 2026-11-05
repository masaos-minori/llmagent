## Goal
Make `check_workflow_schema` stop creating a missing workflow database at the resolved
(default) path: check `db.DB_PATH` existence before `open`, return the existing
"Workflow DB not found" result, and remove the misleading `_WORKFLOW_SCHEMA_READ_ONLY`
constant (Plan REQ-001, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Opening an already-existing database still applies `PRAGMA journal_mode=WAL` through
  `SQLiteHelper.open`; unchanged behavior (Plan Assumptions).
- A failed database-config build still raises `RuntimeError` from the `SQLiteHelper`
  constructor instead of returning a result; out of scope (Plan Assumptions).
- A file removed between the existence check and the open is not handled specially
  (Plan Assumptions).
- Open issues `issues/20261103-134147_wfreview001_workflow-diagnostics-empty-session-id.md`
  and `issues/20261103-134147_wfreview003_workflow-loader-bare-int-coercion.md` reference
  `scripts/agent/services/workflow_schema.py` only in adjacent regions (`REQUIRED_WORKFLOW_TABLES`
  column retention; `check_workflow_definition` exception wrapping); this document changes
  neither — compatible (Step 3a check).
- No overlap candidate from `tools/check_plan_target_overlaps.py` names this Plan.

## Design decisions
- Move the existence guard to the resolved path `db.DB_PATH` before `open`; no
  `SQLiteHelper` change (Plan Decision 1).
- Remove `_WORKFLOW_SCHEMA_READ_ONLY` and pass `write_mode=False`: `write_mode` only
  selects the foreign-keys pragma, which a read-only check does not need (Plan Decision 2).

## Alternatives considered
N/A: adding a no-create open mode to `SQLiteHelper` was rejected in Plan Decision 1 — it
would change a shared helper used by other databases.

## Implementation
### Target file
`scripts/agent/services/workflow_schema.py`
### Procedure
1. In `check_workflow_schema`, replace the guard `if db_path and not os.path.exists(db_path)`
   with an existence check on `db.DB_PATH` after `SQLiteHelper` construction and before
   `db.open`; on a missing file return `SchemaCheckResult(valid=False, error=f"Workflow DB not found: {db.DB_PATH}")`
   (REQ-001).
2. Delete the module constant `_WORKFLOW_SCHEMA_READ_ONLY` and call
   `db.open(write_mode=False, row_factory=False)` (REQ-003).
### Method
Single-function change inside `check_workflow_schema` plus deletion of one module constant.
Function signature, `SchemaCheckResult`, and every existing error text stay identical.
No other file is modified except the companion test file.
### Details
- The current guard tests the `db_path` argument only, so it is skipped when
  `ComponentInitializer._check_workflow_schema` calls `check_workflow_schema()` with no
  argument; `SQLiteHelper` then resolves `workflow_db_path` through `build_db_config` and
  `sqlite3.connect` inside `open` creates the file. `SQLiteHelper.DB_PATH` returns the
  resolved path for both explicit and default targets, so the guard covers both cases with
  the same message format — the explicit-path test stays green (REQ-002, AC-2).
- The guard move must not add a branch beyond the moved one: `check_workflow_schema` is
  radon complexity 12 (grade C) at baseline; dropping the `db_path and` operand from the
  guard condition lowers it to 11, still grade C.
- `write_mode=False` is already `SQLiteHelper.open`'s default value; pass it explicitly per
  REQ-003 so no constant name contradicts its use.

### Companion test files
- `tests/agent/test_repl_health.py`
  - Procedure: in `TestCheckWorkflowSchema`, add a default-path missing-database test that
    patches `db.helper.build_db_config` (via `monkeypatch.setattr`; the name is imported
    into `db.helper` from `db.config` and looked up there by `SQLiteHelper.__init__`) to
    return a `DbConfig` (new import `from db.config import DbConfig`) whose
    `workflow_db_path` is a file absent inside `tmp_path`, calls `check_workflow_schema()`
    with no argument, and asserts `valid is False`, the error contains `Workflow DB not
    found`, and `tmp_path` contains no files afterwards; land this test before the
    target-file change and record that it fails on the pre-change code (REQ-004, AC-5).
  - Validation: `uv run pytest tests/agent/test_repl_health.py -v` — the new test fails
    before the target-file change and passes after it; every existing
    `TestCheckWorkflowSchema` test stays green; `uv run python tools/check_mock_patch_targets.py`
    reports no finding on the new patch.

## Compatibility considerations
The caller `ComponentInitializer._check_workflow_schema` treats any invalid result as a
startup failure and passes the new message through unchanged (`tools/scan_change_consumers.py`
candidate list in the Plan re-verified in Step 3a). `tests/agent/test_startup_workflow_preflight.py`
mocks `check_workflow_schema` at the caller and stays valid. No persisted schema, config key,
or public API changes.

## Security considerations
N/A: no trust boundary, input path, or secret handling changes.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Companion test file | Unit, temporary directory, patched config | `uv run pytest tests/agent/test_repl_health.py -v` | New test fails before the target-file change, passes after; existing schema tests pass |
| Caller regression | Unit | `uv run pytest tests/agent/test_startup_workflow_preflight.py -v` | All pass |
| Touched Python files | Static | `uv run ruff format scripts/`, `uv run ruff check scripts/ --fix`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean, no new errors |
| `scripts/agent/services/` | Architecture / security / DB separation | `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_db_separation.py` | No new findings |
| `check_workflow_schema` | Complexity baseline | `uv run radon cc scripts/agent/services/workflow_schema.py -s -n C` | Still grade C (12); no new branch |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent |
| Reference tables | Generated-doc drift | `uv run python tools/generate_reference_table.py --check` | Exit 0 |

## Completion criteria
- AC-1: with the workflow database absent and no path argument, the preflight returns the
  not-found error and no file exists at that path or its WAL/SHM side paths.
- AC-2: with an explicit missing path, the existing not-found result is unchanged.
- AC-3: a valid database passes; a missing table or column still names it; the version
  mismatch message is unchanged.
- AC-4: no constant name contradicts its use; the open call passes `write_mode=False`.
- AC-5: the new test fails on the pre-change code and passes after it.

## Out of Scope
- The required-table, column, and schema-version rules and their error messages; the
  database ownership and path configuration (4DB separation); schema creation or migration
  inside the preflight.
- `SQLiteHelper` behavior (including the WAL pragma on an already-existing database), the
  deploy scripts, other databases' startup checks, and `check_workflow_definition`.

## Adversarial Verification Results (20261105-111500)
- Confirmed against current source: the guard is still `if db_path and not
  os.path.exists(db_path)` (workflow_schema.py L85) and only covers explicit paths;
  `ComponentInitializer._check_workflow_schema` (startup_component_init.py L142) calls
  `check_workflow_schema()` with no argument — the default-path creation bug is live.
  `_WORKFLOW_SCHEMA_READ_ONLY` (L61) is defined and used once (L89). `SQLiteHelper.DB_PATH`
  property exists (helper.py L127) and `open` already defaults `write_mode=False`
  (helper.py L186).
- Confirmed test baseline: `TestCheckWorkflowSchema` has no default-path test;
  `test_missing_db_file_returns_error` pins the explicit-path message and stays green. On
  the pre-change code the new test fails twice (error text is the missing-table message;
  `tmp_path` gains the created db file).
- Confirmed baselines: radon `check_workflow_schema` C (12); `check_plan_target_overlaps`
  reports no open-plan overlap on either target file; no other unprocessed procedure
  targets `workflow_schema.py` or `test_repl_health.py`; adjacent wfreview issues touch
  neither region changed here. `DbConfig` exists in `db.config` (L22); `build_db_config` is
  imported into `db.helper` (L19) and looked up there, so the patch target is correct for
  `check_mock_patch_targets`.
- Corrections applied: Details bullet reworded — removing the `db_path and` operand lowers
  radon complexity 12 to 11, still grade C (the doc's "must stay C (12)" implied a frozen
  number); companion-test procedure now names the `monkeypatch.setattr` mechanism and the
  new `from db.config import DbConfig` import.
- Plan status note: the source plan is archived at
  `plans/done/20261104-103600_wfschema001_schema-preflight-creates-database.md` with plan
  steps 1-2 still In Progress; this procedure completes them.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the default-path missing-database test in the companion test file and record it failing on the pre-change code (REQ-004) | Completed | 20261105-112000 | 20261105-112400 | `test_missing_db_default_path_returns_error_without_creating_file` added in `TestCheckWorkflowSchema`; recorded failing on the pre-change code (error text was the missing-table message and the db file was created in tmp_path); 12 existing class tests stayed green |
| 2 | Implement the `db.DB_PATH` existence guard and remove `_WORKFLOW_SCHEMA_READ_ONLY` (REQ-001, REQ-002, REQ-003) | Completed | 20261105-112500 | 20261105-112700 | guard now `if not os.path.exists(db.DB_PATH)` before `open`, message on `db.DB_PATH`; constant deleted; `db.open(write_mode=False, row_factory=False)`; ruff format wrapped the long return line only |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan gates | Completed | 20261105-112800 | 20261105-114500 | targeted 50 passed; full suite 11534 passed / 9 skipped; ruff + mypy clean; lint-imports 6 kept; bandit baseline unchanged (Low 50 / Medium 0 / High 0); check_db_separation, check_mock_patch_targets, check_module_size, check_workitem_structure, generate_reference_table --check all clean; radon `check_workflow_schema` C (11) as predicted in the verification note; diff-cover 100 percent (gate >= 90); no docs/00_index.md task row maps these files to a docs section - no doc update required |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003` (target file), `REQ-004` (companion test file)
- **Source issue**: issues/20261031-135607_wfschema001_schema-preflight-creates-database.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-103600_wfschema001_schema-preflight-creates-database.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-205210
- **Related target files**: `scripts/agent/services/workflow_schema.py`, `tests/agent/test_repl_health.py`
