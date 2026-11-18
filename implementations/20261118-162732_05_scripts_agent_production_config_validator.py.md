## Goal

Register `"workflow_db_path"` in the subsystem-keys allowlist of
`scripts/agent/production_config_validator.py` so `_check_unknown_production_keys`
accepts the new agent.toml key instead of aborting Agent startup. (`REQ-005` allowlist
registration; plan scope amendment S1)

## Scope
**Release unit**: WORKFLOW-CONFIG

## Assumptions

- `config/agent.toml` gains the key in the same commit (procedure 03); without this
  registration every Agent startup fails (`config_builders.py:104` path).
- The registration is a single entry in the existing `valid_keys.update({...})`
  subsystem block (near `:188` `"rag_db_path"`); no new mechanism.

## Design decisions

- Add the key beside `rag_db_path`/`session_db_path` entries — same subsystem class
  (DB path keys).

## Alternatives considered

- N/A: allowlist membership is the established pattern for every other `*_db_path` key.

## Implementation
### Target file
`scripts/agent/production_config_validator.py`

### Procedure
1. Add `"workflow_db_path"` to the subsystem-keys `valid_keys.update({...})` block
   (`:186-206`), beside the existing `rag_db_path`/`session_db_path` entries.

### Method
Single-string addition; `_check_unknown_production_keys` (`:298`, called at `:368`)
then accepts the key with no further change.

### Details
No comment about the change history (Current-Specification-Only).

### Companion test files
- `tests/agent/test_production_config_validator.py`
  - Procedure: add one test method asserting a config mapping that includes `workflow_db_path` produces no unknown-key error (pattern of `:24-45`).
  - Validation: `uv run pytest tests/agent/test_production_config_validator.py -q` — new method green.

## Compatibility considerations

- Only Agent startup validation is affected; validator semantics for all other keys
  unchanged.

## Security considerations

- Keeps the unknown-key gate strict (the key is explicitly registered rather than the
  gate loosened).

## Rollback considerations

- Revert with the WORKFLOW-CONFIG unit (key in agent.toml without this registration
  aborts startup).

## Validation plan

- `uv run pytest tests/agent/test_production_config_validator.py -q` (AC-3).
- `uv run mypy scripts/agent/production_config_validator.py`.

## Completion criteria

- A config mapping containing `workflow_db_path` validates with no unknown-key error
  (AC-3); all existing validator tests pass.

## Out of Scope

- Any change to `_check_unknown_production_keys` logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the allowlist entry | Completed | 2026-11-18 | 2026-11-18 |  |
| 2 | Add the companion acceptance test | Completed | 2026-11-18 | 2026-11-18 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-18 | 2026-11-18 |  |

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
- **Requirement ID**: `REQ-005` (validator accepts the new workflow_db_path key)
- **Source issue**: issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-155712_adrchk019_mdq-workflow-db-settings.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162732
- **Related target files**: `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`