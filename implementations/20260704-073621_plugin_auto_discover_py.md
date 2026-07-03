# Implementation: Add `ValueError` to `load_plugins()` except tuple in `plugin_auto_discover.py`

## Goal

Add `ValueError` to the exception catch tuple in `load_plugins()` so that a plugin whose
`@register_tool` decorator raises `ValueError` (missing or wrong return-type annotation) is
recorded as a `PluginFailure` entry rather than propagating to the caller as an unhandled exception.

## Scope

- In-Scope: One-line change to `scripts/shared/plugin_auto_discover.py` line 62 — add `ValueError`
  to the existing `except` tuple.
- Out-of-Scope: No changes to `register_tool()`, `ToolExecutor.execute()`, tests, or documentation
  (tests and docs for this bug are already covered by existing `implementations/done/` entries).

## Assumptions

1. `load_plugins()` is the single location that must be updated; no other caller silently swallows
   or depends on `ValueError` propagating from `load_plugins()`.
2. Raising `ValueError` from `register_tool()` during plugin import is logically equivalent to
   `ImportError` for `load_plugins()` purposes — both represent a failure to load the plugin.
3. `_tools[name] = (fn, ...)` in `register_tool` is only executed after both annotation checks pass,
   so an invalid tool is never inserted into the registry even under non-strict mode.
4. `grep -rn "load_plugins" scripts/` shows only `factory.py` and tests call `load_plugins()`;
   none expect `ValueError` to propagate.
5. The existing `type: ignore` comments on line 117 of `plugin_auto_discover.py` are pre-existing
   and must not be removed.

## Implementation

### Target file

`scripts/shared/plugin_auto_discover.py`

### Procedure

1. Read line 62 to confirm the current except tuple.
2. Add `ValueError` to the tuple at line 62.
3. Run `uv run ruff format scripts/shared/plugin_auto_discover.py` and
   `uv run ruff check scripts/shared/plugin_auto_discover.py` to confirm 0 errors.
4. Run `uv run mypy scripts/shared/plugin_auto_discover.py` — expect 2 pre-existing
   `Invalid "type: ignore" comment` errors at lines 117/123; no new errors.
5. Run `uv run pytest tests/test_plugin_registry.py -v` to confirm no regressions.

### Method

**Line 62 — current:**
```python
        except (ImportError, SyntaxError, AttributeError, RuntimeError) as e:
```

**Line 62 — after change:**
```python
        except (ImportError, SyntaxError, AttributeError, RuntimeError, ValueError) as e:
```

No other lines change.

### Details

- `ValueError` is raised by `register_tool()` in two cases:
  - Missing return type annotation: `raise ValueError("... missing return type annotation ...")`
  - Wrong return type: `raise ValueError("... expected return type ...")`
- Both cases occur during `spec.loader.exec_module(mod)` on line 59, inside the existing try block.
- After the fix, both cases are caught, a `PluginFailure` is appended with the full error message,
  and a `WARNING` log line is emitted: `[plugin] skipped: <filename> (ValueError)`.
- In strict mode, the failure is aggregated into the `PluginLoadError` message at line 88.
- The `finally` block at line 66 already resets `_current_loading_module[0]`, so no change needed there.

## Validation plan

```bash
# Lint
uv run ruff check scripts/shared/plugin_auto_discover.py
# Expected: 0 errors

# Type check (2 pre-existing errors on lines 117/123 are expected; no new errors)
uv run mypy scripts/shared/plugin_auto_discover.py

# Full plugin registry test suite
uv run pytest tests/test_plugin_registry.py -v
# Expected: all existing tests pass

# Integration tests added for this bug (already in done/)
uv run pytest tests/test_plugin_registry.py::TestPluginToolContractLoadIntegration -v
# Expected: 3 passed (missing_annotation, wrong_annotation, strict_mode_raises)
```
