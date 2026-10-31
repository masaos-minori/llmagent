# Workflow schema preflight creates an empty database when it is missing

## Priority
Medium

## Summary
The startup workflow-schema preflight (`check_workflow_schema`) is meant to be a read-only check. When it is called without a path, as `ComponentInitializer._check_workflow_schema` does, its "database exists" guard is skipped and the connection is opened through `sqlite3.connect`, which creates the file. A missing workflow database is therefore silently created empty, and the check then reports a missing table instead of a missing database. The module constant that is meant to request read-only access is also passed as `write_mode`. Make the preflight inspect without creating anything and report the real condition.

## Background
Found during an adversarial review (`python-code-review`) of the agent startup path.
- The comment in `check_workflow_schema` says the existence check exists because `sqlite3.connect()` creates files automatically, but the guard is written as `if db_path and not os.path.exists(db_path)`, so it only runs when a path is passed explicitly.
- The production call passes no path, so the default workflow database path is resolved by `SQLiteHelper`.
- The module constant `_WORKFLOW_SCHEMA_READ_ONLY` is `True` and is passed as the `write_mode` argument of `SQLiteHelper.open`. For `SQLiteHelper`, `write_mode` selects the foreign-key pragma, so the name and the use disagree.
- Related archived work on the workflow preflight: `issues/done/20261008-150558_wfpreflight01_validate-the-workflow-definition-content-in-the-startup-preflight.md` (definition content, not the database side effect).

## Problem
Reproduction (throwaway script, not committed): `SQLiteHelper` redirected to a path inside a fresh temporary directory, then `check_workflow_schema(db_path=None)` with the database absent. Observed: the file did not exist before and existed afterward (4096 bytes); the result was invalid with the error "Workflow schema missing table 'tasks'. Run create_workflow_schema() to initialize."

Consequences:
- A check that is documented as a preflight changes state: an empty database file appears at the production path.
- The reported cause is wrong. The operator is told a table is missing in a database that did not exist.
- Deployment tooling that decides between "create" and "keep" by file presence may see an unexpected empty file. How `deploy/init_db.sh` and the schema creation function treat a pre-existing empty file was not verified.

## Reason for Change
A startup preflight must not modify the system it checks, and its error message must identify the actual failure so that the operator runs the right remediation. The mismatch between the constant name and its use also invites a wrong fix later.

## Implementation Intent
Apply the existence check to the resolved database path (including the default path) before any connection is opened, and report a distinct "database not found" error. Open the database in a way that cannot create it, if the helper supports that, or keep the guard as the safeguard. Rename or remove the misleading constant so that the argument it feeds matches its name. Keep the table, column, and version checks as they are.

## Target Files or Areas
- `scripts/agent/services/workflow_schema.py` (`check_workflow_schema`, `_WORKFLOW_SCHEMA_READ_ONLY`)
- `scripts/db/helper.py` (`SQLiteHelper`, only if a no-create open mode is needed)
- `scripts/agent/startup_component_init.py` (`ComponentInitializer._check_workflow_schema`, caller)
- `tests/agent/test_startup_workflow_preflight.py`, `tests/agent/test_repl_health.py`

## Required Changes
- Resolve the database path first and fail with a "not found" result when the file does not exist, for both the explicit-path and default-path cases.
- Ensure the preflight never creates the database file or its WAL/SHM side files.
- Fix the constant so its name matches how it is used (or stop passing it as `write_mode`).
- Add tests: missing database yields the not-found error and creates no files; an existing valid database still passes; an existing database with a missing table still reports that table.

## Constraints
- Do not change the required-table, column, and schema-version rules.
- Do not change the database ownership or path configuration (4DB separation).
- Do not add schema creation or migration to the preflight.
- Tests must use a temporary directory and must not touch the real workflow database.

## Acceptance Criteria
- With the workflow database absent, the preflight reports a not-found error and no file is created at that path.
- With a valid database present, the preflight passes as before.
- With a database missing a required table, the error names that table as before.
- No constant name contradicts its use.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests in `tests/agent/test_startup_workflow_preflight.py` using a temporary database path.
- Run `tests/agent/test_startup_workflow_preflight.py`, `tests/agent/test_repl_health.py`, `tools/check_db_separation.py`, `ruff`, and `mypy --no-namespace-packages` on the touched files.

## Documentation Impact
Needs confirmation: check whether the startup or deployment documentation describes the preflight message for a missing workflow database. If it does, align it with the new not-found message and state that the preflight does not create the database.

## Out of Scope
- Schema creation, migration, and the deploy scripts.
- Other databases' startup checks.
- The workflow definition preflight.

## Dependencies
N/A: none. No open issue or in-flight plan targets `scripts/agent/services/workflow_schema.py` for this behavior.

## Unresolved Questions
- How `deploy/init_db.sh` and `create_workflow_schema()` behave when an empty database file already exists: `Needs confirmation`. This decides whether the side effect can cause a real deployment problem or only a misleading message.
- Whether `SQLiteHelper` should offer a read-only or no-create open mode, or whether the existence guard is enough: left to the implementer.

## AI Implementation Instruction
Change only the preflight's existence handling and the misleading constant, plus tests. Do not alter the schema rules or the database configuration. Use a temporary directory for every test database. Stop and report if the fix would require changing `SQLiteHelper` behavior used by other databases.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-135607
- **Related target files**: scripts/agent/services/workflow_schema.py, scripts/db/helper.py, scripts/agent/startup_component_init.py, tests/agent/test_startup_workflow_preflight.py, tests/agent/test_repl_health.py
