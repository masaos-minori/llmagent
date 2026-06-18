---
name: 20260618-151720_04_mcp_06_configuration_and_operations.md
description: Add strict-mode startup validation behavior section for unreachable servers
metadata:
  type: implementation
---

# Goal

Add a "Startup Validation Behavior (`tool_definitions_strict`)" section to `docs/04_mcp_06_configuration_and_operations.md` documenting the three scenarios: partial unreachable, all unreachable, and tool mismatch.

# Scope

- **File:** `docs/04_mcp_06_configuration_and_operations.md`
- **Change:** Add new section after "Settings with High Operational Impact" table
- **Out of scope:** Other sections, other docs

# Assumptions

1. The existing table entry `| tool_definitions_strict = true | Agent startup aborts on tool name mismatch |` only covers the mismatch case. The unreachable cases are undocumented.
2. The new section should immediately follow the "Settings with High Operational Impact" table since that table references `tool_definitions_strict`.

# Implementation

## Target file

`docs/04_mcp_06_configuration_and_operations.md`

## Procedure

Locate the end of the "Settings with High Operational Impact" table (currently the last section before "New Tool Registration Procedure"). Insert the new section between the table and the "New Tool Registration Procedure" heading.

## Method

New section:
```markdown
## Startup Validation Behavior (`tool_definitions_strict`)

`_check_tool_definitions` runs at agent startup and compares `tool_definitions` from `config/agent.toml` against live `/v1/tools` responses. Behavior depends on server reachability and `tool_definitions_strict`:

| Scenario | `strict = false` | `strict = true` |
|---|---|---|
| **Partial unreachable** — some servers respond | Validation proceeds with reachable servers; unreachable servers logged as `WARNING` | Same — only reachable tools are compared; mismatch in reachable tools raises `RuntimeError` |
| **All unreachable** — no server responds | Validation skipped; `INFO: "All MCP servers unreachable ... skipping tool definition check"` | Same — cannot validate zero tools; skipped |
| **Tool mismatch** — reachable but names differ | `WARNING` per direction (missing_in_server / extra_on_servers) | `RuntimeError: "Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."` |

**Key points:**
- Unreachable servers never cause `RuntimeError` by themselves; only a tool name mismatch in strict mode does.
- When all servers are unreachable, strict mode does **not** raise — validation is skipped.
- The error message clearly separates mismatches from unreachable servers for operator debugging.
```

## Details

- Insert after the "Settings with High Operational Impact" table, before "## New Tool Registration Procedure".

# Validation plan

| Check | Command | Expected |
|---|---|---|
| Section exists | `grep "Startup Validation Behavior" docs/04_mcp_06_configuration_and_operations.md` | 1 match |
| No broken markdown | manual review | table, headings correct |
