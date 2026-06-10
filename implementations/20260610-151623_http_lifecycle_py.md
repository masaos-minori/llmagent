# Implementation: http_lifecycle.py

## Goal

Replace the two `except Exception` handlers in `http_lifecycle.py` with specific exception types (`httpx.RequestError`, `httpx.HTTPStatusError`, `OSError`) so that unexpected errors propagate rather than being silently logged.

## Scope

- Target: `scripts/agent/http_lifecycle.py`
- Replace `except Exception as e:` in `start()` health-check poll loop (line ~141) with `except (httpx.RequestError, httpx.HTTPStatusError) as e:`
- Replace `except Exception as e:` in `shutdown_all()` (line ~168) with `except OSError as e:`
- Keep `StartupFailure` / `HttpStartupError` exception types unchanged

## Assumptions

1. Health-check failures during startup are always `httpx.RequestError` (connection refused, timeout) or `httpx.HTTPStatusError` (non-200 response from `resp.raise_for_status()`). Other errors would be bugs.
2. `shutdown_all()` termination failures are OS-level (`OSError`, `ProcessLookupError`) — `subprocess.Popen.terminate()` and `proc.wait()` only raise `OSError` subclasses.
3. `_terminate_with_timeout()` uses `asyncio.wait_for()` which raises `TimeoutError` (not `asyncio.TimeoutError`) — already caught in that method; no change needed.

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. In `start()`, health-check poll `except Exception as e:` → `except (httpx.RequestError, httpx.TimeoutException) as e:`. The health-check is expected to fail (connection refused) while the server is starting; only these error types are expected.
2. In `shutdown_all()`, `except Exception as e:` → `except OSError as e:`. Log as warning (side-effect on shutdown, non-fatal).
3. No change to `StartupFailure`, `HttpStartupError`, or `restart()`.

### Method

Targeted substitution of broad `except Exception` with the narrowest covering type. The health-check broad catch is the most important: if an unexpected exception occurs (e.g. `MemoryError`), it should not be swallowed.

### Details

```python
# start() health-check poll loop — BEFORE
except Exception as e:
    logger.debug(f"Lifecycle: health-check poll {server_key!r}: {e}")

# AFTER
except (httpx.RequestError, httpx.TimeoutException) as e:
    logger.debug(f"Lifecycle: health-check poll {server_key!r}: {e}")
```

```python
# shutdown_all() — BEFORE
except Exception as e:
    logger.warning(f"Lifecycle: error stopping HTTP subprocess {key!r}: {e}")

# AFTER
except OSError as e:
    logger.warning(f"Lifecycle: error stopping HTTP subprocess {key!r}: {e}")
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/http_lifecycle.py` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Tests | `uv run pytest tests/ -k "http_lifecycle"` | all pass |
