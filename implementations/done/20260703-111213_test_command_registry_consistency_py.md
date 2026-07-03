# Implementation: tests/test_command_registry_consistency.py — Parametrized per-command tests and final validation

**Plan source:** `plans/20260703-104216_plan.md` (Steps 2–3)  
**Target file:** `tests/test_command_registry_consistency.py`

---

## Goal

Determine whether per-command `@pytest.mark.parametrize` tests are needed to close any coverage gap (Step 2), then run the full validation suite to confirm all acceptance criteria pass (Step 3).

---

## Scope

- In-Scope:
  - Gap analysis: map each acceptance criterion to an existing test and confirm coverage
  - Conditional addition of `@pytest.mark.parametrize("cmd", _COMMANDS, ids=lambda c: c.name)` test(s) to `tests/test_command_registry_consistency.py` if any acceptance criterion lacks individual per-command test granularity
  - Final validation run: `uv run pytest tests/ -k command --ignore=...` to confirm no regressions
- Out-of-Scope:
  - Changes to source files (`registry.py`, `command_defs.py`, `command_defs_list.py`)
  - Testing external LLM, MCP, DB, or embedding services
  - `/exit` handling, sqlite-vec path handling, plugin command execution

---

## Assumptions

1. The 18 tests in `tests/test_command_registry_consistency.py` already fully satisfy all four acceptance criteria from `requires/20260703_01_require.md`; Step 2 additions are only needed if per-command isolation is desired for faster failure diagnosis.
2. The existing `MagicMock`-based `registry` fixture is sufficient; no new fixture is required for parametrized tests.
3. `_COMMANDS` from `agent.commands.command_defs_list` is the correct source of truth (the import already uses `command_defs_list`, not `command_defs`).
4. `uv run pytest tests/ -k command` without `--ignore` flags may collect failing modules unrelated to command tests; the ignore list from the plan must be applied to get a clean run.
5. Adding parametrized tests increases test count from 18 to 18 + len(_COMMANDS); as of this plan `_COMMANDS` has 25 entries, so the new count would be 43 if one parametrized test is added.

---

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_command_registry_consistency.py`

### Procedure

1. Run gap analysis: `uv run pytest tests/test_command_defs.py tests/test_command_registry_consistency.py -v` and verify all 18 tests pass and each acceptance criterion is covered by at least one test:
   - Acceptance criterion 1 (missing handler fails): `test_all_handlers_exist_on_registry`
   - Acceptance criterion 2 (exact handler requiring `args` fails): `test_exact_handlers_have_no_required_params`
   - Acceptance criterion 3 (prefix handler not accepting `args` fails): `test_prefix_handlers_accept_args_param`
   - Acceptance criterion 4 (wrong `is_async` flag fails): `test_async_handlers_are_coroutines` + `test_sync_handlers_are_not_coroutines`
2. **If** all 18 pass and all criteria are covered, proceed directly to Step 6 (final validation) without adding any new tests.
3. **If** a gap is found (any acceptance criterion is not covered), add the following parametrized test to the `TestCommandRegistryConsistency` class in `tests/test_command_registry_consistency.py`, inserting it after `test_prefix_handlers_accept_args_param`:

```python
@pytest.mark.parametrize("cmd", _COMMANDS, ids=lambda c: c.name)
def test_handler_signature_per_command(
    self, cmd: CommandDef, registry: CommandRegistry
) -> None:
    assert hasattr(registry, cmd.handler), (
        f"{cmd.name}: handler '{cmd.handler}' missing from CommandRegistry"
    )
    fn = getattr(registry, cmd.handler)
    if cmd.is_async:
        assert inspect.iscoroutinefunction(fn), (
            f"{cmd.handler}: expected coroutine, got sync"
        )
    else:
        assert not inspect.iscoroutinefunction(fn), (
            f"{cmd.handler}: expected sync, got coroutine"
        )
    sig = inspect.signature(fn)
    positional = [
        p
        for p in sig.parameters.values()
        if p.kind
        in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        )
    ]
    if cmd.prefix:
        assert len(positional) >= 1, (
            f"{cmd.handler}: prefix handler must accept at least one positional param"
        )
    else:
        required = [
            p for p in positional if p.default is inspect.Parameter.empty
        ]
        assert required == [], (
            f"{cmd.handler}: exact-match handler must have no required params, "
            f"found {[p.name for p in required]}"
        )
```

4. Add `CommandDef` to imports if the parametrized test is added: `from agent.commands.command_defs import CommandDef`
5. Run lint and type check on the modified file:
   - `uv run ruff check tests/test_command_registry_consistency.py`
   - `uv run mypy tests/test_command_registry_consistency.py`
6. Run final validation:
   ```
   uv run pytest tests/ -k command \
     --ignore=tests/test_agent_cmd_context.py \
     --ignore=tests/test_cmd_context_refactor.py \
     --ignore=tests/test_delete_chain.py \
     --ignore=tests/test_shell_mcp_service.py \
     -v
   ```

### Method

- `@pytest.mark.parametrize("cmd", _COMMANDS, ids=lambda c: c.name)`: generates one test item per `CommandDef`, identified by the command name (e.g., `/help`, `/session`, `/rag`)
- `inspect.signature(fn).parameters`: returns an `OrderedDict[str, Parameter]`; for bound methods `self` is already excluded
- `inspect.Parameter.POSITIONAL_OR_KEYWORD` and `inspect.Parameter.POSITIONAL_ONLY`: the two kinds that count as positional for this check
- `p.default is inspect.Parameter.empty`: distinguishes required from optional parameters
- The `ids=lambda c: c.name` argument makes test IDs human-readable in pytest output and in failure messages

### Details

- `_COMMANDS` is imported as `from agent.commands.command_defs_list import _COMMANDS` (already present in the file at line 12)
- `CommandDef` import lives in `agent.commands.command_defs` (separate from `command_defs_list`)
- Existing class `TestCommandRegistryConsistency` at line 27; append the new method after `test_prefix_handlers_accept_args_param` (line 76)
- Current `_COMMANDS` has 25 entries (8 exact-match, 17 prefix); the parametrized test would add 25 items
- The `registry` fixture at line 16 uses `MagicMock()` for `ctx`; this is compatible with the parametrized approach since `CommandRegistry.__init__` is called once per class-level fixture scope

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Gap analysis | `uv run pytest tests/test_command_defs.py tests/test_command_registry_consistency.py -v` | 18 passed, all 4 acceptance criteria covered |
| Import check (if modified) | `uv run pytest tests/test_command_registry_consistency.py --collect-only` | No import errors; 18 or 43 items collected |
| Lint (if modified) | `uv run ruff check tests/test_command_registry_consistency.py` | 0 errors |
| Type check (if modified) | `uv run mypy tests/test_command_registry_consistency.py` | 0 errors |
| Final validation | `uv run pytest tests/ -k command --ignore=tests/test_agent_cmd_context.py --ignore=tests/test_cmd_context_refactor.py --ignore=tests/test_delete_chain.py --ignore=tests/test_shell_mcp_service.py -v` | All command-related tests pass; no regressions |
