# MCP server module executes twice under python -m because the startup posture gate re-imports it

## Priority
Medium

## Summary
When an MCP server is started as `python -m mcp_servers.<pkg>.<server>`, the server module runs twice: once as `__main__` and once as the imported module that `MCPServer.run_http()` resolves for the posture gate and that uvicorn serves. Make the start path execute the server module exactly once, and make the regression test exercise the real `run_http()` path.

## Background
Archived issue `issues/done/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md` required that `python -m <server module>` executes the module once, and `tests/mcp_servers/test_config_isolation_import.py` gained `test_a_server_module_executes_once_under_python_m`. Archived issue `issues/done/20261029-012525_ebrev003_serverbase-posture-gate-outside-try.md` and the `_enforce_startup_posture_gate()` method in `MCPServer` came after that work (evidence label: `Explicit in code`).

Evidence from this review (reviewed head `59dbae624`, working tree clean):

- `MCPServer._enforce_startup_posture_gate()` in `scripts/mcp_servers/server.py` calls `importlib.import_module(<app_module module name>)`. Under `python -m`, the running module is registered as `__main__`, not as `mcp_servers.git.git_server`, so this import executes the whole module a second time. A minimal two-file experiment confirmed the Python behavior (`exec as __main__` followed by `exec as pkg.m`).
- A probe ran `runpy.run_module("mcp_servers.git.git_server", run_name="__main__")` with the real `run_http()` and only `uvicorn.Server.run` stubbed, recording `ConfigLoader.load` calls and whether `ConfigLoader._allowed_files` was already set. Result: `git_mcp_server.toml` was loaded twice, the first time with no restriction active and the second after `restrict_to` (evidence label: `Operationally observed`, confidence High). The posture gate then exited with status 1 in the probe environment, so the second copy's posture was the one that decided the outcome.
- `test_a_server_module_executes_once_under_python_m` replaces `MCPServer.run_http` with a no-op, so it never reaches `_enforce_startup_posture_gate()` and cannot see the second import (evidence label: `Explicit in code`).
- Production binaries use the launcher path, which applies `restrict_to` before import (`deploy/build_binaries.sh` ENTRIES comment and `scripts/mcp_launcher.py`), so the exposure is the `python -m` / direct-run path used for development and debugging.

## Problem
Under `python -m`, two copies of every module-level singleton exist: config, service, security posture, `FastAPI` app, and log handlers (for example the `Logger(...)` file handlers). The `__main__` copy loads its config before `restrict_to` runs, so config isolation (ADR-002) is not in effect for that load. The `__main__` copy evaluates `_enforce_posture_gate()` against its own posture, while `run_http()` gates and serves a different copy, so the gate that ran first does not describe the app that is served. The existing regression test passes while this still happens.

## Reason for Change
The acceptance criterion from the archived issue ("executes the module once") is not met on the real path, and its regression test gives false assurance. There is no deadline pressure; the affected path is the non-production launch path, which is why this is Medium rather than High.

## Implementation Intent
Make the start path independent of module identity: the process should gate and serve the same module instance that is already running, or the `__main__` block should delegate to a single canonical import so no module body executes twice. Keep the posture gate on every launch path (`mcp_launcher`, binaries, `python -m`) and keep the loopback and config-isolation checks before any socket is created. Decide the approach in the plan; do not move per-server config loading in this issue beyond what the single-execution fix requires.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (`MCPServer._enforce_startup_posture_gate`, `MCPServer.run_http`)
- The `if __name__ == "__main__":` blocks of the ten `*_server.py` modules and `scripts/mcp_servers/mdq/__main__.py`
- `tests/mcp_servers/test_config_isolation_import.py`
- `tests/mcp_servers/test_posture_gate_start_path.py`

## Required Changes
- Ensure a server module body executes exactly once when started with `python -m <module>` and with `runpy.run_module(..., run_name="__main__")`.
- Ensure the posture gate evaluated at start is the posture of the app object that uvicorn serves.
- Ensure `ConfigLoader.restrict_to` is in effect before the first config load on the `python -m` path, or record why that is not achievable and what the residual window is.
- Change the regression test so it runs the real `run_http()` (stubbing only the server run or socket creation) and asserts a single load of the server's own config file.

## Constraints
- Do not weaken the gate: a server without a gate must still refuse to start (`_enforce_startup_posture_gate` fails closed).
- Keep `MCPServer.run_http()` enforcing loopback binding and `own_config_file` isolation before any socket is created.
- Keep `uvicorn.Config(self.app_module, ...)` working for the launcher and the Nuitka binaries.
- `ConfigLoader.restrict_to` allows only one file set per process.

## Acceptance Criteria
- Starting a server module via `runpy.run_module(<module>, run_name="__main__")` with the real `run_http()` records exactly one load of that server's own config file.
- The posture that `_enforce_posture_gate()` checks is the posture exposed by the served app's `/health` response.
- The updated regression test fails on the current code (two loads) and passes after the fix.
- All ten servers and `python -m mcp_servers.mdq` still refuse to bind when the posture is not validated (`tests/mcp_servers/test_posture_gate_start_path.py` passes).

## Testing Expectations
- Regression test with the real `run_http()` for at least one server, ideally parametrized over all ten server modules.
- Run `uv run pytest tests/mcp_servers`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, and `uv run python tools/generate_reference_table.py --check`.

## Documentation Impact
Update the MCP lifecycle documentation only if it states when config isolation takes effect or how many times the server module executes. State the boundary and failure behavior, not implementation details. Run the checkers named in `routing.md` for any edited `docs/` file.

## Out of Scope
- Moving module-level config loading in each server into a factory or lifespan.
- Changing which config keys a server reads.
- Changes to the launcher discovery logic beyond what the single-execution fix needs.

## Dependencies
- Follow-up to `issues/done/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md` (archived; its acceptance criterion is not met on the real start path, so re-verify it against current source when planning).
- Related, no order required: `issues/done/20261029-012525_ebrev003_serverbase-posture-gate-outside-try.md`.
- No open issue under `issues/` and no in-flight plan under `plans/` targets `scripts/mcp_servers/server.py`.

## Unresolved Questions
- `Needs confirmation`: whether the two-copy posture can actually differ in production-like environments (the probe only showed two loads and one gate failure).
- `Needs confirmation`: whether any server's module-level side effects (for example log file handlers in `Logger(...)`) behave incorrectly when created twice; not tested in this review.
- `不明`: whether `python -m` is a supported launch mode for operators or only for development.

## AI Implementation Instruction
Keep the change minimal and confined to the start path and its tests. Do not refactor per-server modules. Do not weaken or reorder the loopback, config-isolation, and posture checks relative to socket creation. If the single-execution fix requires changing the launcher or the binaries, stop and report instead of widening scope. Report any open question rather than guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-132004
- **Related target files**: `scripts/mcp_servers/server.py`, the `if __name__ == "__main__":` blocks of the ten `*_server.py` modules and `scripts/mcp_servers/mdq/__main__.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/mcp_servers/test_posture_gate_start_path.py`
