# Goal

Narrow `except Exception` in `load_plugins()` to specific exception types, and add
a `ToolHandler` type alias for registered tool handlers.

# Scope

- `scripts/shared/plugin_registry.py`

# Assumptions

1. Plugin load failures are expected to be `ImportError` (bad import), `SyntaxError`
   (malformed Python), or `AttributeError` (decorator registration failure).
   Other exceptions (e.g. from `exec_module`) propagate upward.
2. `ToolHandler` type alias: `Callable[[dict[str, Any]], Awaitable[tuple[str, bool]]]`.
   This does not change runtime behavior; it only adds type annotation support.
3. The existing `_tools: dict[str, Callable[..., Any]]` registry type is left unchanged
   since changing it to `dict[str, ToolHandler]` would require `Callable` covariance
   considerations. The alias is added for documentation and annotation use only.

# Implementation

## Target file

`scripts/shared/plugin_registry.py`

## Procedure

1. Add `ToolHandler` type alias after the imports section:
   ```python
   from collections.abc import Awaitable
   ToolHandler = Callable[[dict[str, Any]], Awaitable[tuple[str, bool]]]
   ```
2. Change `except Exception as e:` in `load_plugins()` to:
   ```python
   except (ImportError, SyntaxError, AttributeError) as e:
   ```
3. Run ruff + mypy.

## Method

One exception narrowing + one type alias addition.

## Details

```python
# load_plugins() — before
        except Exception as e:
            logger.warning("Plugin load failed (%s): %s", py_file.name, e)

# load_plugins() — after
        except (ImportError, SyntaxError, AttributeError) as e:
            logger.warning("Plugin load failed (%s): %s", py_file.name, e)
```

# Validation plan

- `grep -n "except Exception" scripts/shared/plugin_registry.py` → 0 hits
- `uv run ruff check scripts/shared/plugin_registry.py`
- `uv run mypy scripts/shared/plugin_registry.py`
- `uv run pytest tests/ -k "plugin" --ignore=tests/test_create_schema.py -v`
