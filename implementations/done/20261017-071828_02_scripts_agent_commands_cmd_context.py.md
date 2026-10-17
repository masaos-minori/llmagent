## Goal

Delete the `/diff` and `/system` handlers and their private helpers from
`scripts/agent/commands/cmd_context.py`, and remove the imports that become unused
(`REQ-002`, command-surface reduction).

## Scope

In scope: remove `_cmd_diff`, `_collect_diff_touched_paths`, `_group_paths_by_repo`,
`_print_repo_diffs`, `_DIFF_TOUCHED_TOOL_NAMES`, and `_cmd_system` from
`scripts/agent/commands/cmd_context.py`, plus imports that are now unused. Out of scope:
the `CommandDef` entries (`command_defs_list.py`, `REQ-001`), the `/audit` mixin module
(`cmd_audit.py` + `registry.py`, `REQ-003`), the test changes (`test_agent_cmd_context.py`,
`REQ-006`), and documentation (`REQ-007`).

## Assumptions

- The six symbols are owned solely by the `/diff` and `/system` commands being removed.
- After deletion, `git`, `orjson`, and `check_preflight` become unused and can be removed —
  but only after static-analysis confirmation, not by assumption.
- `switch_system_prompt` is imported on the same line as `clear_conversation`
  (`from agent.services.conversation_service import clear_conversation, switch_system_prompt`);
  `clear_conversation` is still used, so the import line must be edited, not dropped.

## Design decisions

- **Delete the code, then confirm dead imports.** Remove the handler/helper bodies first,
  then run `ruff`/`mypy` to find genuinely-unused imports before removing them — avoids
  dropping an import that some other handler still needs.
- **Preserve the mixin class and other handlers.** Only the two commands' code is removed;
  `_ContextMixin` and the remaining context handlers stay.

## Alternatives considered

`N/A`: the goal mandates deletion with no shim or forwarding path; keeping stubs would
contradict it.

## Implementation

### Target file

`scripts/agent/commands/cmd_context.py`

### Procedure

1. Confirm the symbols with `rg`: `_DIFF_TOUCHED_TOOL_NAMES` (constant L47, used L232),
   `_cmd_system` (L170, calls `switch_system_prompt` at L181), `_cmd_diff` (L186, async,
   called L189), `_collect_diff_touched_paths` (L213), `_group_paths_by_repo` (L242),
   `_print_repo_diffs` (L266). Also confirm the docstring lines for `_cmd_system` (L11) and
   `_cmd_diff` (L12).
2. Delete `_cmd_system()`, `_cmd_diff()`, `_collect_diff_touched_paths()`,
   `_group_paths_by_repo()`, `_print_repo_diffs()`, and the `_DIFF_TOUCHED_TOOL_NAMES`
   module constant.
3. Remove the docstring lines for the two removed handlers.
4. Edit the `switch_system_prompt` import (L33) to keep `clear_conversation` and drop
   `switch_system_prompt` (its only caller, L181, is being deleted).
5. Run `ruff check` / `mypy`; remove `git`, `orjson`, `check_preflight` only where they are
   now unused.

### Method

Delete each function/method body and the constant assignment as whole blocks, keeping class
and module indentation intact. Trim the import line in step 4 rather than deleting it.

### Details

- The `/audit` side of `REQ-003` (`cmd_audit.py` deletion + `registry.py` import/composition
  removal) is a separate procedure document; land both changes together so the registry
  integrity check never sees a dangling `CommandDef`→handler link.
- `orjson` usage currently sits inside the diff-touched-paths helper (L234/L236); once that
  helper is gone it may be unused — let `ruff` decide rather than assuming.
- `clear_conversation` is still called (L130); do not remove it.

## Compatibility considerations

The `_ContextMixin` class and the surviving context handlers keep working; only the two
removed commands' code disappears. `/diff`/`/system` now fail like unknown commands.

## Security considerations

Removes repository-diff and prompt-selection exposure through the REPL; no new data path is
introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `pytest tests/agent/commands/test_agent_cmd_context.py` — deleted-handler tests removed;
  the four rejection tests pass.
- `ruff check scripts/` — no unused-import findings after the edits.
- `mypy --no-namespace-packages scripts/` and `lint-imports` — clean.

## Completion criteria

`_cmd_diff`, `_collect_diff_touched_paths`, `_group_paths_by_repo`, `_print_repo_diffs`,
`_DIFF_TOUCHED_TOOL_NAMES`, and `_cmd_system` are absent from the file, the now-unused
imports are gone, `clear_conversation` still works, and no other handler references the
deleted symbols.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_audit.py`/`registry.py` (`REQ-003`), tests
(`REQ-006`), documentation (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `/diff`/`/system` handlers and helpers from `scripts/agent/commands/cmd_context.py` (`REQ-002`) | Completed | 20261017-100006 | 20261017-100006 |  |
| 2 | Drop deleted-handler tests; add the four rejection tests (`test_agent_cmd_context.py`) | Completed | 20261017-100006 | 20261017-100006 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-100006 | 20261017-100006 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261017-100006 | 20261017-100006 |  |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `scripts/agent/commands/cmd_context.py`