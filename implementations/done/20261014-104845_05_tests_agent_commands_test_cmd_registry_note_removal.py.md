## Goal

Remove `_MdqMixin` use from the removed-note-command tests (REQ-002: update tests).

## Scope

- Remove one import, one class, and one patch block; rewrite two descriptions. Only the Mdq-related parts; the note tests, `_Mcp`, and `_McpMixin` stay.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Remove `from agent.commands.cmd_mdq import _MdqMixin` (line 13) and `class _Mdq` (lines 51-55).
- In `_PatchedCommandRegistry`, remove the `_cmd_mdq` patch block and its comment (lines 71-77) and rewrite the class docstring (lines 62-64) so it no longer claims a patch; the wrapper only constructs the registry and exposes `dispatch`.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/agent/commands/test_cmd_registry_note_removal.py`

### Procedure

Apply the edits in Design decisions.

### Method

Edit by symbol. Keep `_Mcp` (used at the MCP test) and the `_McpMixin` import; run `uv run ruff check` to confirm no unused import remains.

### Details

The `hasattr(_CR, "_cmd_mdq")` patch was already a no-op while the mixin existed, so removing it changes no test behavior.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/agent/commands/test_cmd_registry_note_removal.py -q` passes with the same number of tests.
- `rg -n -i 'mdq' tests/agent/commands/test_cmd_registry_note_removal.py` has no match.

## Completion criteria

- The file imports nothing from `cmd_mdq` and mentions no `mdq`.
- All note tests still pass.

## Out of scope

- The note-dispatch tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the import, class, wrapper, and docstring | Completed | 20261014-110318 | 20261014-110318 |  |
| 2 | Run the tests that cover this file | Completed | 20261014-110318 | 20261014-110318 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-110318 | 20261014-110318 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: tests/agent/commands/test_cmd_registry_note_removal.py