## Goal

Apply `.strip()` to the `args` string extracted in both built-in and plugin prefix dispatch branches of `CommandRegistry`, so all prefix command handlers receive whitespace-normalized argument strings.

## Scope

- In-Scope:
  - Line 123 of `scripts/agent/commands/registry.py`: add `.strip()` to `args = line[len(cmd.name) :]`
  - Line 145 of `scripts/agent/commands/registry.py`: add `.strip()` to `args = line[len(cmd_name) :]`
- Out-of-Scope:
  - Removing defensive `.strip()` calls already present in individual handler methods (`cmd_db.py`, `cmd_session.py`, etc.)
  - Changing `/exit` handling or the plugin command conflict policy
  - Any handler files outside `registry.py`

## Assumptions

1. The only callers of `dispatch()` are the REPL loop and existing tests; none expect un-stripped args.
2. `.strip()` on an already-stripped string is a no-op; existing handler-level `.strip()` calls remain harmless.
3. `line.startswith(cmd.name + " ")` guarantees at least one leading space in `line[len(cmd.name):]`; stripping that space is the intended fix.
4. Plugin commands follow the same pattern: `line.startswith(cmd_name)` can match with no trailing space; stripping an empty string is also safe.

## Implementation

### Target file

`/home/masaos/llmagent/scripts/agent/commands/registry.py`

### Procedure

1. Open `registry.py` and locate the `dispatch()` method (line ~108).
2. Find the built-in prefix branch (currently line 123):
   ```python
   args = line[len(cmd.name) :]
   ```
   Replace with:
   ```python
   args = line[len(cmd.name) :].strip()
   ```
3. Locate `_dispatch_plugin()` (currently line 140).
4. Find the plugin prefix branch (currently line 145):
   ```python
   args = line[len(cmd_name) :]
   ```
   Replace with:
   ```python
   args = line[len(cmd_name) :].strip()
   ```
5. Save the file; no import changes are needed.

### Method

- Single-expression change: append `.strip()` to the slice expression on each line.
- `str.strip()` with no argument removes all leading and trailing whitespace (spaces, tabs, newlines).
- The type annotation `args: str` in `_dispatch_plugin` remains correct; `.strip()` returns `str`.

### Details

- `dispatch()` built-in branch — exact location:
  ```python
  if cmd.prefix:
      if line == cmd.name or line.startswith(cmd.name + " "):
          args = line[len(cmd.name) :]          # ← change this line
  ```
- `_dispatch_plugin()` plugin branch — exact location:
  ```python
  if is_prefix and line.startswith(cmd_name):
      args = line[len(cmd_name) :]              # ← change this line
  elif not is_prefix and line == cmd_name:
      pass  # args stays empty
  ```
- Both surrounding contexts already use `args` as `str`; no type annotation updates needed.
- Existing `args.strip().split(None, 1)` calls in `cmd_db.py` (lines 36, 55, 78) and `args.strip().split()` in `cmd_session.py` (line 122) remain functionally correct (double `.strip()` is a no-op).

## Validation plan

| Check | Command | Expected outcome |
|-------|---------|-----------------|
| Ruff lint clean | `uv run ruff check scripts/agent/commands/registry.py` | Zero violations |
| mypy type check | `uv run mypy scripts/agent/commands/registry.py` | Zero errors |
| Full test suite (no regressions) | `uv run pytest` | All existing tests pass |
