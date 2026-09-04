## Goal
Add post-start socket verification to Event Bus's `_main()` entry point,
confirming the actual bound socket address is loopback after startup
completes.

## Scope
- **In-Scope**: `_main()` (verified 2026-09-04, lines 194-206), specifically
  the `uvicorn.run(...)` call (lines 200-206) that currently only logs the
  configured `cfg.host`/`cfg.port` (line 199) before starting, with no
  post-bind confirmation.
- **Out-of-Scope**: the rest of `scripts/eventbus/app.py` (route handlers,
  `lifespan()`, `ack`/`nack` endpoints, lines 1-192) — confirmed by direct
  read to be unrelated to startup binding.

## Assumptions
- Coupled to row 1 (`scripts/eventbus/config.py`) — `cfg.host` is already
  validated by `EventBusConfig.__post_init__` (row 1's unconditional
  `_is_public_host()` check) before `_main()` ever calls `uvicorn.run()`;
  this row's post-start verification is a defense-in-depth confirmation that
  the actual OS-level bind matches the validated config value, not a
  substitute for row 1's config-time validation.
- `uvicorn.run()` is a blocking convenience wrapper with no direct return
  value or handle to the bound socket while it is running — the same API
  constraint noted in row 2's document for `scripts/mcp_servers/server.py`.
  Confirm at execution time whether this project's installed uvicorn version
  supports a lifespan/startup hook that can inspect the bound socket, or
  whether `_main()` must be restructured to use `uvicorn.Config`/
  `uvicorn.Server` directly to obtain a socket handle before `serve()` is
  awaited.

## Design decisions
- Prefer adding the post-start check inside the existing FastAPI `lifespan()`
  context manager (referenced but not fully read in this document's
  investigation — re-read its full body at execution time via `sed -n
  '1,60p' scripts/eventbus/app.py`) if it has access to the running
  server's socket via `app.state` or a similar mechanism uvicorn exposes to
  lifespan handlers; this avoids restructuring `_main()`'s straightforward
  `uvicorn.run()` call into a lower-level `Config`/`Server` construction
  unless the lifespan approach proves infeasible.
- If the lifespan approach cannot obtain a genuine bound-socket handle,
  fall back to restructuring `_main()` to construct `uvicorn.Config`/
  `uvicorn.Server` explicitly, call `server.startup()` to bind the socket
  first, verify via `server.servers[0].sockets[0].getsockname()` (uvicorn's
  documented low-level API for this), then continue with
  `server.main_loop()`/`server.serve()` for the remainder.

## Alternatives considered
- Skipping in-process verification and instead relying on an external
  post-deploy smoke test (e.g. a separate script that connects to the port
  after startup): rejected — REQ-004 and AC-6 specifically call for
  verification "after startup completes" as part of the running process's
  own startup sequence, not a separate operational script; an external
  script would also not be exercised by this Plan's unit/integration test
  suite (REQ-005's Validation plan row for this file).

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. Re-read `scripts/eventbus/app.py`'s full `lifespan()` definition (not yet
   fully inspected in this document's investigation) to determine whether it
   has a `server`/`app.state` reference to the running uvicorn `Server`
   instance.
2. Add a post-start check that calls `socket.getsockname()` (or uvicorn's
   equivalent `server.servers[*].sockets[*].getsockname()`) on the actual
   bound socket, comparing its host component against `cfg.host` and
   confirming it is `"127.0.0.1"` or `"::1"`.
3. On mismatch or a non-loopback bound address, log an error (this is a
   post-bind confirmation of an already-validated config value, so a
   mismatch here indicates an environment-level anomaly, not a config
   error — REQ-004 does not specify whether this should raise or only log;
   default to raising `RuntimeError` for consistency with this Plan's
   other unconditional-FATAL patterns, per `localremoval`'s REQ-005/REQ-008
   precedent of unconditional severity, unless the implementer determines
   at execution time that a raise here would be unrecoverable in a way a
   log would not be).
4. Update the startup log statement (line 199) to include the verified
   bound address once available, if the mechanism naturally produces it.

### Method
Direct `Edit`, informed by a full read of `lifespan()` (not yet performed —
see Procedure step 1) and the installed uvicorn version's API
(`python -c "import uvicorn; print(uvicorn.__version__)"`) at execution
time.

### Details
Current (verified 2026-09-04, lines 194-206):
```python
def _main() -> None:
    """Start the Event Bus with config-based host binding."""
    import uvicorn  # noqa: PLC0415

    cfg = load_config(get_config_path())
    logger.info("eventbus starting on port=%d host=%s", cfg.port, cfg.host)
    uvicorn.run(
        "eventbus.app:app",
        host=cfg.host,
        port=cfg.port,
        log_level="info",
        access_log=True,
    )
```
Exact post-start verification code is deferred to execution time pending the
uvicorn-API investigation in Procedure steps 1-2 — this document intentionally
does not prescribe a specific low-level restructure without first confirming
`lifespan()`'s existing capabilities, per `rules/workflow-lifecycle.md`'s
adversarial-verification discipline (avoid asserting an implementation detail
not yet confirmed against the actual codebase).

## Compatibility considerations
Coupled to row 1 — this row's verification is meaningful only once row 1's
config-time validation lands (otherwise a non-loopback `cfg.host` would
already have raised before `_main()` reaches `uvicorn.run()`).

## Security considerations
Provides defense-in-depth confirmation that the OS-level bind matches the
validated configuration, catching an environment-level discrepancy (e.g. a
container network namespace remapping) that config-time validation alone
cannot observe.

## Rollback considerations
Localized change to `_main()`'s startup sequence, under version control;
revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/app.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_startup.py -v` (post-start socket check) | Actual bound socket confirmed loopback after startup |

## Completion criteria
Event Bus startup verifies the actual bound socket address is loopback after
`uvicorn`'s server binds, independent of the pre-bind config validation in
row 1.

## Out of scope
Route handlers (`ack`/`nack`), `lifespan()`'s non-socket-related setup, and
the rest of this file's request-handling logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Confirmed `lifespan()` has no access to the raw uvicorn socket (FastAPI ASGI lifespan doesn't expose it) — fell back to the Design decisions' documented alternative: restructured `_main()` to use `uvicorn.Config`/`uvicorn.Server` directly with the same locally-subclassed `_LoopbackVerifyingServer` pattern as row 2, for consistency across the codebase |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | Covered by row 4 — added a new real-subprocess integration test (`test_main_post_start_verification_binds_loopback`) beyond row 4's originally-scoped unit tests, since this row's own restructure of `_main()` needed its own dedicated coverage |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff/mypy clean; `tests/eventbus/test_eventbus_startup.py` 16 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260904 | 20260904 | Covered by row 1's shared update to `docs/06_eventbus_05_configuration-and-operations.md` (Bind Address section now documents the post-start verification this row adds) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260902-143334_loopbackonly_enforce_loopback_only_http_remove_external_publication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091921_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-092757
- **Related target files**: scripts/eventbus/app.py
