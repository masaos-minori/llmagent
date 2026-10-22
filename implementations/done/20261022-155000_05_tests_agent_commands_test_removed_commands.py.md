## Goal

Add parametrized dispatch, completion, and help-rejection tests for the six registry-only removed commands (`/db`, `/note`, `/skill`, `/mdq`, `/approve`, `/reject`) to `tests/agent/commands/test_removed_commands.py`, reusing the real `CommandRegistry` and the rejection patterns already used for `/diff`, `/system`, `/audit`, `/workflow` in `test_agent_cmd_context.py` (REQ-004; AC-4).

## Scope

- Modify `tests/agent/commands/test_removed_commands.py` only.
- Add new parametrized test functions; keep all existing registry-membership tests (including the four duplicate `/db` tests) unchanged.

## Assumptions

- `CommandRegistry.dispatch(name)` returns `False` for a name that is not registered, exactly as it does for an unknown command.
- `completion_command_names()` returns the completion name set; `/help` renders via `CommandRegistry._cmd_help()`.
- A minimal `MagicMock` context is enough for the integrity check and help rendering (as `test_agent_cmd_context._registry_ctx()` provides).

## Design decisions

- Parametrize three new tests over the six names with `@pytest.mark.parametrize("removed_name", [...])`, mirroring the five tests in `test_agent_cmd_context.py`'s "removed command rejection" section.
- Keep the existing per-command `_COMMANDS` membership tests; the new tests cover the paths they do not (dispatch, completion, help).

## Alternatives considered

- Extending each existing class with the extra assertions — rejected: a single parametrized block mirrors the established pattern and keeps the four `/db` membership tests intact.

## Implementation

### Target file

`tests/agent/commands/test_removed_commands.py`

### Procedure

1. Add the needed imports (`pytest`, `CommandRegistry`, `completion_command_names`, `CliOutputPort`, and a minimal-context factory) at module scope or inside the new tests.
2. Add a "removed command rejection" block with three parametrized tests over the six names.
3. Run the module.

### Method

Append after the existing classes (mirroring `test_agent_cmd_context.py` lines 283-332):

```python
_REMOVED_REJECTION_NAMES: tuple[str, ...] = (
    "/db", "/note", "/skill", "/mdq", "/approve", "/reject",
)


def _registry_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.tool.tool_definitions = []
    ctx.cfg.llm.llm_url = "http://localhost/v1"
    return ctx


@pytest.mark.asyncio
@pytest.mark.parametrize("removed_name", _REMOVED_REJECTION_NAMES)
async def test_removed_names_dispatch_fails_like_unknown(removed_name: str) -> None:
    registry = CommandRegistry(_registry_ctx(), None)
    assert await registry.dispatch(removed_name) is False


@pytest.mark.parametrize("removed_name", _REMOVED_REJECTION_NAMES)
def test_removed_names_absent_from_completion(removed_name: str) -> None:
    assert removed_name not in completion_command_names()


@pytest.mark.parametrize("removed_name", _REMOVED_REJECTION_NAMES)
def test_removed_names_absent_from_help(capsys, removed_name: str) -> None:
    registry = CommandRegistry(_registry_ctx(), CliOutputPort())
    registry._cmd_help()
    out = capsys.readouterr().out
    assert removed_name not in out
```

### Details

- Evidence in-file: the six names appear only as `_COMMANDS` membership assertions (`"/db"`, `"/note"`, `"/skill"`, `"/mdq"`, `"/approve"`, `"/reject"`); none is checked against dispatch, completion, or `/help`.
- Pattern source: `tests/agent/commands/test_agent_cmd_context.py` "removed command rejection" (lines 283-332) provides `_registry_ctx()`, `CommandRegistry(...).dispatch(...)`, `completion_command_names()`, and `CommandRegistry(..., CliOutputPort())._cmd_help()`.
- REQ-004 requires all six names tested absent from the registry (already covered), rejected by dispatch, and absent from completion and `/help`; this row adds the latter two.

## Compatibility considerations

N/A: test-only change; no runtime contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is added.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/commands/test_removed_commands.py` | Unit | `uv run pytest tests/agent/commands/test_removed_commands.py -q` | All 9 existing tests plus the 18 new assertions pass |

## Completion criteria

The six names each pass dispatch-fails-like-unknown, absent-from-completion, and absent-from-help, alongside the existing registry-membership tests.

## Out of Scope

- Modifying the existing `_COMMANDS` membership tests.
- Adding rejection tests for `/diff`, `/system`, `/audit`, `/workflow` (already covered in `test_agent_cmd_context.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add parametrized dispatch, completion, and help rejection tests for the six names | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (add missing removed-command tests covering dispatch, completion, and help for the registry-only names)
- **Source issue**: `issues/20261022-124244_aliasstatus_classify-session-export-alias-and-removed-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-131142_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-155000
- **Related target files**: `tests/agent/commands/test_removed_commands.py`
