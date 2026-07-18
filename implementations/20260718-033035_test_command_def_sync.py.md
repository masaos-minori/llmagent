# Implementation procedure: `tests/test_command_def_sync.py`

Source plan: `plans/done/20260717-130901_plan.md` (requirement `requires/20260717_11_require.md`),
Implementation step 4 (help-output cross-reference) and the consequence of step 1 identified in this doc's
Assumption 1 below.

## Goal

Keep `tests/test_command_def_sync.py`'s bidirectional `CommandDef` ↔ handler-method sync check passing once
`_cmd_mcp_tools()` (added by `implementations/20260718-032912_cmd_mcp.py.md`) exists as a new, intentionally
un-registered sub-dispatch helper method.

## Scope

**In scope**
- `tests/test_command_def_sync.py` (real path — confirmed to exist at 144 lines; the plan's own Scope
  bullet names this file directly as the real path for help-output-sync assertions, replacing the
  requirement's stated `tests/agent/commands/test_help.py`, which does not exist).
- Add `"_cmd_mcp_tools"` to `INTENTIONAL_HANDLER_EXCLUSIONS` (line 19-30).

**Out of scope**
- `command_defs_list.py`'s `/mcp` `CommandDef.help` string — confirmed by direct read
  (`command_defs_list.py:75`) to already read `"MCP server status, tool list, connectivity check"`, which
  already generically references tool-listing; no test in this file asserts on subcommand-level help text
  (only `test_help_output_mentions_all_command_names`, line 82, which checks top-level command *names*
  appear in `/help` output — `/mcp` already appears, unaffected by adding a subcommand). No change to this
  string is required by this doc.
- `_cmd_mcp_tools_dump` exclusion — not needed, since `/mcp tools dump` itself is deferred (see the
  cmd_mcp.py doc's Scope).

## Assumptions

1. **This file's `test_every_handler_has_commanddef` (lines 51-64) is a repo-wide structural sync check,
   not specific to `/mcp`.** It computes `all_handlers` as every `_cmd_*`-prefixed callable on a live
   `CommandRegistry` instance minus `defined_handlers` (from `_COMMANDS`) minus
   `INTENTIONAL_HANDLER_EXCLUSIONS`. Adding `_cmd_mcp_tools()` to `_McpMixin` (which `CommandRegistry`
   composes, per `registry.py:43,62`) makes it appear in `all_handlers` the moment the method exists,
   whether or not this plan's own text mentions this test file for that specific reason. This is a
   consequence this plan's Affected-areas table did not spell out explicitly (it names this file only for
   "help-output tests," not the handler-exclusion mechanics) — flagging this as a real, concrete gap in the
   plan's own analysis, not a stale assumption.
2. `_cmd_mcp_status` (the existing sibling sub-dispatch helper) is already listed at line 21 of
   `INTENTIONAL_HANDLER_EXCLUSIONS` for exactly this reason (confirmed by direct read) — `_cmd_mcp_tools`
   is the same pattern, one line away in the same frozenset literal.
3. This exclusion-set addition has zero runtime behavior effect — it only keeps a structural test
   accurate; it does not change dispatch, help text, or `/mcp`'s registered `CommandDef`.

## Implementation

### Target file

`tests/test_command_def_sync.py`.

### Procedure

1. Add `"_cmd_mcp_tools"` as a new entry inside the existing `INTENTIONAL_HANDLER_EXCLUSIONS` frozenset
   literal (`tests/test_command_def_sync.py:19-30`), alphabetically adjacent to `"_cmd_mcp_status"` for
   readability (not load-bearing, just consistent with the existing near-alphabetical ordering of that
   set).
2. No other line in this file changes.

### Method

One-line frozenset-literal addition; no new test function needed (the existing
`test_every_handler_has_commanddef` already covers the check once the exclusion is present).

### Details

Before (current, confirmed):
```
INTENTIONAL_HANDLER_EXCLUSIONS: frozenset[str] = frozenset(
    {
        "_cmd_mcp_status",
        "_cmd_mdq_get",
        ...
    }
)
```

After (pseudocode diff):
```
        "_cmd_mcp_status",
        "_cmd_mcp_tools",
        "_cmd_mdq_get",
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format tests/test_command_def_sync.py && uv run ruff check tests/test_command_def_sync.py` | 0 errors |
| Sync test | `uv run pytest tests/test_command_def_sync.py -v` | `test_every_handler_has_commanddef` passes once both `_cmd_mcp_tools()` (cmd_mcp.py doc) and this exclusion-set entry exist together |
| Regression check | `uv run pytest tests/test_command_def_sync.py -v` run *before* this edit, with `_cmd_mcp_tools()` already added | confirms the test actually fails without this doc's change (proves the dependency is real, not speculative) |
| Full suite | `uv run pytest -v` | no new failures |
