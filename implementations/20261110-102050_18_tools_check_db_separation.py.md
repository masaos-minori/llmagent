## Goal
- Keep the ADR-008 four-database checks passing without the Agent-side accessors (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, Phase 2 of the Plan.
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
`tools/check_db_separation.py`

### Procedure
1. In `_schema_ddl()` (`check_db_separation.py:118-126`) replace `schema_sql.build_eventbus_schema_sql()` with the text of `scripts/eventbus/schema.sql` (read the file with `Path`, as the tool reads other repository files; the tool is repository tooling and may read it directly).
2. In `check_db_paths()` (`:180-196`) take the eventbus default path from `config/eventbus.toml` `db_path` (parse with `tomllib`) instead of `DbConfig`'s `eventbus_db_path` default, and stop reading an `eventbus_db_path` key from `agent.toml`.
3. Keep the table-ownership, cross-DB FK, distinct-path, and sqlite-vec scope checks.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- The tool also runs in CI (`lint` job) and the pre-deploy check; it must pass both before (Agent-side accessors present) and after Phase 3, so it must not use the removed names.
- It is repository tooling, not a process under ADR-002 (Plan Assumptions).

### Companion test files
- `tests/tools/test_check_db_separation.py`
  - Procedure: Keep the helper `_ddl()` working through the checker's new eventbus DDL source (it uses `mod._schema_ddl()`); adjust only if the dict shape changed.
  - Validation: `uv run pytest tests/tools/test_check_db_separation.py -v`

## Compatibility considerations
- See Details; the removal is intentional and has no shim (`tools/check_compat_shims.py`).

## Security considerations
- No authentication or authorization behavior changes; the EventBus path and schema checks stay fail-closed.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_db_separation.py` and `uv run pytest tests/tools/test_check_db_separation.py -v`.
- `uv run ruff check tools/check_db_separation.py`, `uv run mypy tools/check_db_separation.py`, `uv run bandit tools/check_db_separation.py`, `uv run python tools/check_tool_descriptions_sync.py`.

## Completion criteria
- The tool passes against the live repository and no longer imports the removed accessors.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Switch the eventbus DDL and default-path sources in `tools/check_db_separation.py` | Pending | — | — | |
| 2 | Run `uv run pytest tests/tools/test_check_db_separation.py -v` and the checker itself | Pending | — | — | |
| 3 | Run the tool validation sequence of `routing.md` Tools (ruff, mypy, bandit, tool-description sync) | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261109-112538_adrrev002_agent-eventbus-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-102050
- **Related target files**: `tools/check_db_separation.py`, `tests/tools/test_check_db_separation.py`
