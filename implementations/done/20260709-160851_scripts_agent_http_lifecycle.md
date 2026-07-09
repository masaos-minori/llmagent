# Implementation: Phase 1 — Production-code hardening (scripts/agent/http_lifecycle.py)

## Goal

Eliminate PID-reuse race in `_terminate_with_timeout` by removing the `proc.pid` fallback in `os.killpg` target resolution, and prevent `start()` from storing a PID-as-PGID when `os.getpgid()` fails.

## Scope

- `scripts/agent/http_lifecycle.py` only.
- Two changes: `_terminate_with_timeout` L96-112 and `start()` L217-219.

## Assumptions

1. `_terminate_with_timeout` is always called with a `server_key` whose pgid has been stored in `self._http_pgids`. Verified by `start()` (L217) and `restart()` (pgid popped after terminate call). The fallback path `self._http_pgids.get(server_key, proc.pid)` is dead code under normal conditions.
2. When `os.getpgid(proc.pid)` fails in `start()`, the subprocess has already exited. Using `proc.terminate()` (instead of `os.killpg(proc.pid, ...)`) in `_terminate_with_timeout` is the correct safe fallback.

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. Change `_terminate_with_timeout` L96-112 to not fall back to `proc.pid`.
2. Change `start()` L217-219 to not store `proc.pid` when `os.getpgid` fails.

### Method

Both changes are small in-place edits. No new functions or classes.

### Details

#### Change 1a: `_terminate_with_timeout` — SIGTERM block (current L96-100)

Before:

```python
        pgid = self._http_pgids.get(server_key, proc.pid)
        try:
            os.killpg(pgid, signal.SIGTERM)  # nosec B603
        except (ProcessLookupError, OSError):
            proc.terminate()
```

After:

```python
        pgid = self._http_pgids.get(server_key)
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGTERM)  # nosec B603
            except (ProcessLookupError, OSError):
                proc.terminate()
        else:
            proc.terminate()
```

#### Change 1b: `_terminate_with_timeout` — SIGKILL block (current L108-112)

Before:

```python
            pgid = self._http_pgids.get(server_key, proc.pid)
            try:
                os.killpg(pgid, signal.SIGKILL)  # nosec B603
            except (ProcessLookupError, OSError):
                proc.kill()
```

After:

```python
            pgid = self._http_pgids.get(server_key)
            if pgid is not None:
                try:
                    os.killpg(pgid, signal.SIGKILL)  # nosec B603
                except (ProcessLookupError, OSError):
                    proc.kill()
            else:
                proc.kill()
```

#### Change 2: `start()` — pgid storage fallback (current L217-219)

Before:

```python
        try:
            self._http_pgids[server_key] = os.getpgid(proc.pid)
        except OSError:
            self._http_pgids[server_key] = proc.pid
```

After:

```python
        try:
            self._http_pgids[server_key] = os.getpgid(proc.pid)
        except OSError:
            pass
```

When `os.getpgid` fails, the pgid is left unset. `_terminate_with_timeout` will then fall back to `proc.terminate()` instead of `os.killpg(proc.pid, ...)`.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Phase 1 regression | `uv run pytest tests/test_lifecycle.py -k TestProcessGroupShutdown -v` | all pass |
| Lifecycle full suite | `uv run pytest tests/test_lifecycle.py -v` | all pass |
| Lint | `uv run ruff check scripts/agent/http_lifecycle.py` | 0 errors |
| Safety: killpg only called when pgid is known | Manual review of L96-112 | `os.killpg` never receives a bare `proc.pid` |
