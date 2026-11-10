## Goal

Remove the `tool_def_strict` display row (and the now-empty "MCP / security settings" block) from the `/config` display, and make the empty `allowed_tools` line say that every tool is denied (REQ-001, with the REQ-002 display consequence).

## Scope
**Release unit**: strict-only-startup

Edit `scripts/agent/commands/cmd_config_display.py` and its companions `tests/agent/commands/test_cmd_config_char.py` and `tests/agent/commands/test_agent_cmd_config.py`.

## Assumptions

- Sequencing: the Plan's Phases 1-4 can land in any order within this file; the strict-key removal (Phase 1) ships in the `strict-only-startup` release unit, the `security_profile` removal is Phase 3 and the `allowed_root` rejection is Phase 4.
- `_print_mcp_settings` (line 77) contains only the `tool_def_strict` row, so removing the row leaves an empty heading; the method, its call (line 167) and the module-docstring entry (line 10) are removed. This is a judgment call inside the same file; the maintainer may prefer keeping the heading, which would be a change to the companion test only.
- The `(unrestricted)` text for an empty `allowed_tools` (line 133) becomes false once REQ-002 lands, so it is reworded here.

## Design decisions

- Delete the section rather than leave an empty heading; reword the empty-`allowed_tools` value to `(none: all tools denied)`.

## Alternatives considered

Keeping the heading with a placeholder row was rejected as noise.

## Implementation
### Target file
`scripts/agent/commands/cmd_config_display.py`

### Procedure
1. Delete `_print_mcp_settings` (lines 77-83), its call in the display routine (line 167), and its docstring line at line 10.
2. Change `pairs.append(("allowed_tools", "(unrestricted)"))` (line 133) to a value stating that all tools are denied.

### Method
- Run `rg -n "tool_def_strict|_print_mcp_settings|unrestricted" scripts/agent/commands/cmd_config_display.py`; only the reworded allowed_tools line may remain.

### Details
- Column widths: `write_kv` is called with `key_width=20` elsewhere; no change.

### Companion test files
- `tests/agent/commands/test_cmd_config_char.py`
  - Procedure: Remove the `MCP / security settings:` assertion (line 53), the two lines at 143-144 of the expected output, and change the `allowed_tools` expectation at line 155 to the new text; keep the `"unrestricted" not in out` check (line 104).
  - Validation: `uv run pytest tests/agent/commands/test_cmd_config_char.py -v`
- `tests/agent/commands/test_agent_cmd_config.py`
  - Procedure: Delete `ctx.cfg.tool.tool_definitions_strict = False` (line 199).
  - Validation: `uv run pytest tests/agent/commands/test_agent_cmd_config.py -v`

## Compatibility considerations

Output text change only; no machine consumer of the `/config` display found by `rg`.

## Security considerations

N/A: display only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/commands/test_cmd_config_char.py tests/agent/commands/test_agent_cmd_config.py -v`.
- `uv run ruff format`/`ruff check` on the three files; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- The display has no strict row or empty heading; both companion tests pass with the new expectations.

## Out of Scope

- Other display sections; the `allowed_root` display (no empty-root display exists).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `_print_mcp_settings` and reword the empty-`allowed_tools` value | Pending | — | — | REQ-001, REQ-002 |
| 2 | Update the two companion tests | Pending | — | — | REQ-001 |
| 3 | Run ruff, mypy and the command tests | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/agent/commands/cmd_config_display.py`, `tests/agent/commands/test_cmd_config_char.py`, `tests/agent/commands/test_agent_cmd_config.py`
