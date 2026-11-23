## Goal

Declare the `/clear` command as asynchronous so its handler can await the transition service that finalizes the old session for `/clear new`.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the `CommandDef` entry for `/clear` only (`is_async=False` to `True`). The handler change is in procedure 13 and the service change in procedure 06.

## Assumptions

- Verified: `registry.py` rejects a handler whose coroutine-ness differs from `CommandDef.is_async`, so this flag must change together with `_cmd_clear` becoming `async def` (procedure 13).
- Found while implementing procedure 06 (Blocked: file outside procedure scope); added to the Plan as a fallout row in this cycle.

## Design decisions

- Change only the flag; keep name, prefix, help, and args so the command surface and the generated command docs are unchanged.

## Alternatives considered

Rejected: keeping `/clear` synchronous and finalizing the old session outside the transition service (it would leave `/clear new` without the old-session finalization that REQ-002 requires).

## Implementation
### Target file
`scripts/agent/commands/command_defs_list.py`

### Procedure
1. Set `is_async=True` on the `/clear` `CommandDef`.

### Method
One-line edit in `scripts/agent/commands/command_defs_list.py`.

### Details
- Land together with procedures 06 and 13 in the same batch run; the registry import check fails in between.

## Compatibility considerations

Slash-command syntax and help text are unchanged; only the dispatch path awaits the handler.

## Security considerations

N/A: no data path change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_cmd_context.py tests/agent/commands`
- registry self-check at import (`registry.py` raises on an is_async mismatch)

## Completion criteria

- `/clear` is declared async and the command registry imports without an is_async mismatch.

## Out of Scope

Handler and service changes (procedures 13 and 06); any other command definition.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261123-122903 | Changed: scripts/agent/commands/command_defs_list.py (/clear is_async=True) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261123-122903 | Covered by tests/agent/commands/test_agent_cmd_context.py::test_clear_handler_is_a_coroutine_declared_async |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-122903 | 20261123-123430 | 3e clean; awaiting end-of-batch run End-of-batch run passed: 13519 passed, 5 skipped; mypy 608 files clean; lint-imports 6 kept; diff-cover 98% |

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
- **Requirement ID**: `REQ-002` (atomic /clear new and /session load through the transition service)
- **Source issue**: issues/20261119-145300_cliplc002_session-transition-generation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-232757_cliplc002_session-transition-generation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/commands/command_defs_list.py`