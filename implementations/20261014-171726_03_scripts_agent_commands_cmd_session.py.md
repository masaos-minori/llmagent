# Implementation Procedure

## Goal

Render `message_count` as a new column in the `/session list` table, passing it through the extended `SessionRow` (`REQ-001` / `AC-1`).

## Scope

Modify only `_session_list` in `scripts/agent/commands/cmd_session.py`: the `SessionRow(...)` construction (lines 100-106), the render-loop `table_rows.append(...)` (lines 121-127), and the `write_table` header (line 128). No other file is modified here.

## Assumptions

- `list_sessions()` returns `message_count` (sibling procedure for `scripts/agent/session.py`).
- `SessionRow` has a `message_count` field (sibling procedure for `scripts/agent/services/models.py`).
- Existing callers/tests may pass dicts without `message_count`; reading defensively avoids a `KeyError`.

## Design decisions

- In the `SessionRow(...)` call (line 100), add `message_count=int(r.get("message_count", 0))`. `.get(...)` keeps backward compatibility with any caller that omits the key; `int(...)` coerces SQLite's count to a plain int.
- In the render loop, append `sr.message_count` to each `table_rows` list (after `sr.created_at`, line 125).
- Extend the header on line 128 to `["ID  ", "Title", "Created", "Messages"]`. Column count must match the appended row length (4).

## Alternatives considered

- Reading `r["message_count"]` directly in the render loop: rejected — the plan mandates the value flow through `SessionRow`, not ad hoc reads.
- Hard-requiring `message_count` (no `.get` default): rejected — would break existing list tests whose mock dicts omit the key.

## Implementation

### Target file

`scripts/agent/commands/cmd_session.py`

### Procedure

1. Add `message_count=int(r.get("message_count", 0))` to the `SessionRow(...)` constructor (inside lines 100-106).
2. Append `sr.message_count` to the `table_rows` list in the render loop (inside lines 121-127).
3. Change the header on line 128 to include `"Messages"` as a fourth column.

### Method

Keep all three edits inside `_session_list`. Preserve the `ID`/`*` current marker column, title truncation, and the `(generating...)`/`(no title)` branches. The new column is purely additive and rendered last.

### Details

- `sr.message_count` is read off the dataclass (single source of truth), satisfying the "flow through `SessionRow`" constraint.
- Header width: `write_table` draws a grid from `table_rows`; the header now has 4 entries and every row appends 4 values — they must stay in sync.

## Compatibility considerations

Depends on the two sibling procedures (query + dataclass). The added column is display-only; no contract or import changes.

## Security considerations

N/A: display formatting only.

## Rollback considerations

Revert the commit touching `scripts/agent/commands/cmd_session.py`.

## Validation plan

| Target/Module | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/commands/cmd_session.py` | Integration — roundtrip: listed ID loads/deletes; new column renders | `uv run pytest tests/agent/commands/test_agent_cmd_session.py` | Roundtrip passes; 4-column table shows counts |

## Completion criteria

`/session list` prints a four-column table (ID, Title, Created, Messages) where Messages equals each session's `message_count`.

## Out of scope

Query change (`scripts/agent/session.py`) and dataclass extension (`scripts/agent/services/models.py`) are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Render `message_count` column in `_session_list` | Pending | — | — | REQ-001 / AC-1 |
| 2 | Add/update tests per Validation plan | Pending | — | — | roundtrip test in `test_agent_cmd_session.py` |
| 3 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | — |
| 4 | Update documentation | N/A | — | — | not in scope for this row |

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
- **Requirement ID**: `REQ-001` — add per-session message count to `/session list`
- **Source issue**: `issues/20261014-150311_sess001_finalize-session-list-command.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261014-160933_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-171726
- **Related target files**: `scripts/agent/commands/cmd_session.py`
