## Goal

Remove the `/diff`, `/system`, and `/audit` rows from the built-in slash-command index
table in `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`
(`REQ-007`, command-surface reduction).

## Scope

In scope: remove the three command rows from the index table in
`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`. Out of scope: the
command/handler/mixin deletions (`REQ-001`–`REQ-003`), the `GV-017` pattern additions
(`REQ-005`), and the other docs changes (`REQ-007`, separate documents).

## Assumptions

- The three rows describe only the removed commands; removing them does not affect the
  remaining rows.

## Design decisions

- **Delete only the three rows.** Leave every other row and the table structure intact.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or forwarding path; leaving stale rows would
mislead readers into thinking the commands still exist.

## Implementation

### Target file

`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`

### Procedure

1. Locate the three rows with `rg`: `/diff` (L58), `/system` (L63), `/audit` (L66).
2. Delete those three rows from the index table.
3. Leave the rest of the table and the document unchanged.

### Method

Delete the three table rows as whole lines, preserving table syntax.

### Details

- If any of the three rows spans multiple lines, delete the whole logical row.

## Compatibility considerations

Docs-only change; production behavior is unaffected.

## Security considerations

`N/A`: documentation change; no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- Run the agent-domain docs checker named in `routing.md`
  (`uv run python tools/check_docs_consistency.py --domain agent`) — clean.
- `ruff` / `mypy` — not applicable to docs.

## Completion criteria

No `/diff`, `/system`, or `/audit` row remains in the index table, and the rest of the
document is unchanged.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py`\n(`REQ-003`), `tools/check_compat_shims.py` (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `/diff`, `/system`, `/audit` rows from the index table in `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (`REQ-007`) | Pending | — | — | |
| 3 | Run the docs checkers named in `routing.md` (`check-agent-docs`) | Pending | — | — | |

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
- **Related target files**: `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`
