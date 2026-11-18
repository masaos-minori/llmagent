## Goal

Create `tests/db/test_db_config.py` — regression coverage that `build_db_config()`
reads the `workflow_db_path` key from the repo `config/agent.toml` and that only one
code default literal remains. (`REQ-003` key read-back, `REQ-004` single default)

## Scope
**Release unit**: WORKFLOW-CONFIG (created red in Phase 1 per the Plan's step 1, but it
goes green only with the WORKFLOW-CONFIG commit — its assertions are about procedures
03/04, not FK-ENFORCE)

## Assumptions

- Phase 1 writes this file against today's `config.py`; the failure (missing key /
  duplicate literal) is recorded as red evidence in the Plan Execution Status, same
  convention as procedure 06.
- The test reads the repository `config/agent.toml` (repo-root-relative path), not a
  synthetic copy.

## Design decisions

- Source-literal assertion counts occurrences of `"/opt/llm/db/workflow.sqlite"` in
  `scripts/db/config.py` text (grep-style source assertion, mirroring the style
  already used in `tests/tools/test_check_docs_consistency_checks.py:53`) — this is
  how AC-2's "exactly one literal" becomes checkable.

## Alternatives considered

- **Assert only behavior (default fallback works).** Rejected: behavior alone cannot
  detect the duplicate literal the plan eliminates.

## Implementation
### Target file
`tests/db/test_db_config.py` (new)

### Procedure
1. `test_build_db_config_reads_workflow_path_from_agent_toml (new)`: call
   `build_db_config()` with the repo `config/agent.toml` and assert
   `DbConfig.workflow_db_path` equals the agent.toml value.
2. `test_single_default_literal (new)`: assert the literal
   `"/opt/llm/db/workflow.sqlite"` appears exactly once in `scripts/db/config.py`
   (the `DbConfig` field default).

### Method
Load the toml with `tomllib` for the value comparison; read the `config.py` source as
text for the count assertion. No monkeypatching of the default.

### Details

- Tests import from `scripts/db` the same way existing `tests/db/` modules do.

## Compatibility considerations

- Tests only; no production import graph impact.

## Security considerations

- N/A: test-only file.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_db_config.py -q` — red before procedures 03/04, green
  after (AC-2).
- `uv run ruff check tests/db/test_db_config.py`.

## Completion criteria

- Both tests green after the WORKFLOW-CONFIG commit; read-back equals the agent.toml
  value and the literal count is 1 (AC-2).

## Out of Scope

- `rag_db_path`/`session_db_path` read-back (already covered elsewhere).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the two config tests (red-first run recorded) | Completed | — | — | red-first evidence 2026-11-18: repo agent.toml has no workflow_db_path key; literal count == 2 (both tests red before procedures 03/04) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-18 | 2026-11-18 | green after procedures 03/04: repo agent.toml key present, build_db_config reads it, single literal |

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
- **Requirement ID**: `REQ-003` (key read-back), `REQ-004` (single code default)
- **Source issue**: issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-155712_adrchk019_mdq-workflow-db-settings.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162732
- **Related target files**: `tests/db/test_db_config.py`