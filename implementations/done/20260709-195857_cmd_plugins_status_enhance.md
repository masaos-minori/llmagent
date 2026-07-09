# Implementation: plugin audit — /plugin status enhancement

## Goal

Enhance `/plugin status` command output to show last load result details and per-plugin last load result timestamp.

## Scope

- `scripts/agent/commands/cmd_plugins.py` — enhance output formatting

## Assumptions

1. `PluginLoadResult` already contains `tool_conflicts_shadowed`, `tool_conflicts_allowed`, `command_shadows_rejected`, `failed` details.
2. Plugin registry tracks load timestamps per plugin.

## Implementation

### Target file

`scripts/agent/commands/cmd_plugins.py`

### Procedure

1. Read the current `/plugin status` output format in `cmd_plugins.py`.
2. Add additional fields from `PluginLoadResult` to the status display:
   - `tool_conflicts_shadowed`
   - `tool_conflicts_allowed`
   - `command_shadows_rejected`
   - `failed` details
3. Add per-plugin last load result timestamp if available.
4. Format output consistently with existing fields.

### Details

- Keep output readable; add extra columns or sections as needed.
- Do not break existing parsers that consume `/plugin status` output.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Plugin status tests | `uv run pytest tests/test_cmd_plugins.py -v` | Pass |
| Manual review | View `/plugin status` output | Shows new fields |
