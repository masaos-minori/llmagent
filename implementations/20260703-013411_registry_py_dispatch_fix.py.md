# Implementation: scripts/agent/commands/registry.py — Fix exact-match dispatch to call handlers with no argument

**Plan source:** `plans/20260702-202758_plan.md` (Phase 1 + Phase 2)
**Target file:** `scripts/agent/commands/registry.py`

---

## Goal

`CommandRegistry.dispatch()` currently passes an empty string `""` to exact-match (`prefix=False`) command handlers, but those handlers take no positional arguments. Remove the `""` argument from both call sites and add test coverage to confirm correct dispatch behavior for both exact-match and prefix commands.

---

## Scope

**In:**
- `scripts/agent/commands/registry.py` — remove `""` from `handler("")` and `await handler("")` in the exact-match `else` branch of `dispatch()` (lines 297-303)
- `_get_handler` return type annotation — widen or suppress so zero-arg call sites typecheck cleanly
- `tests/` — add or update tests for exact-match dispatch (`/help`, `/compact`) and prefix dispatch (`/db help`, `/rag search test`)

**Out:**
- `/exit` handling
- `sqlite-vec` path handling
- Plugin command dispatch (`_dispatch_plugin`)
- Large-scale command registry redesign
- Duplication between `_COMMANDS` in `registry.py` and `command_defs.py`

---

## Assumptions

1. All `prefix=False` handler methods (`_cmd_help`, `_cmd_config`, `_cmd_stats`, `_cmd_context`, `_cmd_plan`, `_cmd_undo`, `_cmd_reload`, `_cmd_compact`) take no positional arguments beyond `self`. Confirmed by reading source in the plan.
2. The existing prefix-match branch is correct and must not change.
3. `dispatch()` is called only from `agent/repl.py` `_repl_loop`; blast radius is confined to exact-match command execution.
4. `# type: ignore[misc]` is already present on the handler call sites; widening `_get_handler` return type to `Callable[..., ...]` is an acceptable alternative.

---

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

1. Open `scripts/agent/commands/registry.py` and locate the exact-match `else` branch of `dispatch()` (around lines 297-303).
2. Change `await handler("")` to `await handler()` in the async call site.
3. Change `handler("")` to `handler()` in the sync call site.
4. Inspect the `_get_handler` return type annotation. If it is `Callable[[str], None] | Callable[[str], Awaitable[None]]`, either:
   - Replace with `Callable[..., None] | Callable[..., Awaitable[None]]` (preferred — removes the string-arg constraint), or
   - Leave as-is and retain the existing `# type: ignore[misc]` comment on each call site.
5. Add/update tests in `tests/` (see Details section below).
6. Run the validation steps.

### Method

Edit tool for code changes in `scripts/agent/commands/registry.py`.
Write tool or Edit tool for new/updated test file in `tests/`.

### Details

**Before (exact-match else branch):**
```python
else:
    if line == cmd.name:
        if cmd.is_async:
            await handler("")  # type: ignore[misc]
        else:
            handler("")
        return True
```

**After:**
```python
else:
    if line == cmd.name:
        if cmd.is_async:
            await handler()  # type: ignore[misc]
        else:
            handler()
        return True
```

**Test cases to add (suggested file: `tests/test_dispatch_arg_handling.py`):**

| Test | Setup | Assertion |
|---|---|---|
| `test_exact_match_help_no_arg` | Mock `_cmd_help`; call `dispatch("/help")` | `_cmd_help` called with no args; no `TypeError` |
| `test_exact_match_compact_no_arg` | Mock `_cmd_compact`; call `dispatch("/compact")` | `_cmd_compact` called with no args; no `TypeError` |
| `test_prefix_db_passes_remainder` | Mock `_cmd_db`; call `dispatch("/db help")` | `_cmd_db` called with `" help"` |
| `test_prefix_rag_passes_remainder` | Mock `_cmd_rag`; call `dispatch("/rag search test")` | `_cmd_rag` called with `" search test"` |

Confirm existing tests in `tests/test_cmd_registry_ingest_removal.py`, `tests/test_removed_commands.py`, and `tests/test_repl.py` still pass.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | `ruff check scripts/agent/commands/registry.py` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Targeted tests | `uv run pytest tests/test_repl.py tests/test_cmd_registry_ingest_removal.py tests/test_removed_commands.py -v` | all pass |
| Full test suite | `uv run pytest` | all pass |
