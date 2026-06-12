# Implementation: agent/repl_health.py — Replace assert + narrow except Exception

## Goal

Replace 3 `assert` statements with `RuntimeError` guards and narrow 5 `except Exception` clauses to specific exception types in `scripts/agent/repl_health.py`.

## Scope

**In:** `scripts/agent/repl_health.py`
**Out:** No other files change.

## Assumptions

1. All three assert guards check `ctx.services.http is not None`; the HTTP client is set by the factory and a None value is a programming error.
2. `probe_mcp_health` swallows all exceptions and returns `False`; narrowing to `(httpx.HTTPError, OSError, asyncio.TimeoutError)` covers all network failure modes.
3. `check_service_health` swallows network errors and appends a warning; `(httpx.HTTPError, OSError)` is sufficient.
4. `_collect_server_tool_names` (HTTP branch) swallows network errors; `(httpx.HTTPError, OSError)` is sufficient.
5. Watchdog restart calls (`lifecycle.restart()` / `lifecycle.restart_stdio()`) raise `HttpStartupError(RuntimeError)` or `OSError`; `(OSError, RuntimeError)` covers both.

## Implementation

### Target file

`scripts/agent/repl_health.py`

### Procedure

1. Replace `assert ctx.services.http is not None` (×3) with explicit RuntimeError guards.
2. Narrow `probe_mcp_health` bare `except Exception:` to `(httpx.HTTPError, OSError, asyncio.TimeoutError)`.
3. Narrow `check_service_health` `except Exception as e:` to `(httpx.HTTPError, OSError)`.
4. Narrow `_collect_server_tool_names` `except Exception as e:` to `(httpx.HTTPError, OSError)`.
5. Narrow watchdog restart `except Exception as e:` (×2) to `(OSError, RuntimeError)`.

### Method

Targeted in-place edits. No structural changes.

### Details

**Assert replacements (3 occurrences of `assert ctx.services.http is not None`):**
```python
# Before
assert ctx.services.http is not None

# After
if ctx.services.http is None:
    raise RuntimeError("http service not initialized")
```

**probe_mcp_health (line ~33):**
```python
# Before
except Exception:
    return False

# After
except (httpx.HTTPError, OSError, asyncio.TimeoutError):
    return False
```

**check_service_health (line ~60):**
```python
# Before
except Exception as e:
    msg = f"{label} unreachable at {health_url}: {e}"

# After
except (httpx.HTTPError, OSError) as e:
    msg = f"{label} unreachable at {health_url}: {e}"
```

**_collect_server_tool_names HTTP branch (line ~107):**
```python
# Before
except Exception as e:
    logger.warning(f"Cannot reach {srv_cfg.url}/v1/tools: {e}")

# After
except (httpx.HTTPError, OSError) as e:
    logger.warning(f"Cannot reach {srv_cfg.url}/v1/tools: {e}")
```

**Watchdog restart — HTTP (line ~186):**
```python
# Before
except Exception as e:
    logger.error(f"Watchdog: failed to restart {key!r}: {e}")

# After
except (OSError, RuntimeError) as e:
    logger.error(f"Watchdog: failed to restart {key!r}: {e}")
```

**Watchdog restart — stdio (line ~236):**
```python
# Before
except Exception as e:
    logger.error(f"Watchdog: failed to restart stdio server {key!r}: {e}")

# After
except (OSError, RuntimeError) as e:
    logger.error(f"Watchdog: failed to restart stdio server {key!r}: {e}")
```

**Required imports:** `httpx` and `asyncio` must already be imported. Verify they are present; add if missing.

## Validation plan

```bash
# Confirm no assert or except Exception remains
grep -n "except Exception\|assert " scripts/agent/repl_health.py

# Lint
uv run ruff check scripts/agent/repl_health.py

# Type check
uv run mypy scripts/agent/repl_health.py

# Tests
uv run pytest tests/test_repl_health.py -v
uv run pytest -v --tb=no -q
```
