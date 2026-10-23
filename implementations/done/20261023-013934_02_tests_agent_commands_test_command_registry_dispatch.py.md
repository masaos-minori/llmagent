## Goal

Add regression tests asserting the new command-boundary error surface in
`tests/agent/commands/test_command_registry_dispatch.py`: a raising handler renders
`[error]`/`[usage]` tagged output naming the command and never `[fatal]`, a
`sqlite3.Error` names the command and states a possibly-partial effect, and every handled
error is logged.

## Scope

In scope: extend the `out` stub in this file with `write_error` / `write_validation_error` /
`write_fatal` mocks, and add the four handler-raises tests plus a `caplog` log assertion
(`REQ-007`). Out of scope: the `registry.py` implementation (`scripts/agent/commands/registry.py`,
separate document), the unchanged turn-failure `[fatal]` regression (already covered by
`tests/agent/test_repl_error_handling.py`, `AC-4`), and the direct-handler-call contract
(`test_command_def_sync.py`, `AC-5`).

## Assumptions

- Tests assert on tags and command-name presence, not exact message bodies (`REQ-007`, issue
  Testing Expectations), so they stay stable if wording changes.
- The existing fixture builds `CommandRegistry(MagicMock(), out)`; injecting a raising handler is
  done by `setattr(registry, "_cmd_mcp", AsyncMock(side_effect=...))`, matching the existing
  `test_builtin_dispatch_strips_args` pattern.
- `/mcp` is a prefix command, so `dispatch("/mcp extra")` matches it and passes `"extra"` as the
  single arg; the matched `CommandDef.name` rendered by the new code is `/mcp`.

## Design decisions

- **Extend the shared `out` stub** rather than add a second fixture, so all tests in the file
  share one consistent stub that exposes every `OutputPort` method the new path may call.
- **One behavior per test**: runtime error → `[error]`, validation error → `[usage]`,
  `sqlite3.Error` → `[error]` + partial-effect, plus a separate log assertion — keeps each
  assertion focused and failures easy to localize.

## Alternatives considered

A single parametrized test over all three exception types would compress the cases but mixes
tag assertions (`[error]` vs `[usage]`) and the partial-effect check in one place; separate
tests assert each classification independently and fail loudly on the wrong tag.

## Implementation

### Target file

`tests/agent/commands/test_command_registry_dispatch.py`

### Procedure

1. Read the current file (34 lines): the `out` stub at L15 is
   `SimpleNamespace(write=MagicMock(), write_table=MagicMock())` and only `test_builtin_dispatch_strips_args`
   exists (args-stripping only).
2. Extend the `out` stub in the `registry` fixture to expose the methods the new dispatch path
   calls: add `write_error=MagicMock()`, `write_validation_error=MagicMock()`, and
   `write_fatal=MagicMock()` alongside the existing `write` / `write_table`.
3. Add imports: `import logging` and
   `from agent.commands.exceptions import UnknownPresetError`; `import sqlite3` in the DB test.
4. Add `test_dispatch_runtime_error_surfaces_as_command_error`: set `_cmd_mcp` to an
   `AsyncMock(side_effect=RuntimeError("boom"))`, `await registry.dispatch("/mcp extra")`, assert
   the result is `True`, `out.write_error` was called once with a message containing
   `OutputTag.ERROR` and the command name `/mcp`, and `out.write_fatal` was not called.
5. Add `test_dispatch_validation_error_uses_usage_tag`: set `_cmd_mcp` to an
   `AsyncMock(side_effect=UnknownPresetError("gold", ("silver",)))`, dispatch `/mcp extra`,
   assert `out.write_validation_error` was called once with a message containing `OutputTag.USAGE`
   and `/mcp`.
6. Add `test_dispatch_sqlite_error_states_partial_effect`: set `_cmd_mcp` to an
   `AsyncMock(side_effect=sqlite3.OperationalError("disk I/O error"))`, dispatch `/mcp extra`,
   assert `out.write_error` was called once with a message containing `OutputTag.ERROR`, `/mcp`,
   and the word "partial".
7. Add `test_dispatch_logs_the_command_error`: wrap the dispatch call in
   `with caplog.at_level(logging.ERROR):`, then assert some `caplog.record` message contains the
   command name `/mcp` (`REQ-005`, `AC-7`).
8. Keep `test_builtin_dispatch_strips_args` unchanged.

### Method

Append the four async test functions after the existing test; edit only the `out` stub line in
the fixture. All changes are confined to this test file.

### Details

- Assert tags via the `OutputTag` enum values (`OutputTag.ERROR == "[error]"`,
  `OutputTag.USAGE == "[usage]"`) and command-name presence (`"/mcp" in message`), never exact
  message bodies (`REQ-007`).
- The `write_fatal` assertion (`assert_not_called`) is what enforces `AC-1`/`AC-4` for the
  command path — a command error must not reach the turn-level `[fatal]` surface.
- The existing `tests/agent/test_repl_error_handling.py` already asserts the turn-failure
  `[fatal]` path (`AC-4`); this file does not re-test it.

## Compatibility considerations

Extending the `out` stub is backward compatible; the existing args-stripping test still passes.
The new tests only exercise the new handled-error path (a raising handler), which the current
`registry.py` does not handle — they fail today and pass once the implementation is in place.

## Security considerations

`N/A`: no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `uv run pytest tests/agent/commands/test_command_registry_dispatch.py -v` — the four new tests
  pass; the existing `test_builtin_dispatch_strips_args` still passes.
- `uv run pytest tests/agent/commands -q` then `uv run pytest tests/agent -q` — no regressions,
  including `test_command_def_sync.py` and `test_cmd_registry_note_removal.py`.
- `uv run ruff format scripts/agent tests/agent` ; `uv run ruff check scripts/agent tests/agent`
  ; `uv run mypy --no-namespace-packages scripts/agent tests/agent`.

## Completion criteria

The four handler-raises tests and the `caplog` assertion pass, asserting `[error]`/`[usage]`
tags and command-name presence (and no `[fatal]` from the command path); the pre-existing
args-stripping test and the turn-failure regression in `tests/agent/test_repl_error_handling.py`
still pass unchanged.

## Out of scope

`scripts/agent/commands/registry.py` (`REQ-001`–`REQ-005`, separate document),
`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (`REQ-008`),
`tests/agent/test_repl_error_handling.py` (`AC-4`, unchanged),
`tests/agent/commands/test_command_def_sync.py` (`AC-5`, unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the command-error regression tests + `caplog` assertion to `tests/agent/commands/test_command_registry_dispatch.py` (`REQ-007`) | Completed | 2026-10-23 | 2026-10-23 | AC-1, AC-2, AC-3, AC-7. Step 3b: tag is emitted by `CliOutputPort.write_*`, not in the body registry passes; assertions now target the emitting method + body. |
| 2 | Add or update tests per Validation plan | N/A: this document is the test addition | — | — | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-23 | 2026-10-23 | ruff/mypy clean; 5/5 dispatch tests pass; full suite 9695 passed / 14 skipped. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: documentation-only row | — | — | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocking unknown remains in this Plan | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261021-093421_cmd001-command-failures-surface-as-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-110616_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-013934
- **Related target files**: `tests/agent/commands/test_command_registry_dispatch.py`
