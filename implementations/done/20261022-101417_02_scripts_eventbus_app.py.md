## Goal
Remove the legacy offset import call, its `try`/log block, and the import from the EventBus lifespan (REQ-001).

## Scope
- The import name in `from eventbus.db import ...` and the comment, `try`, call, and `except` log in `lifespan()`.

## Assumptions
- The call sits between `_populate_token_maps(...)` and `app.state.envelope_schema = ...` and nothing else depends on its side effects (verified in `lifespan`).
- The `offsets_dir` config value stays and is simply no longer read at startup.

## Design decisions
- Remove the whole block including the explanatory comment; do not add a replacement log line.

## Alternatives considered
N/A: removal required by the Plan.

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. Change `from eventbus.db import get_db_lock, migrate_legacy_offsets, open_db` to import only `get_db_lock` and `open_db`.
2. Delete the comment, the `try:` block calling `migrate_legacy_offsets(app.state.db, app.state.config.offsets_dir)`, and its `except Exception:` handler that logs "failed to migrate legacy offsets".

### Method
- Apply before deleting `offset_migrator.py`; re-run `ruff` for unused names.

### Details
- Keep every other statement of `lifespan()` in order.

## Compatibility considerations
The service no longer reads `offsets_dir` at start; existing files are ignored and not modified.

## Security considerations
N/A: removes a startup file-reading path and a broad exception handler.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_startup.py tests/eventbus/test_eventbus_restart_resume.py tests/eventbus/test_eventbus_offsets.py -q`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- `lifespan()` has no reference to the import; startup with an empty or non-empty `offsets_dir` succeeds and leaves files untouched.

## Out of Scope
- Offset storage, resume computation, and configuration keys.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the import and the startup call block | Completed | 20261022-114123 | 20261022-114123 | Changed: scripts/eventbus/app.py |
| 2 | Tests are covered by the test-file procedure | Completed | 20261022-114123 | 20261022-114123 | validated; full suite 9686 passed, 14 skipped; ruff, mypy, lint-imports, check_module_size pass; offset, resume, startup tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261022-114123 | 20261022-114123 | validated; full suite 9686 passed, 14 skipped; ruff, mypy, lint-imports, check_module_size pass; offset, resume, startup tests pass |

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
- **Requirement ID**: `REQ-001` (remove the startup call)
- **Source issue**: `issues/20261021-102244_rmoffimp_remove-the-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101417
- **Related target files**: scripts/eventbus/app.py