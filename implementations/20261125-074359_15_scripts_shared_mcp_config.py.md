## Goal

Make the MCP server parser strict: a declared key set, no coercion, and the same type rules the rest
of the configuration uses, so the MCP path rejects what the other paths reject (REQ-004, strict MCP
types; REQ-011, structured error text).

## Scope
**Release unit**: R1-strict-primitives

## Assumptions
- Verified against current source: `_build_single_server` (`mcp_config.py:254`) applies defaults with
  `list(v.get("cmd", []))` and `dict(v.get("env", {}))` and coerces `health_timeout` with `float(...)`,
  so `cmd="python"` becomes `['p','y','t','h','o','n']` and `health_timeout="30"` becomes `30.0`.
- The primitives come from `scripts/shared/config_field_types.py` (row 1), the same layer as this
  module, so no cross-layer import is needed.
- Enum fields (`transport`, `startup_mode`) keep their existing enum validation in
  `McpServerConfig.__post_init__` (`mcp_config.py:118`); only the raw value type check moves here.
- The deployed MCP tables were checked under the strict rules and report no newly rejected value
  (UNK-01); confirm again with the parity test at implementation time.

## Design decisions
- The allowed-key set is declared in this module and unknown keys are rejected with the key name only,
  because silently dropping a key is how a typo becomes a runtime default.
- `env` keeps its denylist check (`_validate_env`, `mcp_config.py:181`) unchanged; the type rule is
  added ahead of it.

## Alternatives considered
- Keeping the coercion and only documenting it — rejected: AC-1 requires the same accept and reject
  result on both paths.

## Implementation
### Target file
`scripts/shared/mcp_config.py`

### Procedure
Rewrite `_build_single_server` with the shared primitives and a declared allowed-key set.

### Method
- `cmd` must be a non-empty sequence of non-empty strings; `env` must be `mapping[str, str]`.
- `required` must be `bool`; numeric fields (`health_timeout`, `startup_timeout_sec`) must reject
  `bool`; `url`, `role`, `auth_token` must be `str`.
- Unknown keys are rejected by name through `reject_unknown_keys` (row 1). Keys the parser does not
  read today, such as enabled and auto_start, are rejected as unknown keys rather than type-checked,
  because they are not `McpServerConfig` fields.

### Details
- A present-but-wrong-typed value is rejected; only a missing key takes the default.
- The raised error names the server key and the field, never the value, because `auth_token` can carry
  a token.

## Compatibility considerations
- Blast radius: 19 modules consume `shared.mcp_config`; the parser is the only place MCP definitions
  are built, so a stricter parser changes what startup accepts.
- `tests/shared/test_mcp_config.py` has coercion-tolerant cases that must be retargeted by this
  document's companion.

## Security considerations
- No raw value in error text; `auth_token` and `env` values must not be echoed.

## Rollback considerations
- Revert the Phase 1 commit; the parser is stateless.

## Validation plan
- `uv run pytest tests/shared/test_mcp_config.py tests/shared/test_config_field_types.py -q`
- `uv run pytest tests/agent/services/test_config_reload_parity.py -q` (row 27)
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- Every input in the Plan's `Newly rejected inputs` list is rejected by the MCP parser, and no raised
  message contains a raw value.

## Out of Scope
- The pending-record display for MCP definition changes (rows 8, 21, 22).

### Companion test files
- `tests/shared/test_mcp_config.py`
  - Procedure: add strict rejection cases for every newly rejected MCP input and assert the declared
    allowed-key set rejects an unknown key by name.
  - Validation: `uv run pytest tests/shared/test_mcp_config.py -q`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (strict MCP server parsing), REQ-011 (structured config error); AC-1, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/shared/mcp_config.py`, `tests/shared/test_mcp_config.py`
