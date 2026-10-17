## Goal

Remove the `/audit` subcommand rows (L43-47) and the `/diff` sections (L51, L67) from
`docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`, keeping
`/debug` and `/compact` (`REQ-007`, command-surface reduction).

## Scope

In scope: remove the `/audit` subcommand rows (L43-47) and the `/diff` sections (L51, L67)
from `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`. Out of
scope: the command/handler/mixin deletions (`REQ-001`–`REQ-003`), the `GV-017` pattern
additions (`REQ-005`), and the other docs changes (`REQ-007`, separate documents).

## Assumptions

- The `/audit` and `/diff` references are confined to the listed rows/sections; `/debug`
  and `/compact` are independent.

## Design decisions

- **Delete only the `/audit` and `/diff` blocks.** Keep `/debug` and `/compact` intact.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or forwarding path; leaving stale sections
would mislead readers into thinking the commands still exist.

## Implementation

### Target file

`docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`

### Procedure

1. Locate the references with `rg`: `/audit` subcommand rows (L43-47), `/diff` sections
   (L51, L67).
2. Delete the `/audit` subcommand rows and the `/diff` sections.
3. Leave `/debug`, `/compact`, and the rest of the document unchanged.

### Method

Delete the rows/sections as whole lines, preserving document structure.

### Details

- Ensure the deletion does not leave an orphaned heading or dangling cross-reference.

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

No `/audit` subcommand rows or `/diff` sections remain, and `/debug`/`/compact` and the
rest of the document are unchanged.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py`\n(`REQ-003`), `tools/check_compat_shims.py` (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `/audit` subcommand rows and `/diff` sections from `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` (`REQ-007`) | Completed | 20261017-100006 | 20261017-100006 |  |
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
- **Related target files**: `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`