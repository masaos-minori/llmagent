## Goal
- Add the EventBus-owned database tool (REQ-002): create-or-validate, rotate, verify, path, and version entry points that read the database path only from the EventBus configuration file.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, Phase 1 of the Plan.
- Not in scope: any other file; a second file needed here is an additional-target discovery.
- Execution order follows the Plan's phases, not `seq`: Phase 1 (documents 03, 04), Phase 2 (05, 18), Phase 3 (the `scripts/db`, `scripts/shared`, validator, config, and test documents, one release unit), Phase 4 (01, 38, 39), Phase 5 (the document rows), Phase 6 verification.

## Assumptions
- Overlap with plans 003, 004, 005, 006 (judged in the Plan's Assumptions): sequencing or different keys; no contradiction on this file.
- The Plan's Step 3a corrections apply (EventBus tool reads `db_path` with its own reader; `eventbus_schema_version` and the DDL text accessor move to `scripts/eventbus/db_tools.py`).

## Design decisions
- The tool is operator and deploy tooling, not part of the service request path.
- Reuse `open_db`/`_init_schema` instead of a second creator: one create-or-validate implementation.

## Alternatives considered
N/A: the ownership decision (EventBus-side tooling, maintainer 2026-11-10) is fixed in the Plan's Design section.

## Implementation
### Target file
`scripts/eventbus/db_tools.py` (new)

### Procedure
1. Create `scripts/eventbus/db_tools.py` with a module docstring, `logger`, and these functions (all new): `read_db_path` (new), `schema_sql` (new), `schema_version` (new), `ensure` (new), `rotate` (new), `verify` (new), `main` (new), plus the `if __name__ == "__main__":` guard.
2. `read_db_path` (new): parse the file `get_config_path()` (from `eventbus.config`) with `tomllib`, return `Path(data["db_path"])`; raise `ValueError` when the file is missing, unparsable, or `db_path` is absent or not a non-empty string. It must not call `load_config` (that resolves token references and rejects an empty `auth_token`; `deploy/init_db.sh` sets no EventBus token variables).
3. `schema_sql`: return the text of `scripts/eventbus/schema.sql` (reuse `eventbus.schema._SCHEMA_PATH`); `schema_version`: return `eventbus.schema._expected_schema_version(schema_sql())`.
4. `ensure(db_path=None)`: resolve the path (the configured one by default), `mkdir(parents=True, exist_ok=True)` its parent, then `open_db(str(path)).close()` from `eventbus.db_conn` so the existing create-or-validate semantics apply (fresh file gets the DDL; a current one is fingerprint-validated; any other database raises `RuntimeError` and is left unchanged).
5. `verify(db_path=None)`: open the file read-only (`sqlite3.connect(f"file:{path}?mode=ro", uri=True)`), require `PRAGMA integrity_check` to return `ok`, then `assert_matches(conn, label=str(path))` from `shared.eventbus_schema_fingerprint`; raise `RuntimeError` on any failure.
6. `rotate(archive_dir=None)`: require the file to exist (`FileNotFoundError` otherwise), default `archive_dir` to `<db parent>/archive`, create it, write `<stem>_<UTC YYYYMMDD_HHMMSS><suffix>` with the SQLite backup API (`src.backup(dst)`), run the `verify` checks on the copy, return the archive path; a failing copy is left in place (same forensic rule as `scripts/db/rotation.py`).
7. `main(argv)`: argparse subcommands `ensure`, `verify`, `rotate [--archive-dir DIR]`, `path` (print the configured path), `version` (print `schema_version()`); exit code 1 with the message on stderr for any raised error.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- Imports allowed by `.importlinter`: standard library, `eventbus.*`, `shared.eventbus_schema_fingerprint`; no `db` or `agent` import (contract `eventbus-is-isolated`).
- `eventbus.config.get_config_path` honors `EVENTBUS_CONFIG_PATH`, which `deploy/init_db.sh` and the test isolation set.
- Plan 005 later replaces `shared.eventbus_schema_fingerprint` with `shared.schema_fingerprint`; keep the import in one line so that change is mechanical (recorded as a Plan 005 fallout row).

## Compatibility considerations
- New module; no existing caller. The default archive directory (`<db parent>/archive`) matches the `/opt/llm/db/archive` fallback `scripts/db/rotation.py` uses; an operator whose `sqlite_archive_dir` differs passes `--archive-dir`.

## Security considerations
- No authentication or authorization behavior changes; the EventBus path and schema checks stay fail-closed.

## Rollback considerations
N/A: delete the new file (no caller until Phase 2).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_db_tools.py -v` (document 04).
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`, `uv run bandit scripts/eventbus/db_tools.py -c pyproject.toml`.

## Completion criteria
- The five subcommands work against a temporary database and a temporary `eventbus.toml`; `lint-imports` reports all contracts kept.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/eventbus/db_tools.py` with the path reader, DDL and version accessors, and the ensure, rotate, verify, and main entry points | Completed | 20261110-122422 | 20261110-122422 | Added path and version subcommands; ensure() reuses open_db, which sets WAL before validation (same as service start); coverage 96%. |
| 2 | Add the tests of document 04 | Completed | 20261110-122422 | 20261110-122422 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-122422 | 20261110-122422 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261109-112538_adrrev002_agent-eventbus-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-102050
- **Related target files**: `scripts/eventbus/db_tools.py`