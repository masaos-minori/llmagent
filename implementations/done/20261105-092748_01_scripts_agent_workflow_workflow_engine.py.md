## Goal
- Stop `WorkflowEngine` from reaching into the store's private `_db`, and expose the workflow version publicly so the adapter can stop reading `_wdef` (`REQ-001`: use `get_connection()`; `REQ-002`: public `version` property; `REQ-005`: its unit test).

## Scope
**Release unit**: N/A: not part of a release unit
- Edits `scripts/agent/workflow/workflow_engine.py`; adds one test to the companion `tests/agent/workflow/test_workflow_engine.py`.
- The adapter and the orchestrator tests are handled by procedures `_02`, `_04`, `_05`.

## Assumptions
- `StateStore.get_connection()` returns the same `SQLiteHelper` as `_db`, so SQL, transactions, and results are identical.
- Tests assign `engine._wdef = ...` directly in several places; the property reads `self._wdef`, so they keep working.
- Overlap with `plans/20261104-115736_partialcount001_partial-completion-counter-dead.md` is limited to `tests/agent/test_orchestrator.py` and does not touch this file.

## Design decisions
- Use `get_connection()` at both call sites rather than new `StateStore` wrapper methods: smaller diff, no new public API on the store, and `get_connection()` is the documented handle for transaction-level helpers.
- The `version` property is read-only and returns `self._wdef.version`; the engine keeps `_wdef` private for its own use.

## Alternatives considered
- `StateStore.begin_stage_if_new` / `record_artifact` wrappers: rejected for now (more public surface; the helpers still need the same handle).
- A `version` attribute on `WorkflowDef` only: it already exists, but the adapter has no `WorkflowDef` reference, only the engine.

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`

### Procedure
1. Add a read-only property `version` (new) on `WorkflowEngine`, placed after `__init__`, returning `self._wdef.version` with a one-line docstring and a `str` return annotation.
2. In the stage runner, replace the first argument `self._store._db` of the `begin_stage_if_new(...)` call with `self._store.get_connection()`.
3. In the same method, replace the first argument `self._store._db` of the `record_artifact(...)` call with `self._store.get_connection()`.

### Method
- Change only those two arguments; keep every other argument and the surrounding control flow.
- `self._wdef` uses inside the engine stay.

### Details
- After the edit `rg "_store\._db" scripts/agent/workflow/workflow_engine.py` must find nothing.

### Companion test files
- `tests/agent/workflow/test_workflow_engine.py`
  - Procedure: add a module-level test `test_engine_exposes_definition_version` (new) next to the engine construction tests, using the existing `store` fixture and `_make_wdef`: `wdef = _make_wdef()`, `engine = WorkflowEngine(wdef, store)`, assert `engine.version == wdef.version`.
  - Validation: run it first and confirm it fails with an `AttributeError` on the current code, then passes after the property is added; `uv run pytest tests/agent/workflow/test_workflow_engine.py -v` passes entirely.

## Compatibility considerations
- Purely additive public property; SQL and behavior are unchanged. No caller outside the adapter uses it yet.
- `Orchestrator`, `workflow/__init__.py`, and the tests that construct `WorkflowEngine` are unaffected.

## Security considerations
- N/A: no input handling, secrets, or trust boundary involved.

## Rollback considerations
- Revert the commit; the adapter procedure (`_02`) must be reverted with it if already applied, because it depends on the property.

## Validation plan
- `uv run pytest tests/agent/workflow`.
- `uv run ruff check scripts/agent/workflow/workflow_engine.py tests/agent/workflow/test_workflow_engine.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `uv run python tools/check_module_size.py`; `uv run python tools/generate_reference_table.py --check`.

## Completion criteria
- Neither `begin_stage_if_new` nor `record_artifact` receives `self._store._db`; `WorkflowEngine.version` returns the definition version; the whole `tests/agent/workflow` suite passes.

## Out of Scope
- New `StateStore` wrappers, the adapter, and test files other than the companion.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the failing `version` test to the companion file | Completed | 20261105-132311 | 20261105-132311 | Failed with AttributeError on current code; passes after the property. |
| 2 | Add the `version` property and switch both call sites to `get_connection()` | Completed | 20261105-132311 | 20261105-132311 | No `_store._db` reference remains in the engine. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261105-132311 | 20261105-132311 | ruff/mypy/lint-imports/bandit/module-size/reference-table all clean; 154 workflow tests pass. |

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
- **Requirement ID**: `REQ-001` (use `get_connection()`), `REQ-002` (public `version`), `REQ-005` (property test)
- **Source issue**: issues/20261103-134147_wfreview004_workflow-adapter-and-engine-private-attribute-access.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-085959_wfreview004_workflow-adapter-and-engine-private-attribute-access.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092748
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `tests/agent/workflow/test_workflow_engine.py`