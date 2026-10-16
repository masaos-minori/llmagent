## Goal

Remove `switch_system_prompt()` from `scripts/agent/services/conversation_service.py` and
delete its dedicated test class, keeping `clear_conversation`, system-prompt configuration,
and startup selection unchanged (`REQ-004`, command-surface reduction).

## Scope

In scope: delete `switch_system_prompt()` from `scripts/agent/services/conversation_service.py`.
Out of scope: the `/system` handler (`cmd_context.py`, `REQ-002`), the `CommandDef` entry
(`command_defs_list.py`, `REQ-001`), the test-class deletion
(`test_conversation_service.py`, `REQ-004`, separate document), and documentation
(`REQ-007`).

## Assumptions

- The function's only production caller is the removed `/system` handler
  (`cmd_context.py` L181); `startup_prompt_setup.py` does not call it.
- Its dedicated test class `TestSwitchSystemPrompt` lives in
  `tests/agent/services/test_conversation_service.py` and is deleted with the function.

## Design decisions

- **Conditional removal backed by evidence.** Removal proceeds only after a fresh
  `rg switch_system_prompt` across the working tree confirms no other caller exists
  (`UNK-01`). If an external (out-of-repo) consumer is found, retain the function and drop
  `REQ-004`.
- **Preserve the surviving surface.** `clear_conversation()` (L28), system-prompt
  configuration, and startup selection are left untouched.

## Alternatives considered

`N/A`: the goal mandates removal of dead code once the command is gone; gating or aliasing
would contradict it.

## Implementation

### Target file

`scripts/agent/services/conversation_service.py`

### Procedure

1. Re-run `rg switch_system_prompt` across the working tree to confirm the only production
   caller is `cmd_context.py` L181 and no external consumer exists (`UNK-01`). Record the
   result.
2. Confirm `def switch_system_prompt` at L49 and read its body.
3. Delete the `switch_system_prompt()` function and its body.
4. Verify `clear_conversation()` (L28) and the remaining functions are intact and still
   referenced.

### Method

Delete the function definition block as a whole, preserving module indentation and the
surviving functions.

### Details

- If step 1 finds an external consumer, stop: retain the function and drop `REQ-004`
  (report `Needs confirmation` for this row — do not proceed on the assumption that one
  `rg` settled it).
- The `TestSwitchSystemPrompt` class (L112 in `test_conversation_service.py`) is deleted in
  a separate document; delete both together.

## Compatibility considerations

Removing the function leaves `clear_conversation`, system-prompt configuration, and startup
selection working (confirmed by the surviving `conversation_service` tests). `/system` now
fails like an unknown command.

## Security considerations

`N/A`: removing an unused service function introduces no new path.

## Rollback considerations

Revert the commit.

## Validation plan

- `pytest tests/agent/services/test_conversation_service.py` — surviving
  `clear_conversation` / config tests pass; `TestSwitchSystemPrompt` gone.
- `lint-imports` — no dangling caller.
- `ruff` / `mypy --no-namespace-packages scripts/` — clean.

## Completion criteria

`switch_system_prompt` is absent from `conversation_service.py`, `clear_conversation` and
the other services are unchanged and still referenced, and no caller references the removed
function.

## Out of scope

`cmd_context.py` (`REQ-002`), `command_defs_list.py` (`REQ-001`),
`test_conversation_service.py` (`REQ-004`), documentation (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `switch_system_prompt()` from `scripts/agent/services/conversation_service.py` (`REQ-004`) | Pending | — | — | Confirm no external caller (UNK-01) before deleting |
| 2 | Delete `TestSwitchSystemPrompt` (`test_conversation_service.py`) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `scripts/agent/services/conversation_service.py`
