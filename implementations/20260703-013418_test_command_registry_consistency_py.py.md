# Implementation: tests/test_command_registry_consistency.py — Scaffold and implement CommandDef/handler consistency tests

**Plan source:** `plans/20260702-202801_plan.md` (Phases 1-2)
**Target file:** `tests/test_command_registry_consistency.py`

---

## Goal

Create a new test file that validates all built-in `CommandDef` entries in `command_defs._COMMANDS` against the actual handler methods on `CommandRegistry`, so that signature mismatches and missing handlers are caught at CI time rather than at runtime.

---

## Scope

**In:**
- Fixture that instantiates `CommandRegistry` with a minimal mock `AgentContext` using `SimpleNamespace` (same pattern as `test_cmd_workflow.py`)
- TC-01: every `CommandDef.handler` string in `command_defs._COMMANDS` exists as an attribute on the `CommandRegistry` instance (`hasattr`)
- TC-02: handlers where `is_async=True` pass `inspect.iscoroutinefunction()`
- TC-03: handlers where `is_async=False` fail `inspect.iscoroutinefunction()`
- TC-04: handlers where `prefix=False` (exact-match) have zero required positional parameters after `self` (checked via `inspect.signature`)
- TC-05: handlers where `prefix=True` accept at least one positional parameter for `args` (checked via `inspect.signature`)
- Tests must run without starting external MCP servers or any LLM/embed service

**Out:**
- Testing actual MCP server behavior
- Testing `/exit` command
- Testing sqlite-vec behavior
- Testing plugin command dispatch (`_dispatch_plugin`)
- End-to-end dispatch integration tests
- Modifying `registry.py` or `command_defs.py`

---

## Assumptions

1. `CommandRegistry` can be instantiated with a `SimpleNamespace`-based mock `AgentContext`, following the pattern established in `tests/test_cmd_workflow.py`.
2. `command_defs._COMMANDS` is the single source of truth; `registry._COMMANDS` is a known duplicate with divergences (handled separately).
3. `inspect.signature()` correctly reflects the calling convention for bound methods on `CommandRegistry`.
4. For TC-04, "zero required positional parameters after `self`" means: all remaining `POSITIONAL_OR_KEYWORD` and `POSITIONAL_ONLY` parameters have defaults, or there are none.
5. For TC-05, "at least one positional parameter" means: at least one `POSITIONAL_OR_KEYWORD` or `POSITIONAL_ONLY` parameter without a default exists after `self`.
6. `_cmd_help` has signature `(self)` with no `args` parameter — TC-04 should surface this as a known bug (the dispatch calls `handler("")`); document with a comment but do not skip the test.

---

## Implementation

### Target file

`tests/test_command_registry_consistency.py`

### Procedure

1. Create `tests/test_command_registry_consistency.py`
2. Add imports: `inspect`, `types.SimpleNamespace`, `pytest`, `agent.commands.command_defs._COMMANDS`, `agent.commands.registry.CommandRegistry`
3. Define a `registry` fixture that builds a minimal `SimpleNamespace` mock for `AgentContext` and returns a `CommandRegistry` instance
4. Implement `TestCommandRegistryConsistency` class with five test methods covering TC-01 through TC-05
5. Verify the file runs with `uv run pytest tests/test_command_registry_consistency.py` (no import errors)

### Method

Write tool for new file creation.

### Details

**Fixture pattern** (based on `test_cmd_workflow.py`):

```python
import inspect
from types import SimpleNamespace

import pytest
from agent.commands.command_defs import _COMMANDS
from agent.commands.registry import CommandRegistry


def _make_ctx() -> SimpleNamespace:
    """Minimal AgentContext stub — no external services started."""
    return SimpleNamespace(
        config=SimpleNamespace(
            llm=SimpleNamespace(model="test", temperature=0.0, max_tokens=1024),
            rag=SimpleNamespace(enabled=False),
        ),
        history=[],
        session=SimpleNamespace(id="test-session"),
        turn=SimpleNamespace(pending_approval_id=None),
        workflow=SimpleNamespace(approval_pending=False),
        stats=SimpleNamespace(turns=0, tool_calls=0, rag_hits=0, errors=0),
        memory_layer=None,
        mcp_manager=None,
    )


@pytest.fixture()
def registry() -> CommandRegistry:
    ctx = _make_ctx()
    out = SimpleNamespace(
        write=lambda msg: None,
        write_error=lambda msg: None,
        write_validation_error=lambda msg: None,
    )
    return CommandRegistry(ctx=ctx, out=out)
```

**TC-01** (handler existence):
```python
def test_all_handlers_exist_on_registry(self, registry: CommandRegistry) -> None:
    missing = [
        cmd.handler
        for cmd in _COMMANDS
        if not hasattr(registry, cmd.handler)
    ]
    assert missing == [], f"Handlers missing from CommandRegistry: {missing}"
```

**TC-02** (is_async=True are coroutines):
```python
def test_async_handlers_are_coroutines(self, registry: CommandRegistry) -> None:
    errors = []
    for cmd in _COMMANDS:
        if cmd.is_async and hasattr(registry, cmd.handler):
            fn = getattr(registry, cmd.handler)
            if not inspect.iscoroutinefunction(fn):
                errors.append(cmd.handler)
    assert errors == [], f"Expected coroutines but got sync: {errors}"
```

**TC-03** (is_async=False are not coroutines):
```python
def test_sync_handlers_are_not_coroutines(self, registry: CommandRegistry) -> None:
    errors = []
    for cmd in _COMMANDS:
        if not cmd.is_async and hasattr(registry, cmd.handler):
            fn = getattr(registry, cmd.handler)
            if inspect.iscoroutinefunction(fn):
                errors.append(cmd.handler)
    assert errors == [], f"Expected sync but got coroutines: {errors}"
```

**TC-04** (prefix=False exact-match: zero required positional params after self):
```python
def test_exact_handlers_have_no_required_params(self, registry: CommandRegistry) -> None:
    # NOTE: dispatch calls handler("") for exact-match commands.
    # Handlers with zero required params (no args parameter) signal a bug
    # where dispatch passes "" but the handler cannot accept it.
    # This test validates the contract: exact-match handlers must have
    # zero *required* positional parameters after self.
    errors = []
    for cmd in _COMMANDS:
        if not cmd.prefix and hasattr(registry, cmd.handler):
            fn = getattr(registry, cmd.handler)
            sig = inspect.signature(fn)
            required = [
                p for p in sig.parameters.values()
                if p.kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.POSITIONAL_ONLY,
                )
                and p.default is inspect.Parameter.empty
            ]
            if required:
                errors.append(f"{cmd.handler}: required params {[p.name for p in required]}")
    assert errors == [], f"Exact-match handlers with required params: {errors}"
```

**TC-05** (prefix=True prefix-match: at least one positional param for args):
```python
def test_prefix_handlers_accept_args_param(self, registry: CommandRegistry) -> None:
    errors = []
    for cmd in _COMMANDS:
        if cmd.prefix and hasattr(registry, cmd.handler):
            fn = getattr(registry, cmd.handler)
            sig = inspect.signature(fn)
            positional = [
                p for p in sig.parameters.values()
                if p.kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.VAR_POSITIONAL,
                )
            ]
            if not positional:
                errors.append(cmd.handler)
    assert errors == [], f"Prefix handlers missing positional param: {errors}"
```

**Note on `CommandRegistry` constructor**: The exact signature of `CommandRegistry.__init__` may differ from the mock built above. If `CommandRegistry` requires additional fields or uses a different argument name (e.g., `context` vs `ctx`), adjust the fixture to match the actual constructor. Run `uv run pytest tests/test_command_registry_consistency.py` first to catch import/init errors before adding the full test suite.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Import check | `uv run pytest tests/test_command_registry_consistency.py --collect-only` | No import errors, 5 test items collected |
| Tests | `uv run pytest tests/test_command_registry_consistency.py -v` | All pass (or known failures documented with comments) |
| Regression | `uv run pytest tests/ -k command` | Existing command tests still pass |
| Lint | `ruff check tests/test_command_registry_consistency.py` | 0 errors |
| Type check | `mypy tests/test_command_registry_consistency.py` | no new errors |
| Full suite | `uv run pytest` | all pass |
