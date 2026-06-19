# Implementation: Document Tool Scheduling Serialization Behavior

## Goal

Add a section to `docs/04_mcp_06_configuration_and_operations.md` explaining why round-wide serialization happens for side-effect tools, how to interpret serialization log entries, and how to read serialization stats from `/mcp status`.

## Scope

- `docs/04_mcp_06_configuration_and_operations.md` — new `### Tool scheduling and serialization` subsection

Out of scope:
- Code changes
- Optimization recommendations (need observability data first)

## Assumptions

1. After Steps 1-3 are implemented, the log format and `/mcp status` output are stable.
2. The doc already covers MCP server configuration (line 281 onward). The new section covers the tool execution scheduling layer.
3. Audience: operators who see serialization warnings in logs and want to understand them.

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`

### Procedure

1. Find an appropriate insertion point (near the end, or after the server health section).
2. Insert a `### Tool scheduling and serialization` subsection.

### Method

New prose section with a reasons table, log example, and `/mcp status` extract.

### Details

**Subsection content outline:**

```
### Tool scheduling and serialization

The agent executes tool calls in resource-scoped groups. Most tools run in
parallel, but certain conditions force serial execution within a round:

| Condition | Trigger | Log reason |
|-----------|---------|------------|
| Tool has `requires_serial=True` | Any tool with this flag | `requires_serial` |
| Multiple write tools share a `resource_scope` | Two+ write tools with same scope | `resource_scope_conflict` |
| Write tools without a `resource_scope` | Any write tool lacking scope metadata | `is_write_overlap` |
| Side-effect tool in round (`_execute_standard` path) | Any side-effect tool | logged as "Side-effect tool detected" |

Serialization is intentional safety behavior — it prevents concurrent writes
from corrupting shared resources. It does not indicate a configuration error.

#### Reading serialization log entries

Each serialization event logs:
```
INFO ROUND_SERIALIZATION: triggered by <tool_name> (<reason>)
     — <N> tools serialized in this round
```

Example:
```
INFO ROUND_SERIALIZATION: triggered by write_file (is_write_overlap)
     — 2 tools serialized in this round
```

#### Serialization stats in /mcp status

Run `/mcp status` to see cumulative session stats:
```
--- Tool Scheduling ---
Serialization events this session: 5
Tools affected by serialization:   12
```

These counters reset on agent restart. A high serialization count relative to
total tool calls may indicate candidates for `resource_scope` annotation or
`requires_serial=False` review — but only after analyzing which tools are
triggering it.

#### Before optimizing

Do not change `requires_serial` or `resource_scope` values without reviewing
the serialization log data. The observability layer (Steps 1-3 above) provides
the data needed to make safe decisions.
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| Manual review | Read the new subsection | reasons, log format, and stats are clear without reading source |
| Accuracy | Verify reason strings match `tool_runner.py` log calls | `requires_serial`, `resource_scope_conflict`, `is_write_overlap` confirmed |
