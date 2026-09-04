## Goal
Add bind-address validation to the `MCPServer` base class, rejecting any
`http_host` that is not `127.0.0.1`/`::1`, and add post-start verification of
the actual bound socket address.

## Scope
- **In-Scope**: `MCPServer.http_host` class attribute (verified 2026-09-04,
  line 147) and `run_http()` (lines 207-221), where `http_host` is consumed
  by `uvicorn.run(host=self.http_host, ...)` (line 218).
- **Out-of-Scope**: `MCPServer.http_port`, `app_module`, `own_config_file`,
  `mcp_tools`, `dispatch()`, `list_tools()`, `health()`, and every other
  method in this file (`build_tools_response()` and beyond, lines 224+) —
  confirmed by direct read to be unrelated to bind-address concerns.

## Assumptions
- `MCPServer` has no `__init__` method of its own today (confirmed by direct
  read of the full class body, lines 136-221) — the Plan's Implementation
  intent phrase "`MCPServer.__init__`/startup path" leaves the exact
  insertion point to this document's own design decision (below), since no
  existing `__init__` exists to extend.
- Coupled to row 1 (`scripts/eventbus/config.py`) only in the sense that both
  rows implement equivalent address-class validation independently — per the
  Plan's Design section, no shared helper module is required; this row's
  validation logic must not diverge from row 1's accepted-address set
  (`127.0.0.1`, `::1`).
- The only subclass overriding `http_host` (`scripts/mcp_servers/mdq/mdq_server.py:411`,
  confirmed by direct read 2026-09-04) sets it to the same safe value
  (`"127.0.0.1"`), so this validation is not expected to break any existing
  subclass.

## Design decisions
- Add validation inside `run_http()` (the sole call site that consumes
  `http_host`, line 218), immediately before the `uvicorn.run(...)` call,
  rather than adding a new `__init__` method — `MCPServer` is instantiated
  once per process and `run_http()` is the only startup entry point that
  actually uses `http_host`; a validation check placed there covers every
  subclass without introducing an `__init__` override burden on subclasses
  that may already define their own.
- Mirror row 1's accepted-address logic exactly (`http_host not in
  ("127.0.0.1", "::1")` → reject) rather than importing
  `scripts/eventbus/config.py`'s `_is_public_host()` — per the Plan's Design
  section, Event Bus and MCP servers are independently-validated call sites
  by explicit architecture decision; importing across these modules would
  introduce a cross-package dependency neither currently has.
- Add post-start socket verification (REQ-004) via `socket.getsockname()` on
  uvicorn's bound server, or — if uvicorn's API does not expose this
  cleanly for a blocking `uvicorn.run()` call — as a same-process check
  performed by the health-check path (`health()`, lines 174-205) confirming
  the configured `http_host` matches the validated address set; determine
  the exact mechanism at execution time based on uvicorn's version-specific
  API (re-check `uvicorn.run()`'s signature/return value, since it is a
  blocking call with no direct handle to the bound socket in typical usage).

## Alternatives considered
- Validating in a class-level `__init_subclass__` hook: rejected — would run
  at class-definition time (import time), before any config override could
  plausibly change `http_host` at runtime; `run_http()`'s call-time check is
  the correct point since it reflects the actual value used to bind.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Add a private validation helper (e.g. `_validate_loopback_host(host:
   str) -> None`, raising `ValueError` if `host not in ("127.0.0.1",
   "::1")`) near the top of this file or as a `MCPServer` static/class
   method.
2. Call this helper at the start of `run_http()` (verified 2026-09-04, line
   207) with `self.http_host`, before the `uvicorn.run(...)` call (line
   216-221).
3. Add post-start bound-socket verification per Design decisions — re-read
   `uvicorn`'s installed version's `Server`/`run()` API at execution time
   (`python -c "import uvicorn; print(uvicorn.__version__)"`) to determine
   the concrete mechanism (e.g. constructing `uvicorn.Config`/`uvicorn.Server`
   directly instead of the `uvicorn.run()` convenience wrapper, if a bound-
   socket handle is needed before serving begins).

### Method
Direct `Edit` for steps 1-2; step 3 may require restructuring `run_http()`'s
body from the `uvicorn.run()` convenience call to explicit
`uvicorn.Config`/`uvicorn.Server` construction — re-confirm the exact
uvicorn API surface at execution time before deciding the restructure's
extent.

### Details
Current (verified 2026-09-04, lines 207-221):
```python
def run_http(self) -> None:
    """Launch the HTTP server via uvicorn."""
    import uvicorn

    if self.own_config_file:
        from shared.config_loader import ConfigLoader

        ConfigLoader.restrict_to(self.own_config_file)

    uvicorn.run(
        self.app_module,
        host=self.http_host,
        port=self.http_port,
        log_level="info",
    )
```
After (illustrative; exact post-start verification mechanism to be finalized
against the installed uvicorn version at execution time):
```python
def run_http(self) -> None:
    """Launch the HTTP server via uvicorn."""
    import uvicorn

    if self.http_host not in ("127.0.0.1", "::1"):
        raise ValueError(
            f"{type(self).__name__} bound to non-loopback address "
            f"{self.http_host}. Internal MCP servers must bind to loopback only."
        )

    if self.own_config_file:
        from shared.config_loader import ConfigLoader

        ConfigLoader.restrict_to(self.own_config_file)

    uvicorn.run(
        self.app_module,
        host=self.http_host,
        port=self.http_port,
        log_level="info",
    )
```

## Compatibility considerations
Coupled to row 5 (`tests/mcp_servers/test_mcp_server_base.py`) — that file's
`_SimpleServer`/`_EmptyServer` test fixtures (lines 19-44, both already
using `http_host = "127.0.0.1"`) are unaffected; new tests must exercise a
fixture subclass with a non-loopback `http_host` to confirm rejection.
Affects every MCP server subclass simultaneously (base-class change) — per
the Plan's Risks section, all 9 MCP server `url` entries in
`config/agent.toml` already resolve to `127.0.0.1` and the sole subclass
override (`mdq_server.py`) already uses a safe value, so no subclass is
expected to fail this new check in the current deployed configuration.

## Security considerations
Closes the confirmed gap where `MCPServer`'s base class enforced no
bind-address validation at all, per the source Issue's constraint against
relying solely on "the default configuration is safe today."

## Rollback considerations
Localized method-body edit under version control; revert via `git revert`
if needed, together with row 5's test updates.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/server.py` | Unit | `uv run pytest tests/mcp_servers/test_mcp_server_base.py -v` | Non-loopback `http_host` rejected at `run_http()`; `127.0.0.1`/`::1` accepted; post-start verification confirms the actual bound address |

## Completion criteria
`run_http()` rejects any `http_host` not in `("127.0.0.1", "::1")`; a
post-start check confirms the live-bound socket address.

## Out of scope
`http_port`, `app_module`, `own_config_file`, `mcp_tools`, `dispatch()`,
`list_tools()`, `health()`, and `build_tools_response()`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Re-confirm uvicorn API surface for post-start verification at execution time |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by row 5 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Plan's Documentation Impact: Yes — EventBus/MCP domain mapping docs, sequenced after this Plan lands |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20260902-143334_loopbackonly_enforce_loopback_only_http_remove_external_publication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091921_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-092757
- **Related target files**: scripts/mcp_servers/server.py
