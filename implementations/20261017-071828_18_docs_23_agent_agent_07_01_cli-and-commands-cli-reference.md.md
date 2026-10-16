## Goal

Trim the chapter-description cells that name the removed commands in
`docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` (`REQ-007`,
command-surface reduction).

## Scope

In scope: trim the chapter-description cells that name the removed commands
(e.g. L38 "Debug/audit, Git/Diff, Compact") in
`docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`. Out of scope: the
command/handler/mixin deletions (`REQ-001`–`REQ-003`), the `GV-017` pattern additions
(`REQ-005`), and the other docs changes (`REQ-007`, separate documents).

## Assumptions

- The removed-command names appear only in chapter-description cells; trimming them does
  not affect the rest of the reference.

## Design decisions

- **Trim only the removed-command mentions.** Leave the surviving command descriptions and
  the table structure intact.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or forwarding path; leaving stale mentions in
the reference would mislead readers into thinking the commands still exist.

## Implementation

### Target file

`docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`

### Procedure

1. Locate the removed-command mentions with `rg`: e.g. L38 "Debug/audit, Git/Diff,
   Compact" and any other `/diff`, `/system`, `/audit` mentions in description cells.
2. Trim the removed-command mentions from the description cells.
3. Leave the surviving command descriptions and the table structure intact.

### Method

Edit the description cells as whole lines, preserving table syntax.

### Details

- If a cell lists multiple commands, remove only the removed-command tokens and keep the
  survivors (e.g. "Debug, Compact").

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

No `/diff`, `/system`, or `/audit` mention remains in the chapter-description cells, and
the rest of the document is unchanged.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py`\n(`REQ-003`), `tools/check_compat_shims.py` (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Trim the removed-command mentions from the chapter-description cells in `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` (`REQ-007`) | Pending | — | — | |
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
- **Related target files**: `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`
