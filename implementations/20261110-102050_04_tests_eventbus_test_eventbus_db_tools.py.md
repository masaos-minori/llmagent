## Goal
- Test the EventBus-side tool against temporary databases and configuration files (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, Phase 1 of the Plan.
- Not in scope: any other file; a second file needed here is an additional-target discovery.
- Execution order follows the Plan's phases, not `seq`: Phase 1 (documents 03, 04), Phase 2 (05, 18), Phase 3 (the `scripts/db`, `scripts/shared`, validator, config, and test documents, one release unit), Phase 4 (01, 38, 39), Phase 5 (the document rows), Phase 6 verification.

## Assumptions
- Overlap with plans 003, 004, 005, 006 (judged in the Plan's Assumptions): sequencing or different keys; no contradiction on this file.
- The Plan's Step 3a corrections apply (EventBus tool reads `db_path` with its own reader; `eventbus_schema_version` and the DDL text accessor move to `scripts/eventbus/db_tools.py`).

## Design decisions
- Remove only what the Plan names for this file; keep every other behavior unchanged.

## Alternatives considered
N/A: the ownership decision (EventBus-side tooling, maintainer 2026-11-10) is fixed in the Plan's Design section.

## Implementation
### Target file
`tests/eventbus/test_eventbus_db_tools.py` (new)

### Procedure
1. Create the test module with a fixture that writes a minimal `eventbus.toml` (`db_path` pointing into `tmp_path`) and sets `EVENTBUS_CONFIG_PATH` with `monkeypatch`.
2. `test_read_db_path_uses_eventbus_config_only` (new): the path comes from the toml; an `agent.toml` value in the environment is not consulted; an empty or missing `db_path` raises `ValueError`; no token variable is needed.
3. `test_ensure_creates_fresh_database_and_accepts_current` (new): `ensure()` creates the file with the canonical schema, a second call succeeds without writing.
4. `test_ensure_refuses_stale_unstamped_and_malformed_database` (new): an old-version file, a `user_version 0` file, and a version-matching file with a changed shape each raise `RuntimeError` and stay byte-identical.
5. `test_rotate_writes_verified_archive` (new): `rotate(tmp_path / "arch")` returns a path whose name starts with the db stem, which passes `verify`; a missing source raises `FileNotFoundError`.
6. `test_verify_rejects_integrity_and_shape_failures` (new) and `test_cli_path_and_version` (new): `main(["path"])` prints the configured path; `main(["version"])` prints `schema_version()`.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- Mirror the existing patterns: `tests/db/test_create_schema.py` (eventbus creation cases, moved here by Phase 3) and `tests/db/test_db_maintenance.py::test_rotate_eventbus_db_happy_path`.
- Build stale files with `sqlite3` directly and `PRAGMA user_version`; no `/opt/llm` access (the `tests/conftest.py` isolation applies).

## Compatibility considerations
N/A: test code only.

## Security considerations
N/A: test code only; no credentials involved.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_db_tools.py -v`.
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- All listed tests pass; each Agent-side eventbus creation, rotation, and refusal case that Phase 3 removes has a counterpart here.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/eventbus/test_eventbus_db_tools.py` with the path, ensure, refusal, rotate, verify, and CLI tests | Pending | — | — | |
| 2 | Run `uv run pytest tests/eventbus/test_eventbus_db_tools.py -v` and the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `tests/eventbus/test_eventbus_db_tools.py`
