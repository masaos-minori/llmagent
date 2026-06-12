# Goal

Replace the string-based `handler` field in `CommandDef` with a typed `Callable`
reference so that dispatching is no longer stringly-typed and `getattr()` lookups
are replaced with direct callable invocation.

# Scope

- `scripts/agent/commands/registry.py`

# Assumptions

1. `CommandDef.handler: str` currently holds a method name (e.g. `"_cmd_memory"`).
2. `dispatch()` calls `getattr(self, cmd.handler)` to look up the method at runtime.
3. Replacing `handler: str` with `handler: Callable[..., Any]` requires the
   `_COMMANDS` list to be built inside `CommandRegistry.__init__` (since `self` is
   needed to bind the methods) or as class-level lambdas that close over `self`.
4. The simplest approach: keep `_COMMANDS` as a class-level list of `CommandDef`
   with `handler: str`, but add a separate `_resolve_handler(cmd: CommandDef)` method
   that returns the bound callable. This avoids re-building the list per instance
   while still allowing type-safe dispatch.
5. Alternatively: change `CommandDef.handler` to `handler: str` with a strict
   validator that asserts the method exists at `__init__` time (fail-fast at startup
   rather than at dispatch time). This is the minimum change.

**Chosen approach (minimum blast radius):** Add runtime validation in
`CommandRegistry.__init__` that all `handler` strings refer to existing methods,
plus add a `_get_handler(cmd: CommandDef) -> Callable[[], Any]` helper that returns
the bound callable. `dispatch()` uses `_get_handler()` instead of bare `getattr()`.

# Implementation

## Target file

`scripts/agent/commands/registry.py`

## Procedure

1. Add `_get_handler()` method to `CommandRegistry`:
   ```python
   def _get_handler(self, cmd: CommandDef) -> Callable[..., Any]:
       handler = getattr(self, cmd.handler, None)
       if handler is None:
           raise AttributeError(
               f"CommandRegistry has no handler method {cmd.handler!r}"
           )
       return handler
   ```
2. In `CommandRegistry.__init__`, validate all handlers exist:
   ```python
   for cmd in _COMMANDS:
       if not hasattr(self, cmd.handler):
           raise AttributeError(
               f"CommandDef references unknown handler: {cmd.handler!r}"
           )
   ```
3. In `dispatch()`, replace:
   ```python
   handler = getattr(self, cmd.handler)
   ```
   with:
   ```python
   handler = self._get_handler(cmd)
   ```
4. Add type annotation for `_get_handler` return using `collections.abc.Callable`.
5. Run ruff + mypy.

## Method

Fail-fast validation at `__init__` time (not only at dispatch time) and a typed
accessor replaces the bare `getattr` call. `CommandDef.handler: str` is kept since
the string table is the simplest data format, but usage is now gated through a
typed accessor.

## Details

The validation in `__init__` ensures any typo in `_COMMANDS` raises immediately on
startup rather than producing a runtime `AttributeError` mid-session. The
`_get_handler()` method is the single place where the `str → Callable` conversion
happens, making it easy to audit.

# Validation plan

- `uv run ruff check scripts/agent/commands/registry.py`
- `uv run mypy scripts/agent/commands/registry.py`
- `uv run pytest tests/ -k "registry or dispatch" --ignore=tests/test_create_schema.py -v`
- Introduce a deliberate typo in one handler name → verify `AttributeError` raised at
  `CommandRegistry()` construction, not at `dispatch()` call time
