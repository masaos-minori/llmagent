## Goal

Remove the enforcement-table row mapping `_cmd_diff()` to `/diff` from
`docs/23_agent/agent_02_runtime-architecture.md` (`REQ-007`, command-surface reduction).

## Scope

In scope: remove the enforcement-table row at L62 from
`docs/23_agent/agent_02_runtime-architecture.md`. Out of scope: the command/handler/mixin
deletions (`REQ-001`–`REQ-003`), the `GV-017` pattern additions (`REQ-005`), and the other
docs changes (`REQ-007`, separate documents).

## Assumptions

- The single enforcement-table row describes only the removed `_cmd_diff()` → `/diff` gate.

## Design decisions

- **Delete only that one row.** Leave every other row and the table structure intact.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or forwarding path; leaving a stale row would
mislead readers into thinking the gate still exists.

## Implementation

### Target file

`docs/23_agent/agent_02_runtime-architecture.md`

### Procedure

1. Confirm the row with `rg`: the `_cmd_diff()` → `/diff` enforcement row at L62.
2. Delete that one row from the enforcement table.
3. Leave the rest of the table and the document unchanged.

### Method

Delete the table row as a whole line, preserving table syntax.

### Details

- If the row spans multiple lines, delete the whole logical row.

## Compatibility considerations

Docs-only change; production behavior is unaffected.

## Security considerations

`N/A`: documentation change; no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- Run the agent-domain docs checker named in `routing.md`
  (`uv run python tools/check_docs_consistency.py --domain agent`) — clean.

## Completion criteria

The `_cmd_diff()` → `/diff` enforcement row is gone, and the rest of the document is
unchanged.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py`\n(`REQ-003`), `tools/check_compat_shims.py` (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `_cmd_diff()` → `/diff` enforcement-table row from `docs/23_agent/agent_02_runtime-architecture.md` (`REQ-007`) | Completed | 20261017-100006 | 20261017-100006 |  |
| 3 | Run the docs checkers named in `routing.md` (`check-agent-docs`) | Completed | 20261017-100006 | 20261017-100006 |  |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`