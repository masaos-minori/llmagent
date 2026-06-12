# Implementation: agent/http_lifecycle.py — Narrow except Exception

## Goal

Narrow 2 `except Exception` clauses in `scripts/agent/http_lifecycle.py` to specific exception types covering the actual failure modes of health-check polling and subprocess shutdown.

## Scope

**In:** `scripts/agent/http_lifecycle.py`
**Out:** No other files change.

## Assumptions

1. The health-check poll (line ~141) sends an HTTP GET to the MCP server's `/health` endpoint inside a loop. Failures are `httpx.HTTPError` (connection refused, timeout) or `OSError`. These are logged at DEBUG level and the loop continues.
2. `shutdown_all()` (line ~169) terminates subprocesses. `_terminate_with_timeout()` can raise `OSError` (process already dead, permission) or `asyncio.TimeoutError` (termination timed out). Failures are logged at WARNING level.
3. Both catch sites currently just log the error; the graceful-degradation behaviour is preserved after narrowing.

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. Health-check poll (line ~141):
```python
# Before
except Exception as e:
    logger.debug(f"Lifecycle: health-check poll {server_key!r}: {e}")

# After
except (httpx.HTTPError, OSError) as e:
    logger.debug(f"Lifecycle: health-check poll {server_key!r}: {e}")
```

2. `shutdown_all()` (line ~169):
```python
# Before
except Exception as e:
    logger.warning(f"Lifecycle: error stopping HTTP subprocess {key!r}: {e}")

# After
except (OSError, asyncio.TimeoutError) as e:
    logger.warning(f"Lifecycle: error stopping HTTP subprocess {key!r}: {e}")
```

### Method

Two targeted in-place edits.

### Details

**Verify imports:** Confirm `import httpx` and `import asyncio` are present. `httpx` is used elsewhere for HTTP calls; `asyncio` is used for `asyncio.sleep`. Both should already be imported.

## Validation plan

```bash
# Confirm no except Exception remains
grep -n "except Exception" scripts/agent/http_lifecycle.py

# Lint
uv run ruff check scripts/agent/http_lifecycle.py

# Type check
uv run mypy scripts/agent/http_lifecycle.py

# Tests
uv run pytest -v --tb=no -q
```
