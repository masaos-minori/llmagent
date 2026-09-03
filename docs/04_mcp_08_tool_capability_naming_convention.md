---
title: "MCP Tool Capability Naming Convention"
area: mcp
tags:
  - mcp
  - tool-naming
  - convention
related:
---
# MCP Tool Capability Naming Convention

## Overview

MCP tools can declare arbitrary capability metadata. A capability is a string in the format `{domain}.{action}` or `{domain}.{subdomain}.{action}`, indicating which domain and what action a tool can perform.

This naming convention is **optional**; existing tools are not required to adopt it. Discovery services allow the absence of this field ([see mcp_tool_discovery.py](04_mcp_03_06_tool-runtime-availability-metadata.md)).

Related: [04_mcp_03_02_tool-registry.md](04_mcp_03_02_tool-registry.md) — Describes ownership and routing roles for `ToolRegistry` (distinct from the capability naming convention in this document).

Related: [04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md) — Describes the canonical name for `TOOL_LIST` exports (distinct from the capability naming convention in this document).

## Naming Convention

Capability strings must follow this format:

```json
{domain}.{action}
or
{domain}.{subdomain}.{action}
```

- All segments must be lowercase.
- Segments must not contain spaces or underscores.
- Segments must be separated by dots.
- Regex equivalent: `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`

**Note**: This regex is for documentation purposes only; **no runtime regex validation will be added**. This document defines a shape convention and does not mandate validator implementation.

## Domains

A domain is a logical resource area and does not necessarily map 1:1 to an MCP server name:

- `filesystem` — Filesystem operations
- `git` — Git repository operations
- `github` — GitHub API operations
- `process` — Process/shell operations
- `search` — Search operations
- Other future domains

This list is **open and extensible**, not a closed enumeration.

## Actions and distinction between read/write/delete/admin

Actions are a small, extensible vocabulary, primarily anchored to the following basic actions:

- `read` — Reader operation
- `write` — Writer operation
- `delete` — Deleter operation
- `execute` — Process/shell-like action

Domain-specific verbs also exist. For example, `github.issue.write` is more precise than just `github.write`.

## Multiple Capabilities

Tools can declare multiple capabilities (e.g., a tool that triggers both a read and a side effect). Therefore, the corresponding `RuntimeTool` field is a `tuple[str, ...]` rather than a single string ([see runtime_tool.py](04_mcp_03_06_tool-runtime-availability-metadata.md)).

## Examples

Requirement examples:

- `filesystem.read`
- `filesystem.write`
- `filesystem.delete`
- `git.read`
- `git.write`
- `github.issue.write`
- `process.execute`
- `search.web`

**Note:** The value `("web_fetch",)` has only been observed in test fixtures (`tests/test_runtime_tool_routing_integration.py`); currently, no MCP servers in production environments declare `capabilities` based on this naming convention.

## Status

This is a proposed standard convention. Currently, no MCP servers in production environments have formally adopted this naming convention.

## Related Documents

- [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) — MCP Documentation Guide
- [04_mcp_03_02_tool-registry.md](04_mcp_03_02_tool-registry.md) — ToolRegistry Ownership & Routing
- [04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md) — Canonical Name for TOOL_LIST Exports
- [04_mcp_03_06_tool-runtime-availability-metadata.md](04_mcp_03_06_tool-runtime-availability-metadata.md) — Tool Runtime Capability Field

## Keywords

mcp
tool-schema
capabilities
naming-convention
policy
