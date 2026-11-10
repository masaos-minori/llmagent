## Goal

Remove the `security_profile` plumbing from `build_agent_config` and its helpers, and stop passing a profile to `ProductionConfigValidator` and `MCPConfig` (REQ-007 no profile key).

## Scope
**Release unit**: N/A: not part of a release unit

Edit `scripts/agent/config_builders.py` only; builder tests are the Plan row for `tests/agent/test_config_builders.py`.

## Assumptions

- Phase 3 of the Plan; independent of the strict removal. It must land with the `config_dataclasses.py` (`MCPConfig` field) and `production_config_validator.py` (`validate()` signature) rows, otherwise `MCPConfig(security_profile=...)` or `validate(security_profile=...)` breaks.
- `SecurityProfile` was only imported here for the `build_agent_config` coercion; `_build_mcp_servers` stays imported from `shared.mcp_config`.

## Design decisions

- `_run_production_validation(cfg, known_tools)` and `_assemble_agent_config(cfg, system_prompt_tool)` lose the profile argument; `MCPConfig(mcp_servers=_build_mcp_servers(cfg))`.
- A config that still sets `security_profile` is no longer read here; the validator reports it as an unknown key, so the failure is a load error rather than being silently ignored.

## Alternatives considered

Ignoring and dropping a stray `security_profile` key silently was rejected: removed keys must fail load (REQ-001 text applied to REQ-007).

## Implementation
### Target file
`scripts/agent/config_builders.py`

### Procedure
1. In the `from shared.mcp_config import (...)` block (line 23) remove `SecurityProfile`, keeping `_build_mcp_servers`.
2. Remove the `security_profile_val` parameter from `_run_production_validation` (line 102) and call `ProductionConfigValidator().validate(cfg, known_tools=known_tools)`.
3. Remove the `security_profile_val` parameter from `_assemble_agent_config` (line 123) and construct `MCPConfig(mcp_servers=_build_mcp_servers(cfg))`.
4. In `build_agent_config` (line 160) delete the `security_profile_val = SecurityProfile(...)` line and update the two calls.

### Method
- Edit by symbol; `rg -n "SecurityProfile|security_profile" scripts/agent/config_builders.py` returns nothing afterwards.

### Details
- `build_agent_config` signature and `cfg_override` behavior are unchanged; `/reload` and tests keep calling it the same way.

## Compatibility considerations

A config with `security_profile` fails production validation as an unknown key (previously accepted when equal to `"production"`). `config/agent.toml` never set it.

## Security considerations

N/A: removes a single-valued setting; no authorization behavior changes (MCP auth enforcement was already unconditional).

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py -v`.
- `uv run ruff format`/`ruff check` on the file; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- No profile symbol remains in the file; `build_agent_config` returns an `AgentConfig` whose `mcp` has only `mcp_servers`.

## Out of Scope

- Validator, dataclass and registry edits (own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the import and the profile parameters and arguments | Pending | — | — | REQ-007 |
| 2 | Run ruff, mypy, lint-imports and the builder tests (after the dataclass and validator rows land) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/agent/config_builders.py`
