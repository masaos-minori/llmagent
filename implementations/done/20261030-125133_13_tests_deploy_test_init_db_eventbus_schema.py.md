## Goal

Keep `tests/deploy/test_init_db_eventbus_schema.py` from reaching the production workflow database by pinning `workflow_db_path` at the top level of the sandbox `agent.toml` (`REQ-004`, the migration release must not make a test depend on production state).

## Scope

- Modify only `tests/deploy/test_init_db_eventbus_schema.py` (`_write_config`).
- Plan amendment (user-approved 2026-10-30): row appended after the registry row as an additional target file discovery.

## Assumptions

- Verified (Step 3a): `_write_config` copies `config/` into the sandbox, rewrites `/opt/llm/db/` paths, and appends `workflow_db_path = ...` to `agent.toml`; `config/agent.toml` ends inside a table (`[tool_definitions.function.parameters.properties.context_after]`, `:1964`), so the appended key is a table member, `build_db_config()` reads `cfg.get("workflow_db_path", "/opt/llm/db/workflow.sqlite")` at the top level, and the `create_schema.py` subprocess falls back to the production path.
- Evidence of the defect: with `WORKFLOW_SCHEMA_VERSION` `1.2.0`, `test_init_db_canonical_passes` fails with `workflow.sqlite schema version '1.1.0' differs from '1.2.0'` (the production database's version), and the production file gained a `schema_migrations` table and a baseline row from earlier full-suite runs (read-only inspection, 2026-10-30). The production database is not modified by this row.
- `eventbus_db_path` is already a top-level key rewritten by the path substitution, so only the workflow key needs the fix.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- Put the key before the first table header: write `workflow_db_path = "..."` as the first line of the copied `agent.toml` (TOML requires top-level keys before any table).

## Alternatives considered

- Rewrite an existing key by text substitution: rejected, `agent.toml` has no `workflow_db_path` key to rewrite.

## Implementation

### Target file

`tests/deploy/test_init_db_eventbus_schema.py`

### Procedure

1. In `_write_config`, replace the `agent_toml.open("a")` append with reading the file and writing it back with the `workflow_db_path` line prepended; update the comment to say why it must be top-level.

### Method

- Keep the explicit `encoding="utf-8"` used in the neighbouring lines.

### Details

- The sandbox now reaches only `db_dir`; the test no longer reads or writes `/opt/llm`.

## Compatibility considerations

- Test-only change; behavior of `init_db.sh` is untouched.

## Security considerations

- Closes a production-write path from the test suite: no new surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/deploy/test_init_db_eventbus_schema.py -v`
- `uv run ruff check tests/deploy/test_init_db_eventbus_schema.py`
- Compare the mtime and `PRAGMA user_version`-independent content of `/opt/llm/db/workflow.sqlite` before and after the run: read-only (`stat`), no change expected.

## Completion criteria

- The three deploy tests pass with the sandbox workflow database, and the production file's mtime does not change during the run.

## Out of Scope

- Any change to `init_db.sh` or to the production database.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pin the key at the top level | Completed | 20261030-173958 | 20261030-173958 | Plan Phase 3; with row 04 agent.toml key prepended; production DB untouched |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-173958 | 20261030-173958 | validators passed; full suite 10487 passed (wftaskapi001 release unit run); production workflow.sqlite mtime unchanged |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125133
- **Related target files**: tests/deploy/test_init_db_eventbus_schema.py