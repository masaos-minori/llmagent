# Event Bus post-start verification raises AttributeError and hides the real startup failure

## Priority
Low

## Summary
Make the Event Bus's post-start loopback verification skip itself when uvicorn's startup was aborted (for example because the application lifespan failed), the way the MCP server base class already does. Today it raises an unrelated `AttributeError` after the real error, which makes a failed start look like a bug in the verification code.

## Background
- Found on 2026-10-20 while investigating a CI failure: `tests/eventbus/test_eventbus_startup.py::test_main_post_start_verification_binds_loopback` failed on the runner. The subprocess printed the real cause first (`FileNotFoundError: /opt/llm/schemas/event_envelope.json`, then `Application startup failed. Exiting.`) and then a second traceback ending in `AttributeError: '_LoopbackVerifyingServer' object has no attribute 'servers'`.
- The real cause of that CI failure was a test environment issue and is already fixed (the test now forwards `EVENTBUS_SCHEMA_PATH`). This issue covers only the secondary error.
- `scripts/mcp_servers/server.py` defines the same `_LoopbackVerifyingServer` and already guards against this case: after `super().startup()` it returns when `self.should_exit` is set or `servers` is absent. The Event Bus copy in `scripts/eventbus/app.py` (`_main`) does not have the guard.

## Problem
- In the installed uvicorn (0.49.0), `Server.startup()` awaits `self.lifespan.startup()`; if the lifespan reports failure it sets `self.should_exit = True` and returns before creating the listening sockets. `Server.__init__` does not define `servers`, so the attribute does not exist at that point.
- The Event Bus override then iterates `self.servers` unconditionally and raises `AttributeError`.
- Effect (Confirmed by CI log of run 39350474293): the process still exits non-zero and the real error is still logged before it, so the failure is not silent. But the log ends with a misleading traceback pointing at the verification code, which costs time during diagnosis.

## Reason for Change
- Operational clarity: the last error in a failed start should be the cause, not a defect in a defense-in-depth check.
- Consistency: two copies of the same override exist; only one handles a failed startup.
- Low risk: the fix mirrors code that already exists and is tested for the MCP servers.

## Implementation Intent
- Apply the same early-return condition the MCP server base class uses, so verification runs only when startup completed and sockets exist.
- Keep the verification semantics unchanged for a successful start: a non-loopback bound socket must still raise `RuntimeError`.
- Do not merge the two copies into one shared class in this issue; that is a separate refactoring decision.

## Target Files or Areas
- `scripts/eventbus/app.py` (`_main` and its `_LoopbackVerifyingServer.startup`)
- `tests/eventbus/test_eventbus_startup.py`
- Reference only: `scripts/mcp_servers/server.py` and `tests/mcp_servers/test_mcp_server_base.py` (`TestStartupOverride`)

## Required Changes
- Add the early return after `super().startup()` when `self.should_exit` is set or `servers` is missing or empty.
- Add a regression test that drives the Event Bus override with a lifespan that fails and asserts no `AttributeError` is raised and the server does not report started.
- Keep the existing loopback-violation test (non-loopback bound socket raises `RuntimeError`) passing.

## Constraints
- Must not weaken the loopback verification for a successful start.
- Must not change `eventbus.app` startup order, logging of the real lifespan error, or the exit code on failed start.

## Acceptance Criteria
- With a failing lifespan, the override returns without raising `AttributeError`, and `_main` still exits non-zero.
- With a successful start and a non-loopback bound socket, the override still raises `RuntimeError`.
- With a successful start and a loopback bound socket, the override logs the post-start verification message as before.
- The new test fails against the current code and passes after the change.

## Testing Expectations
- Unit test in `tests/eventbus/test_eventbus_startup.py` for the failed-lifespan case, modelled on `TestStartupOverride` in `tests/mcp_servers/test_mcp_server_base.py`.
- `uv run pytest tests/eventbus/test_eventbus_startup.py` and `tests/mcp_servers/test_mcp_server_base.py`.
- Follow `rules/toolchain.md` for ruff, mypy, and the module size gate (`tools/check_module_size.py`): `scripts/eventbus/app.py` must not grow past its baseline entry, if it has one.

## Documentation Impact
- Not required: no documented behavior changes. If `docs/24_eventbus` describes the post-start verification, confirm it does not claim a behavior on failed startup.

## Out of Scope
- Unifying the two `_LoopbackVerifyingServer` classes.
- The Event Bus auth token and deployment script problems tracked in the sibling issues below.
- Changing uvicorn or its version.

## Dependencies
- Siblings under `issues/` touching the same service: `20261019-210937_ebsec001_eventbus_auth_token_startup_block.md` and `20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md`. Neither covers this problem: they concern configuration loading and the deployment script, which fail before `_main` creates the server. No fix order is required.

## Unresolved Questions
- N/A: none. (Assumption: behavior is the same in the uvicorn version pinned by `uv.lock`; the installed version, 0.49.0, was inspected.)

## AI Implementation Instruction
- Make the smallest change in `scripts/eventbus/app.py`; do not refactor `_main` or touch the MCP server base class.
- Write the failing test first and show it failing before the change.
- Do not edit the sibling issues or unrelated tests. Stop and report if the installed uvicorn no longer sets `should_exit` on lifespan failure.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-115806
- **Related target files**: scripts/eventbus/app.py, tests/eventbus/test_eventbus_startup.py
