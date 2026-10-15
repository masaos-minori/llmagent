## Goal

Update the `/memory` help text in the command registry to the spec subcommand set
(REQ-010).

## Scope

Modify `scripts/agent/commands/command_defs_list.py` only: the `/memory`
`CommandDef.help` string.

## Assumptions

- The spec subcommand set is `status|list|delete|pin|unpin|prune|reindex|rebuild`
  (REQ-010).
- This module is the single source of truth for built-in slash commands; the help
  string is what the registry consistency tests check.

## Design decisions

- Replace the old pipe-delimited subcommand list on line 134 with the spec set,
  preserving the trailing description.

## Alternatives considered

- Rewriting the whole CommandDef: rejected. Only the `help` field changes; the
  name/prefix/async/handler fields are unchanged.

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

1. Update the `/memory` help string.

### Method

- Change line 134 from:

  ```python
  help="list|search|pin|unpin|delete|show|prune  Manage long-term memory entries",
  ```

  to:

  ```python
  help="status|list|delete|pin|unpin|prune|reindex|rebuild  Manage long-term memory entries",
  ```

### Details

- Keep the `  Manage long-term memory entries` suffix and the two-space separator.
- Do not touch any other CommandDef.

## Compatibility considerations

The help text is user-facing metadata; no behavioral contract changes. The
registry consistency tests assert this string matches the live dispatch set
(`cmd_memory.py`).

## Security considerations

N/A: help-text metadata only.

## Rollback considerations

Revert the commit; the string change is additive/reversible.

## Validation plan

- Registry consistency tests (referenced under `command_defs_list.py`) pass.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

The `/memory` registry help lists exactly the spec subcommand set.

## Out of scope

The dispatch implementation (`cmd_memory.py`) and its tests are separate target
rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `/memory` help to spec subcommand set | Completed | 2026-10-15 | 20261016-064317 | REQ-010; archive was premature: adversarial validation on 2026-10-16 found the help string unchanged in source; change applied then; `subcommands` list also migrated to the spec 8-set (GV-023 contract tests required it; procedure Scope under-specified this) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-15 | 20261016-064317 | ruff/mypy/lint-imports/bandit/stale all clean; 76 command tests pass; pre-existing unrelated failure in test_session_message_repo (undo boundary bug) noted |

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
- **Requirement ID**: `REQ-010`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/agent/commands/command_defs_list.py
