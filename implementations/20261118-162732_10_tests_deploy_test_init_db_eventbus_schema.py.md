## Goal

Remove the pinned `workflow_db_path` prepend from
`tests/deploy/test_init_db_eventbus_schema.py::_write_config()` — with the repo key
present, the prepend creates a duplicate top-level TOML key and the sandbox config
fails to parse. (`REQ-007` deploy-gate consistency; plan scope amendment S2)

## Scope
**Release unit**: WORKFLOW-CONFIG

## Assumptions

- The file's existing whole-file rewrite loop (`cfg_dir.rglob("*.toml")` replace of
  `/opt/llm/db/` at `:102-106`) already runs before the prepend and re-points the new
  repo key into the sandbox — no replacement pinning is introduced (plan Design).
- Lands in the same commit as `config/agent.toml` (procedure 03).

## Design decisions

- Delete the pinning block outright (`:107-115`, including the `agent_toml` variable
  and its explanatory comment); keep every gate assertion unchanged.

## Alternatives considered

- **Conditional prepend.** Rejected: tolerant-fallback shape prohibited by the issue
  constraints.

## Implementation
### Target file
`tests/deploy/test_init_db_eventbus_schema.py`

### Procedure
1. Delete `agent_toml = cfg_dir / "agent.toml"`, the comment block (`:108-113`), the
   `pinned` line and the `write_text(pinned + ...)` prepend (`:114-115`).
2. Leave the rglob rewrite loop (`:102-106`) and `return cfg_dir` as the function body.

### Method
`rg workflow_db_path tests/deploy/test_init_db_eventbus_schema.py` should find nothing
after the edit.

### Details
The comment references the historical `toolexec001 row 06` incident — remove it with
the block (Current-Specification-Only: no history-style comments remain).

## Compatibility considerations

- Gate assertions (EventBus schema refusal paths) unchanged; only sandbox config
  preparation changes.

## Security considerations

- N/A: test fixture change.

## Rollback considerations

- N/A: revert the commit (WORKFLOW-CONFIG unit).

## Validation plan

- `uv run pytest tests/deploy/test_init_db_eventbus_schema.py -m "not integration and not production_paths_allowed and not repo_scan" -q` — gate green with the repo key present (AC-3).

## Completion criteria

- The gate passes with `config/agent.toml` carrying `workflow_db_path`; no prepend
  remains (AC-3).

## Out of Scope

- `tests/deploy/test_init_db_schema_gate.py` (procedure 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drop the pinned prepend and its comment | Pending | — | — | |
| 2 | Run the gate test (validation) | Pending | — | — | |

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
- **Related target files**: `tests/deploy/test_init_db_eventbus_schema.py`
