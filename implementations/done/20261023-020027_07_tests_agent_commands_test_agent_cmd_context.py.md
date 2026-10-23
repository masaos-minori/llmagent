## Goal

Add `/history 0`, `/history -3`, and `/history 201` rejection cases to `TestCmdHistory` in
`tests/agent/commands/test_agent_cmd_context.py`, asserting a usage line is printed and no message
is printed, while keeping the existing default/valid cases unchanged (REQ-003; AC-2, AC-6).

## Scope

In scope: the `TestCmdHistory` class (`:472-527`) in `tests/agent/commands/test_agent_cmd_context.py`.
Out of scope: implementing `_cmd_history` (`scripts/agent/commands/cmd_context.py`, its own row).

## Assumptions

- Existing `TestCmdHistory` cases cover `"2"`, `""`, `"abc"`, `"5"`, `"1"` only (verified by read
  of `:473-527`). `test_history_invalid_n_shows_usage` (`:496-501`) asserts on the tag text
  ("usage"), not the message body, so it stays green once the parser raises and the call site
  renders via `write_validation_error`.
- The handler is called directly (`cmd._cmd_history("0")`), so a raised `CommandValidationError`
  that is not caught would surface as a test error rather than a usage line (A4) — the production
  call site must catch it, which is what the corresponding `cmd_context.py` row implements.

## Design decisions

- Add three methods to `TestCmdHistory`, each asserting the captured stdout contains "usage"
  (case-insensitive) and does NOT contain any conversation content, mirroring the style of the
  existing `test_history_invalid_n_shows_usage`. Keep all existing methods unchanged.

## Alternatives considered

- Asserting the exact usage string: rejected — the existing case asserts only on the tag text, and
  the rendered message format is governed by `cmd001` (out of scope here); keep the assertion on
  the "usage" marker to stay robust.

## Implementation

### Target file

`tests/agent/commands/test_agent_cmd_context.py`

### Procedure

Add three methods to `TestCmdHistory` (`:472`), mirroring `test_history_invalid_n_shows_usage`
(`:496-501`):

```python
@pytest.mark.parametrize("arg", ["0", "-3", "201"])
def test_history_rejects_out_of_range(self, capsys):
    ctx = _make_ctx()
    ctx.conv.history = [_system_msg(), _user_msg("q1"), _assistant_msg("a1")]
    cmd = _FakeCmd(ctx)
    cmd._cmd_history(arg)
    out = capsys.readouterr().out
    assert "usage" in out.lower()
    assert "q1" not in out
```

Keep all existing `TestCmdHistory` methods unchanged.

### Method

Assert the captured stdout contains the usage marker and none of the conversation content. The
handler is called directly, so the production catch (implemented in the `cmd_context.py` row) is
what makes this pass rather than an uncaught raise.

### Details

Existing cases cover `"2"`, `""`, `"abc"`, `"5"`, `"1"` only; they stay green. `test_history_default_is_5`
verifies the omitted-argument default is preserved.

## Compatibility considerations

- The existing default/valid cases (`test_history_default_is_5`, `test_history_prints_last_n_…`,
  etc.) are unchanged and must stay green (REQ-009, AC-2).

## Security considerations

- Locking `0`/negative/`>200` as rejected prevents a regression that would let
  `turns[-0:]`/`turns[-3:]` print the wrong slice.

## Rollback considerations

- Deleting the three added methods reverts this row.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_cmd_context.py -q` — new rejection cases pass;
  `TestCmdHistory`'s existing cases pass unchanged (AC-2).

## Completion criteria

- `TestCmdHistory` includes `/history 0`, `/history -3`, `/history 201` rejection cases asserting a
  usage line and no printed message; existing cases unchanged (AC-2, AC-9).

## Out of Scope

Implementing `_cmd_history` (`scripts/agent/commands/cmd_context.py`) and the other command test
rows — each is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `/history 0`, `/history -3`, `/history 201` rejection cases to `TestCmdHistory`; keep existing cases unchanged | Completed | 2026-10-23 | 2026-10-23 | REQ-003, REQ-009, AC-2, AC-6 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-23 | 2026-10-23 | — |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-23 | 2026-10-23 | — |
| 4 | — | Completed | 2026-10-23 | 2026-10-23 | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocking unknown remains (UNK-01's bounds are two call-site constants) | N/A: none | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`, `REQ-009`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `tests/agent/commands/test_agent_cmd_context.py`
