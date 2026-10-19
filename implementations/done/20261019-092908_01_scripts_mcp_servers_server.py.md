## Goal

Add an early-exit / unset-`self.servers` guard to `_LoopbackVerifyingServer.startup()` in
`scripts/mcp_servers/server.py` so that when uvicorn's lifespan startup fails (or requests
exit), the post-start loopback socket verification is skipped instead of raising
`AttributeError` from iterating the unset `self.servers`. Preserves the loopback-only bind
verification for the normal start path. (`REQ-001`)

## Scope

- **In-Scope**:
  - Add the guard to `_LoopbackVerifyingServer.startup()` immediately after
    `await super().startup(sockets=sockets)` and before the `for srv in self.servers:` loop.
- **Out-of-Scope**:
  - Changing `run_http()`, the `http_host` pre-bind check, or the loopback-only bind policy.
  - Restructuring the uvicorn wiring beyond the override guard.
  - Modifying `rag_pipeline_server.py` or any other MCP server.

## Assumptions

- The deployed uvicorn version keeps the 0.49.0 semantics observed here (early return on
  `should_exit`, `self.servers` unset on the failing path). The Phase 1 reproduction
  re-confirms this against the installed version before relying on it.
- The guard conditioned on `self.should_exit` / unset `self.servers` is acceptable; the
  equivalent `if not self.started: return` signal is also valid since `self.started` is set
  True only on the normal path.
- `tests` is importable as a package so the regression tests resolve.

## Design decisions

- Place the guard immediately after `await super().startup(sockets=sockets)` and before the
  `for srv in self.servers:` loop, so it skips verification only when the server did not
  reach the serving state.
- Condition on `self.should_exit` OR unset `self.servers` (via
  `getattr(self, "servers", None)`); both are false on the normal path, so loopback
  verification is preserved there.

## Alternatives considered

- `if not self.started: return` — an equivalent signal (`self.started` becomes True only on
  the normal path). Acceptable, but the plan's `should_exit` / unset-`servers` form matches
  the observed failure mode more directly.
- Wrapping the loop in `try/except AttributeError` — rejected: it masks the real cause
  (a failed lifespan) behind a generic attribute error and is less explicit than an early
  guard.
- Initializing `self.servers` in `run_http()` before `server.run()` — rejected: out of
  scope; `self.servers` is uvicorn-owned and legitimately unset on the early-return path.

## Implementation

### Target file

`scripts/mcp_servers/server.py`

### Procedure

1. Read `scripts/mcp_servers/server.py` lines 256-284 to locate `_LoopbackVerifyingServer`
   and its `startup()` override (lines 261-270) and the `run_http()` call site (lines
   278-284).
2. Confirm the current state: line 262 `await super().startup(sockets=sockets)`, line 263
   `for srv in self.servers:` — `self.servers` is accessed unconditionally.
3. Insert the guard between the `await super().startup(sockets=sockets)` line and the
   `for srv in self.servers:` line, preserving the 16-space method-body indentation:
   ```python
                   await super().startup(sockets=sockets)
                   if self.should_exit or not getattr(self, "servers", None):
                       return
                   for srv in self.servers:
   ```
4. Leave the loopback verification loop (lines 263-270) intact for the normal start path.
5. Do not modify `run_http()`, the `http_host` pre-bind check (lines 238-242), or any other
   server.
6. Run the Phase 4 validation sequence.

### Method

- Insert exactly two guard lines after the `await super().startup(sockets=sockets)` line and
  before the `for srv in self.servers:` line. Do not reflow or delete the surrounding loop.
- Indentation: `_LoopbackVerifyingServer` is a local class inside `run_http()`; its method
  body is indented 16 spaces, so the `if` sits at 16 spaces and its `return` at 20 spaces.
- Use `getattr(self, "servers", None)` so the guard is safe even though
  `uvicorn.Server.__init__` never assigns `self.servers` and the early-return path leaves
  it unset.

### Details

- `REQ-001`: the guard skips socket verification when `self.should_exit` is True or
  `self.servers` is unset, and still verifies loopback binding on the normal start path
  (AC-001, AC-002).
- Evidence (verified against current source): uvicorn 0.49.0 `Server.startup()` runs
  `await self.lifespan.startup()` first; when `LifespanOn.startup()` reports failure it logs
  `ERROR: Application startup failed. Exiting.` and sets `self.should_exit = True`, after
  which `Server.startup()` returns before assigning `self.servers`. `Server.__init__`
  initializes only `started` and `should_exit`, never `servers`. `run_http()` catches only
  `KeyboardInterrupt` (line 281) then calls `sys.exit(1)` when `not server.started`
  (line 283-284), so the failing process exits cleanly once the guard prevents the
  `AttributeError`.
- `UNK-01`: uvicorn's own diagnostic is sufficient; no extra one-line log in `run_http()` is
  required. Record as a possible future enhancement, not a requirement.

## Compatibility considerations

- Defensive guard with no user-facing behavior change. The normal (successful) start path is
  unchanged: `self.should_exit` is False and `self.servers` is assigned, so the guard does
  not trigger and post-start verification runs as before.

## Security considerations

- The loopback-only bind policy is unchanged; the guard does not weaken post-start bind
  verification on the normal path. Fail-closed behavior elsewhere is untouched.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/server.py` | Static: format, lint, type, security, import boundaries | `uv run ruff format scripts/`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit scripts/mcp_servers/server.py`, `PYTHONPATH=scripts uv run lint-imports` | All clean; no new findings |
| `scripts/mcp_servers/server.py` | Behavioral: failing-lifespan override no longer raises `AttributeError` | throwaway reproduction (Phase 1) then guarded run | No `AttributeError`; clean uvicorn diagnostic |
| `tests/mcp_servers/test_mcp_server_base.py` | Unit: failing-lifespan + normal-loopback + non-loopback-bind | `uv run pytest tests/mcp_servers/test_mcp_server_base.py` | New tests pass; existing tests unchanged |
| Whole suite | Regression | `uv run pytest` | No new failures |

## Completion criteria

- `AC-001`: a server whose lifespan startup raises reaches the
  `if not server.started: sys.exit(1)` path without raising `AttributeError` (asserted by
  the REQ-002 failing-lifespan test).
- `AC-002`: the normal loopback start path still verifies the bound socket is loopback, and
  a stubbed non-loopback bind raises `RuntimeError` (asserted by the REQ-003 normal-path
  test).

## Out of scope

Changing which servers define a lifespan, the loopback-only bind policy, the pre-bind
`http_host` check in `run_http()`, restructuring `run_http()` or the uvicorn wiring beyond
the override guard, or modifying `rag_pipeline_server.py` or any other server.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261019-193849 | Guard inserted at server.py lines 262-264: `if self.should_exit or not getattr(self, "servers", None): return` before the `for srv in self.servers:` loop. Skips verification on the failing path; normal-path loopback verification preserved. |
| 2 | Add or update tests per Validation plan | Completed | — | 20261019-193849 | Regression tests added in sibling procedure 092908_02 (TestStartupOverride: failing-lifespan REQ-002, normal-loopback REQ-003, non-loopback-bind REQ-003). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261019-193849 | ruff format/check clean; mypy success; bandit no issues; lint-imports 6/6 kept. TestStartupOverride 3/3 pass; full mcp_servers suite 2388 pass. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261019-193849 | No doc changes in scope. |

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
- **Source issue**: issues/20261018-191418_mcp001_mcp-server-startup-lifespan-failure-raises-attributeerror-masking-uvicorn-diagnostic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-232138_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-092908
- **Related target files**: scripts/mcp_servers/server.py
