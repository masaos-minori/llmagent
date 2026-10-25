# Implementation Procedure — docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md

## Goal

State the `/session purge` current-session exemption as an operational note in the
slash-command doc (REQ-007, AC-006): the current session is never removed and the
output reports the exemption.

## Scope

- Modify only `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`:
  the `/session purge` row of the `/session` subcommand table (~line 59).
- English; policy/behavior wording only, no code detail (issue Documentation Impact).
- The "Long-running and off-loop subcommands" paragraph below the table is untouched.

## Assumptions

- The `/session purge` table cell quoted below is verbatim from HEAD 529c2fe3e;
  re-confirm before editing in case doc churn landed first.
- The success-line wording matches the implementation decision in procedure 04
  (`(kept active session <id>)`); if the final wording diverges, this sentence tracks
  it — AC-003 pins the behavior, not the exact doc string.

## Design decisions

- Single-cell extension inside the existing table row instead of a new paragraph:
  the table is this page's canonical contract for `/session` behavior, consistent with
  how the flag-validation semantics are already documented in the same cell.
- Describe the kept-count side effect explicitly (may exceed `--max-sessions` by one)
  so operators are not surprised (plan Assumption 2, Risks mitigation).

## Alternatives considered

- A new note paragraph after the table: rejected — fragments the per-command contract
  and duplicates the table's role.

## Implementation
### Target file
`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`

### Procedure

In the `/session purge [--max-sessions <n>] [--max-age-days <n>]` row, append to the
end of the description cell (after "...an absent flag uses the retention default"):

> ; the session currently active in the agent is never removed — when a purge would
> have deleted it, the success line reports `(kept active session <id>)` and the kept
> session count may exceed `--max-sessions` by one

### Method
One in-place cell extension; no new rows, columns, headings, or links.

### Details
- Keep the cell as a single Markdown table row (no line breaks inside the cell).
- Backticks around `(kept active session <id>)` mark it as literal output text,
  matching the cell's existing style for flag syntax.

## Compatibility considerations

- `docs/00_index.md` mapping for `docs/23_agent/` unchanged; no index edit needed.
- The offload/dispatch paragraph and the `is_async` contract sentence are untouched.

## Security considerations

N/A: documentation-only.

## Rollback considerations

Restore the cell to its quoted original.

## Validation plan

- Docs checkers per `routing.md` Tools after the edit:
  `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py`,
  `uv run python tools/check_docs_content_policy.py`, and
  `uv run python tools/check_docs_consistency.py --domain agent`.
- Confirm quoted "before" text still matches HEAD before editing.

## Completion criteria

- AC-006: the exemption note is present in the `/session purge` row; docs checkers
  pass.

## Out of Scope

- The DB-layer policy statement (procedure 07).
- `/session delete` guard documentation (unchanged behavior).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the table-cell edit | Completed | — | — | /session purge table cell extended with active-session keep note |
| 2 | Run docs checkers | Completed | — | — | consistency(agent) + other docs checkers green |

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
- **Requirement ID**: REQ-007 (AC-006)
- **Source issue**: `issues/20261025-115826_sess005_purge-deletes-current-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124106_sess005_purge-deletes-current-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-141651
- **Related target files**: docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md (procedure 07)