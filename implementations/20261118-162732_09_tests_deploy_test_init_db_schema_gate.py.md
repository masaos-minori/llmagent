## Goal

Remove the `workflow_db_path` key-pinning insertion from
`tests/deploy/test_init_db_schema_gate.py::_write_config()` — with the repo
`config/agent.toml` carrying the key, the insertion produces a duplicate top-level TOML
key and the gate fails to parse. (`REQ-007` deploy-gate consistency; plan scope
amendment S2)

## Scope
**Release unit**: WORKFLOW-CONFIG

## Assumptions

- The gate's existing whole-file rewrite `agent.read_text(...).replace("/opt/llm/db/", f"{db_dir}/")` (`:183`) already re-points the new repo key into the sandbox — no replacement pinning is introduced (plan Design).
- Must land in the same commit as `config/agent.toml` (procedure 03): key without the
  gate fix = duplicate key parse error.

## Design decisions

- Delete the pinning logic entirely (`:184-191` loop/insert and the docstring passage
  at `:175-178`); keep every gate assertion unchanged.

## Alternatives considered

- **Keep the insertion but skip it when the key exists.** Rejected: tolerant-fallback
  shape the issue prohibits (no shims / no history-style code).

## Implementation
### Target file
`tests/deploy/test_init_db_schema_gate.py`

### Procedure
1. In `_write_config()`, delete the `lines = text.split("\n")` / `lines.insert(...)`
   block (`:184-191`); the file content after the `:183` rewrite is written back
   directly.
2. Update the function docstring (`:172-179`): drop the "workflow_db_path is absent
   from agent.toml ... inserted as a top-level key" passage.

### Method
`rg workflow_db_path tests/deploy/test_init_db_schema_gate.py` should find nothing
after the edit; gate behavior verified by running the gate itself.

### Details
The `eventbus.toml` rewrite block (`:192-198`) stays untouched.

## Compatibility considerations

- Gate assertions (schema fingerprint refusal, table inventory) unchanged — only the
  sandbox config preparation changes.

## Security considerations

- N/A: test fixture change.

## Rollback considerations

- N/A: revert the commit (WORKFLOW-CONFIG unit).

## Validation plan

- `uv run pytest tests/deploy/test_init_db_schema_gate.py -m "not integration and not production_paths_allowed and not repo_scan" -q` — gate green with the repo key present (AC-3).

## Completion criteria

- The gate passes with `config/agent.toml` carrying `workflow_db_path`; no pinned
  insertion remains (AC-3).

## Out of Scope

- `tests/deploy/test_init_db_eventbus_schema.py` (procedure 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drop the pinning insertion and update the docstring | Completed | 2026-11-18 | 2026-11-18 |  |
| 2 | Run the gate test (validation) | Completed | 2026-11-18 | 2026-11-18 |  |

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
- **Requirement ID**: `REQ-007` (deploy gates consistent with the new key)
- **Source issue**: issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-155712_adrchk019_mdq-workflow-db-settings.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162732
- **Related target files**: `tests/deploy/test_init_db_schema_gate.py`