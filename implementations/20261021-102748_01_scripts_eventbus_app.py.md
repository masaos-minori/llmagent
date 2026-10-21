## Goal

Add an early-return guard to the Event Bus `_LoopbackVerifyingServer.startup` override so a failed uvicorn lifespan returns cleanly instead of raising a secondary `AttributeError`, mirroring the already-tested MCP server base class. (REQ-001, AC-1)

## Scope

- Modify only `scripts/eventbus/app.py`, inside the `_LoopbackVerifyingServer` local class within `_main()`.
- No change to the MCP base class, no unification of the two copies, no uvicorn version change.

## Assumptions

- The pinned uvicorn sets `self.should_exit = True` on lifespan failure and does not define `self.servers` until a successful `create_sockets()` — confirmed by the reproduced `AttributeError` against current code.

## Design decisions

- Insert the guard immediately after `await super().startup(sockets=sockets)` and before the `for srv in self.servers:` loop, using the exact condition from the MCP base class.
- Keep both conditions (`self.should_exit` and `not getattr(self, "servers", None)`) to match the proven reference verbatim; the `getattr` guard covers the missing-attribute case defensively.

## Alternatives considered

- N/A: the guard mirrors the single proven pattern in the MCP base class; no alternative condition is warranted.

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

1. In `_main()`, locate `_LoopbackVerifyingServer.startup` (current lines 311-321).
2. After the line `await super().startup(sockets=sockets)` (line 312), insert:
   ```python
   if self.should_exit or not getattr(self, "servers", None):
       return
   ```
3. Leave the existing `for srv in self.servers:` loop and its loopback `RuntimeError` unchanged.

### Method

Edit the existing method in place — no new symbols, imports, or functions.

### Details

- Current code (verified at lines 311-321):
  ```python
  async def startup(self, sockets: list[Any] | None = None) -> None:
      await super().startup(sockets=sockets)
      for srv in self.servers:
          for sock in srv.sockets or []:
              ...
  ```
  A failed lifespan leaves `self.servers` undefined, so the unconditional loop raises `AttributeError`.
- Reference pattern (verified in `scripts/mcp_servers/server.py` lines 261-264):
  ```python
  async def startup(self, sockets: list[Any] | None = None) -> None:
      await super().startup(sockets=sockets)
      if self.should_exit or not getattr(self, "servers", None):
          return
      for srv in self.servers:
          for sock in srv.sockets or []:
              ...
  ```
- The guard returns before the loop only when startup failed; loopback verification semantics for a successful start are unchanged (a non-loopback socket still raises `RuntimeError`; a loopback socket still logs the post-start message).
- Empirically confirmed: running `eventbus.app` with a missing schema path reproduces the `AttributeError` against current code and logs `Application startup failed. Exiting.` first (non-zero exit).

## Compatibility considerations

N/A: the change only short-circuits an already-failed startup path; the exit contract (`_main` still exits non-zero via uvicorn) is unchanged.

## Security considerations

N/A: no auth, config, or network-scope change; the loopback verification still runs on every successful start.

## Rollback considerations

N/A: revert the commit (a single guarded line).

## Validation plan

- Lint/type/size: `uv run ruff format scripts/` + `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run python tools/check_module_size.py` for `scripts/eventbus/app.py` (no baseline entry exists yet — must stay under the 16384 B gate).
- Existing tests: `uv run pytest tests/eventbus/test_eventbus_startup.py` — the loopback-violation (AC-2) and loopback-success (AC-3) tests must still pass; no `AttributeError`.

## Completion criteria

- The guard line is present after `await super().startup(sockets=sockets)` and before the `for srv in self.servers:` loop.
- `ruff`, `mypy`, and the module-size gate pass for `scripts/eventbus/app.py`.
- The existing loopback tests in `tests/eventbus/test_eventbus_startup.py` still pass with no `AttributeError`.

## Out of Scope

- The regression test for the failing-lifespan case (`tests/eventbus/test_eventbus_startup.py`) — separate document.
- Unifying the two `_LoopbackVerifyingServer` copies; touching the MCP base class; changing the uvicorn version.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the early-return guard to `_LoopbackVerifyingServer.startup` after `await super().startup(sockets=sockets)` | Pending | — | — | REQ-001, AC-1 |
| 3 | Run ruff/mypy/module-size gate and confirm existing eventbus startup tests still pass | Pending | — | — | REQ-001..004, AC-2, AC-3 |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261020-115744_ebstart003_event-bus-post-start-verification-raises-attributeerror-when-lifespan-startup-fails.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-232535_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-102748
- **Related target files**: `scripts/eventbus/app.py`
