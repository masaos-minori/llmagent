## Goal

Make a failing slash-command handler surface as a command-scoped error (`[error]`/`[usage]`
tagged, command-attributed, logged) at the `CommandRegistry.dispatch()` boundary instead of
propagating to the REPL loop's turn-level `[fatal]` path.

## Scope

In scope: add command-boundary error handling around the handler invocation in
`scripts/agent/commands/registry.py` — classify the exception, render through the existing
`OutputPort.write_error` / `write_validation_error`, attribute the matched `CommandDef.name`
and `CommandDef.usages()` line, and log the error (`REQ-001`–`REQ-005`). Out of scope:
changing `dispatch()`'s `bool` return contract or `TypeError` guard (`AC-5`), the REPL loop
(`repl_input_loop.py`, `REQ-006`), the tag strings in `scripts/agent/output_tags.py`, argument
parsing/validation (`cmd002`), and event-loop blocking (`cmd003`). The companion regression
tests live in `tests/agent/commands/test_command_registry_dispatch.py` (`REQ-007`, separate
document).

## Assumptions

- Catching `Exception` (never `BaseException`) at the dispatch boundary is sufficient; handlers
  already raise the domain types for argument errors (`cmd_mcp.py:241`, `cmd_memory.py:125`
  raise `UnknownSubcommandError`).
- Keeping the handling in `dispatch()` rather than `_dispatch_line` is correct: `dispatch()`
  knows the matched `CommandDef` and its usage line; `_dispatch_line` does not.
- A module-level `logger` in `registry.py` matches repository conventions — sibling command
  modules already define one (`cmd_config.py`, `cmd_mcp.py`, `cmd_memory.py`).
- `sqlite3` is imported in `registry.py` (added during implementation; the pre-edit module did
  not import it, so this assumption was corrected at Step 3b) and `CommandValidationError` /
  `CommandParseError` come from `scripts/agent/commands/exceptions.py`.

## Design decisions

- **Classify inside a single private helper, not inline in `dispatch()`.** `dispatch()`'s
  cyclomatic complexity must stay at radon grade B (8); moving the render/classify logic into
  `_emit_command_error(cmd, exc)` keeps `dispatch()` flat.
- **Wrap only the handler invocation, not the lookup.** `_get_handler(cmd)` stays outside the
  guarded region — a missing-handler failure is a registry-integrity bug (`__init__` already
  fail-fasts on missing handlers), not a command error (`AC-5`).

## Alternatives considered

Catching the three exception types with inline `except` clauses at both invoke sites would
duplicate the try blocks across the prefix (L129-132) and exact (L133-136) match branches; a
single broad `except Exception` plus a classify-in-helper avoids that duplication while still
never catching `BaseException` (so `asyncio.CancelledError` / `KeyboardInterrupt` keep
propagating to `_repl_loop` shutdown handling).

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

1. Confirm the current state with `Read`: `dispatch()` (L115-138) awaits
   `_invoke_handler` (L105-113) with no `try`/`except`, and the module imports contain no
   `logging` import while `sqlite3` is already present.
2. Add `import logging` near the top imports and a module logger
   `logger = logging.getLogger(__name__)`, matching the sibling-module pattern.
3. Import the command domain exceptions used for classification:
   `from agent.commands.exceptions import CommandValidationError, CommandParseError`.
4. Extract the matched-handler invocation into a small private async helper
   `_run_matched_command(self, handler, cmd, *args) -> bool` that wraps
   `await self._invoke_handler(handler, cmd, *args)` in a single `except Exception as exc`
   branch which calls `self._emit_command_error(cmd, exc)` and returns `True`; the success
   path also returns `True`.
5. Add the private render-and-log helper `_emit_command_error(self, cmd, exc) -> None`:
   - `CommandValidationError` / `CommandParseError` (and subclasses such as
     `UnknownPresetError` / `UnknownTierError`) → `self._out.write_validation_error(...)`
     (`[usage]`).
   - `sqlite3.Error` → `self._out.write_error(...)` (`[error]`) with an explicit statement that
     the effect may be partial.
   - any other `Exception` → `self._out.write_error(...)` (`[error]`).
   - then log via `logger.error(...)`, naming the command and the exception type.
6. In `dispatch()`, call `_run_matched_command(...)` at both match sites and return its result;
   leave the `isinstance(line, str) -> TypeError` guard (L122-123), the empty-line
   `return False` (L124-125), and the unknown-command `return False` path unchanged, and keep
   `_get_handler(cmd)` outside the guarded region.

### Method

Insert the two imports, add the module logger, add the two private helpers, and replace the two
`await self._invoke_handler(...)` sites in `dispatch()` with
`return await self._run_matched_command(...)`. All changes are confined to `registry.py`.

### Details

- Attribution uses the matched `CommandDef`: `cmd.name` for the command name and, for prefix
  commands, `cmd.usages()` supplies the usage line (`command_defs.py` `CommandDef.usages()` /
  `format_usage()`). The rendered message must contain the command name so the regression tests
  can assert on it.
- `sqlite3.Error` wording (REQ-004) must name the subcommand and state the effect may be partial,
  e.g. `f"{cmd.name}: {exc} — the effect may be partial"`.
- Logging (REQ-005) must name the command and the exception type, e.g.
  `logger.error("command %s failed: %s: %s", cmd.name, exc.__class__.__name__, exc)`.
- Do NOT catch `BaseException`; `asyncio.CancelledError` / `KeyboardInterrupt` must keep
  propagating to `_repl_loop` shutdown-race handling (`repl_input_loop.py` L254-284).
- Direct handler-call behavior is untouched: handlers called outside `dispatch()` (e.g.
  `test_command_def_sync.py` asserting `UnknownSubcommandError`) still raise.

## Compatibility considerations

A command handler that raised before now renders `[error]`/`[usage]` and returns `True` from
`dispatch()`; the line is treated as matched. The turn-level `[fatal]` path
(`_surface_turn_error`, `repl_input_loop.py` L128-134) is no longer reached by command-handler
errors (`REQ-006`, `AC-4`). No other component is affected.

## Security considerations

`N/A`: no secret, permission, or data path is introduced. The change only affects how an
already-raised exception is surfaced and logged; it does not relax any access check.

## Rollback considerations

Revert the commit.

## Validation plan

- `uv run pytest tests/agent/commands/test_command_registry_dispatch.py -v` — new command-error
  surface tests pass; `[error]`/`[usage]` asserted by tag; no `[fatal]` from the command path.
- `uv run pytest tests/agent/test_repl_error_handling.py -v` — turn failure still surfaces via
  `view.write_fatal` unchanged (`AC-4`).
- `uv run pytest tests/agent/commands -q` — all pass, including `test_command_def_sync.py` and
  `test_cmd_registry_note_removal.py` (`AC-5`).
- `uv run ruff format scripts/agent` ; `uv run ruff check scripts/agent` ;
  `uv run mypy --no-namespace-packages scripts/agent` ;
  `uv run radon cc scripts/agent/commands/registry.py -s` (dispatch stays grade B; helper
  extracted) ; `uv run python tools/check_module_size.py` (module under 16384 B).
- `uv run pytest -q` + changed-line coverage via `coverage run -m pytest tests/` →
  `coverage xml` → `diff-cover coverage.xml --compare-branch=master` (≥ 90%).

## Completion criteria

`dispatch()` catches handler-invocation exceptions, renders each through the correct severity
(`[usage]` for command domain validation/parse errors, `[error]` otherwise, `[error]` with a
partial-effect statement for `sqlite3.Error`), logs the attributed error, and returns `True`;
the `bool` return contract, the `TypeError` guard, and direct handler-call behavior are
unchanged; no command-handler error reaches `_surface_turn_error`.

## Out of scope

`tests/agent/commands/test_command_registry_dispatch.py` (`REQ-007`, separate document),
`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (`REQ-008`, separate document),
`scripts/agent/repl_input_loop.py` (unchanged, `REQ-006`), `scripts/agent/output_tags.py` (tag
strings unchanged), argument parsing (`cmd002`), event-loop blocking (`cmd003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement command-boundary error classification, rendering and logging in `scripts/agent/commands/registry.py` (`REQ-001`–`REQ-005`) | Completed | 2026-10-23 | 2026-10-23 | AC-1, AC-2, AC-3, AC-5, AC-7. Step 3b: `sqlite3` was NOT pre-imported in `registry.py`; added `import sqlite3` (needed for `sqlite3.Error` classification). |
| 2 | Add or update tests per Validation plan (companion tests in `test_command_registry_dispatch.py`) | Completed | 2026-10-23 | 2026-10-23 | AC-7. Step 3b: procedure asserted `OutputTag.*` inside the rendered body, but the tag is added by `CliOutputPort.write_*` (registry passes the raw body); rewritten to assert on the emitting method + body. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-23 | 2026-10-23 | ruff/mypy/import-linter/bandit clean; radon `dispatch()` grade B(8); module size OK; full suite 9695 passed / 14 skipped; diff-cover 100%. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: docs handled by companion doc | — | — | REQ-008 is a separate row |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261021-093421_cmd001-command-failures-surface-as-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-110616_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-013934
- **Related target files**: `scripts/agent/commands/registry.py`
