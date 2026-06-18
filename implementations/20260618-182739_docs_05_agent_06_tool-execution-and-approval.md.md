# Implementation: Document round_exec serialization event schema

## Goal

Analysts can query the audit log for `round_exec` events and understand the schema, trigger conditions, and interpretation of elapsed time without reading source code.

## Scope

- `docs/05_agent_06_tool-execution-and-approval.md` — add `round_exec` event schema section

**Out of scope:** Code changes, other audit event documentation.

## Assumptions

1. The `write_round_exec()` function exists in `tool_audit.py` before this doc change.
2. The document already has a "Parallel vs Sequential Execution" section (confirmed — lines 32-43).

## Implementation

### Target file

`docs/05_agent_06_tool-execution-and-approval.md`

### Procedure

Add a new subsection "Serialization Event Schema" after the "Parallel vs Sequential Execution" section.

### Method

Single additive edit.

### Details

**Add after the "Parallel vs Sequential Execution" section (after line 43):**

```markdown
### Serialization Event Schema

Every round of tool calls executed by `_execute_standard()` emits a `round_exec`
audit event with the following fields:

| Field | Type | Description |
|---|---|---|
| `round_id` | string | UUIDv4 identifying this round |
| `tool_count` | int | Number of tool calls in the round |
| `mode` | string | `"parallel"`, `"serial"`, or `"dag"` |
| `has_side_effect` | bool | True if at least one tool is a side-effect tool |
| `trigger_tool` | string or null | Name of the first side-effect tool that triggered serial mode |
| `elapsed_ms` | float | Wall-clock time for the full round in milliseconds |

Use `elapsed_ms` to identify serialization overhead. A round with
`mode="serial"` and a high `elapsed_ms` compared to equivalent parallel rounds
is a candidate for optimization.

Query the audit log:
```
grep round_exec /path/to/audit.log | jq '.'
```
```

## Validation Plan

| Check | Tool | Criterion |
|---|---|---|
| Markdown | Manual review | Section renders correctly |
| Accuracy | Cross-reference with write_round_exec() | Field names and types match |
| Pre-commit | `pre-commit run --all-files` | Pass (markdown lint) |
