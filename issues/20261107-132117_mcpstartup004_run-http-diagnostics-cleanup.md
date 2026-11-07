# run_http startup diagnostics mislabel SystemExit and verify the bound address only after listening

## Priority
Low

## Summary
Three small inaccuracies in `MCPServer.run_http()` make startup diagnostics less trustworthy: a `SystemExit` handler labels any exit from `server.run()` as a posture-gate failure, the loopback post-start check runs after the socket is already listening and silently skips when no server object exists, and a local `import logging` shadows the module-level import. Correct the label and state the intent of the post-start check precisely, without changing startup behavior.

## Background
Evidence from `scripts/mcp_servers/server.py` at reviewed head `59dbae624` (label: `Explicit in code`):

- The posture gate runs before the `try`, and the `run_http` docstring says a gate `SystemExit` propagates uncaught. The remaining `except SystemExit` clause wraps only `server.run()` and logs "Posture-gate failure during startup" before re-raising. A `SystemExit` raised from inside `server.run()` is not a posture-gate failure, so the log line would misattribute it.
- `_LoopbackVerifyingServer.startup()` calls `super().startup()` first and then inspects `srv.sockets`. By then uvicorn has created the listening sockets, so the check detects a wrong bind after the fact rather than preventing it. The earlier `http_host` allow-list check is what prevents it. The method also returns without checking anything when `self.should_exit` is set or `self.servers` is empty.
- `run_http` contains `import logging` and `import sys` inside the function although `logging` is already imported at module level.

Archived issue `issues/done/20261029-012525_ebrev003_serverbase-posture-gate-outside-try.md` moved the gate outside the `try`; the handler's message was not revisited.

## Problem
No functional defect was found: the loopback allow-list and the config-isolation check run before any socket is created, and a failed lifespan startup leads to `sys.exit(1)`. The issue is diagnostic accuracy: an operator reading "Posture-gate failure" for an unrelated exit, or reading the post-start check as a pre-bind guarantee, is misled. Confidence is High for the code facts and Low that any operator is currently affected.

## Reason for Change
Startup logs are the main evidence operators and the watchdog use when a server fails to come up. The change is cosmetic and low risk, and carries no urgency.

## Implementation Intent
Make the log message and the post-start check's docstring describe what the code actually does. Keep the pre-bind loopback allow-list as the authoritative guard and the post-start check as defense in depth. Do not alter the order of the loopback check, config isolation, posture gate, and socket creation.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (`MCPServer.run_http`, `_LoopbackVerifyingServer.startup`)
- `tests/mcp_servers/test_mcp_server_base.py`

## Required Changes
- Reword or remove the `except SystemExit` log line so it does not claim a posture-gate failure for exits that originate in `server.run()`.
- Update the `_LoopbackVerifyingServer` docstring to state that the check runs after sockets are created and is skipped when startup was aborted or no server exists.
- Remove the redundant function-local `import logging`.

## Constraints
- Keep re-raising the `SystemExit` unchanged.
- Keep `sys.exit(1)` when the server did not start.
- Do not change the loopback allow-list values.

## Acceptance Criteria
- A `SystemExit` raised from `server.run()` is re-raised with the same exit code and a log message that does not mention the posture gate.
- The docstring of the post-start verification matches its actual timing and skip conditions.
- `ruff check` reports no unused or redefined import in `server.py`.
- Existing tests in `tests/mcp_servers/test_mcp_server_base.py` pass.

## Testing Expectations
- Add or adjust one unit test asserting the log message and the re-raise for a `SystemExit` from `server.run()`.
- Run `uv run pytest tests/mcp_servers/test_mcp_server_base.py tests/mcp_servers/test_posture_gate_start_path.py`, `uv run ruff check scripts/mcp_servers`, and `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.

## Documentation Impact
Not expected. If MCP lifecycle documentation quotes the log line, update it to the new wording and run the `docs/` checkers from `routing.md`.

## Out of Scope
- Changing the order of startup checks.
- Any change to `_enforce_startup_posture_gate` behavior or to the double-execution problem tracked separately.
- Changing uvicorn configuration or log levels.

## Dependencies
- Same file as `issues/20261107-132004_mcpstartup001_python-m-double-execution.md` and `issues/20261107-132052_mcpstartup003_auth-guard-single-point.md`; no required order, but sequence the edits to avoid conflicts in `scripts/mcp_servers/server.py`.
- Related archived: `issues/done/20261029-012525_ebrev003_serverbase-posture-gate-outside-try.md`.

## Unresolved Questions
- `Needs confirmation`: whether any alerting or documentation matches on the exact "Posture-gate failure during startup" string before the wording changes.
- `Needs confirmation`: which uvicorn paths can raise `SystemExit` from `server.run()` in the pinned version; not checked in this review.

## AI Implementation Instruction
Limit the change to the message, docstring, and import cleanup in `run_http`. Do not reorder or remove any startup check and do not change exit codes. Report open questions instead of guessing the uvicorn behavior.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-132117
- **Related target files**: `scripts/mcp_servers/server.py`, `tests/mcp_servers/test_mcp_server_base.py`
