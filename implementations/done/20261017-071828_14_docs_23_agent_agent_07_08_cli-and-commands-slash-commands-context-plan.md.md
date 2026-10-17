## Goal

Remove the `/system [name]` row and its surrounding `/system` prose from
`docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`
(`REQ-007`, command-surface reduction).

## Scope

In scope: remove the `/system [name]` row (L40) and surrounding `/system` prose from
`docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`. Out of scope:
the command/handler/mixin deletions (`REQ-001`–`REQ-003`), the `GV-017` pattern additions
(`REQ-005`), and the other docs changes (`REQ-007`, separate documents).

## Assumptions

- The `/system` references are confined to the one row and its surrounding prose.

## Design decisions

- **Delete the row and its prose block.** Leave the rest of the document intact.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or forwarding path; leaving stale prose would
mislead readers into thinking the command still exists.

## Implementation

### Target file

`docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`

### Procedure

1. Locate the `/system` references with `rg`: the row (L40) and surrounding prose.
2. Delete the `/system [name]` row and its surrounding prose block.
3. Leave the rest of the document unchanged.

### Method

Delete the row and prose block as whole lines, preserving document structure.

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

No `/system` row or prose remains in the document, and the rest is unchanged.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py`\n(`REQ-003`), `tools/check_compat_shims.py` (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `/system [name]` row and prose from `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md` (`REQ-007`) | Completed | 20261017-100006 | 20261017-100006 |  |
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
- **Related target files**: `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`