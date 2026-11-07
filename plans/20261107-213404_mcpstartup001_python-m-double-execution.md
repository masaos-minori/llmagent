## Goal
Make every MCP server start path (`python -m mcp_servers.<pkg>.<server>`, `runpy.run_module(..., run_name="__main__")`, the launcher, and the Nuitka binaries) execute the server module exactly once, so the security-posture gate and the config-isolation check that run at start describe the same module instance that uvicorn serves. Eliminate the second in-process module copy that currently exists under the `python -m` / direct-run development path and that the existing regression test cannot observe.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/mcp_servers/server.py` — `MCPServer.run_http` and `MCPServer._enforce_startup_posture_gate` so the gate and config-isolation run against the already-running module instance and the startup diagnostics are accurate.
  - The `if __name__ == "__main__":` blocks of the ten `*_server.py` modules and `scripts/mcp_servers/mdq/__main__.py` so they delegate to a single canonical import instead of re-executing the module body.
  - `tests/mcp_servers/test_config_isolation_import.py` — repair the single-execution regression test so it exercises the real `run_http()` path.
  - `tests/mcp_servers/test_posture_gate_start_path.py` — extend the mdq entry-point assertions to cover the real `run_http()` path.
- **Out-of-Scope**:
  - Moving module-level config loading in each server into a factory or lifespan.
  - Changing which config keys a server reads.
  - Changing the launcher discovery logic beyond what the single-execution fix needs.
  - Any change to `_enforce_startup_posture_gate` fail-closed semantics or to the loopback/config-isolation ordering relative to socket creation.
- **Dependencies**: The Issue follows the archived `issues/done/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md`; its acceptance criterion ("executes the module once") is not met on the real start path, so re-verify it against current source when planning. Related, no order required: `issues/done/20261029-012525_ebrev003_serverbase-posture-gate-outside-try.md`. Sequencing note: sibling issues `issues/20261107-132052_mcpstartup003_auth-guard-single-point.md` and `issues/20261107-132117_mcpstartup004_run-http-diagnostics-cleanup.md` also edit `scripts/mcp_servers/server.py`; sequence their edits against this Plan to avoid conflicts in that file (no hard ordering dependency — these are sequencing-only notes, not `Depends on` entries).

## Background
Archived issue `issues/done/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md` required that `python -m <server module>` executes the module once, and `tests/mcp_servers/test_config_isolation_import.py` gained `test_a_server_module_executes_once_under_python_m`. The `_enforce_startup_posture_gate()` method in `MCPServer` was added later (evidence label: `Explicit in code`). Current source verified against HEAD `47b837eb8`; `scripts/mcp_servers/server.py` is unchanged since the review head `59dbae624`.

## Problem
Under `python -m`, two copies of every module-level singleton exist: config, service, security posture, the FastAPI app, and log handlers. `_enforce_startup_posture_gate()` resolves `_enforce_posture_gate` from `importlib.import_module(self.app_module.partition(":")[0])`; because the running module is registered as `__main__` rather than `mcp_servers.<pkg>.<server>`, that import executes the module body a second time. The `__main__` copy loads its config before `restrict_to` runs, so config isolation (ADR-002) is not in effect for that load. The `__main__` copy evaluates the posture gate against its own state while `run_http()` gates and serves a different copy, so the gate that ran first does not describe the served app. The existing regression test replaces `MCPServer.run_http` with a no-op and never reaches the gate, so it passes while the double execution continues.

## Reason for Change
The archived acceptance criterion ("executes the module once") is not met on the real path, and its regression test gives false assurance. There is no deadline pressure; the affected path is the non-production launch path used for development and debugging (production uses the launcher, which applies `restrict_to` before import), which is why this is Medium rather than High.

## Implementation Intent
Make the start path independent of module identity. Choose one of two mechanisms and record the choice in the Plan's Design: (a) centralize in `server.py` so the process gates and serves the module instance already running (the gate stops re-importing a second copy), or (b) make each `__main__` block delegate to a single canonical import so the module body runs once. Keep the posture gate on every launch path (`mcp_launcher`, binaries, `python -m`) and keep the loopback and config-isolation checks before any socket is created. Decide the approach in the plan; do not move per-server config loading in this issue beyond what the single-execution fix requires.

## Requirements
- `REQ-001`: A server module body executes exactly once when started with `python -m <module>` and with `runpy.run_module(..., run_name="__main__")` for every one of the ten servers and `python -m mcp_servers.mdq`.
- `REQ-002`: The posture that `_enforce_startup_posture_gate()` checks is the posture exposed by the served app's `/health` response.
- `REQ-003`: `ConfigLoader.restrict_to` is in effect before the first config load on the `python -m` path, or the residual window is recorded.
- `REQ-004`: The regression test in `test_config_isolation_import.py` runs the real `run_http()` (stubbing only the server run or socket creation) and asserts a single load of the server's own config file.

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/server.py` | Modify | `run_http` re-raises a `SystemExit` from `server.run()` through a handler labeled "Posture-gate failure during startup" (mislabel); `_enforce_startup_posture_gate()` re-imports the module via `importlib.import_module`, executing it a second time under `python -m`. Fix the label and make the gate serve the already-running instance. | `REQ-001`/`REQ-002`/`REQ-003` | `_enforce_startup_posture_gate` L257 `importlib.import_module`; `run_http` `except SystemExit` logs "Posture-gate failure during startup" (checked in Step 2) | `test_posture_gate_start_path.py` | `Verified` |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | `if __name__ == "__main__"` block re-executes the module body under `python -m`; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__":` present at module end (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `scripts/mcp_servers/file/delete_server.py` | Modify | Same `__main__` double-execution pattern; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__":` present (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `scripts/mcp_servers/file/read_server.py` | Modify | Same `__main__` double-execution pattern; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__":` present (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `scripts/mcp_servers/file/write_server.py` | Modify | Same `__main__` double-execution pattern; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__":` present (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `scripts/mcp_servers/git/git_server.py` | Modify | Same `__main__` double-execution pattern; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__": _enforce_posture_gate(); server = GitMCPServer(); server.run_http()` (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `scripts/mcp_servers/github/github_server.py` | Modify | Same `__main__` double-execution pattern; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__":` present (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `scripts/mcp_servers/mdq/__main__.py` | Modify | Entry point `python -m mcp_servers.mdq` imports the class then calls `run_http()`, which re-imports the module; delegate through a single canonical import. | `REQ-001` | `from mcp_servers.mdq.mdq_server import MdqMCPServer` then `MdqMCPServer().run_http()` (checked in Step 3) | `test_posture_gate_start_path.py` | `Verified` |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | Same `__main__` double-execution pattern; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__":` present (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | Same `__main__` double-execution pattern; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__":` present (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `scripts/mcp_servers/shell/shell_server.py` | Modify | Same `__main__` double-execution pattern; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__":` present (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `scripts/mcp_servers/web_search/web_search_server.py` | Modify | Same `__main__` double-execution pattern; delegate to a single canonical import. | `REQ-001` | `if __name__ == "__main__":` present (checked in Step 3) | `test_config_isolation_import.py` | `Verified` |
| `tests/mcp_servers/test_config_isolation_import.py` | Modify | `test_a_server_module_executes_once_under_python_m` stubs `run_http`, so it never reaches `_enforce_startup_posture_gate()` and cannot see the second import; rewrite to exercise the real `run_http()` path. | `REQ-004` | `MCPServer.run_http = lambda self: None` then `runpy.run_module(...)` (checked in Step 2) | `test_config_isolation_import.py` | `Verified` |
| `tests/mcp_servers/test_posture_gate_start_path.py` | Modify | Existing mdq entry-point tests stub `run_http`; extend them to assert single execution through the real `run_http()` path. | `REQ-001`/`REQ-004` | `patch.object(MCPServer, "run_http", ...)` in `test_running_the_mdq_entry_module_goes_through_run_http` (checked in Step 3) | `test_posture_gate_start_path.py` | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/dispatch.py` | `run_http` imports `dispatch` and shares the posture-gate lifecycle; read to confirm the gate still runs before any socket after the edit. | `scripts/mcp_servers/server.py` |
| `deploy/build_binaries.sh` | Documents the production ENTRIES launcher path that applies `restrict_to` before import; confirms the exposure is the `python -m` / direct-run path only. | `scripts/mcp_servers/server.py` (`REQ-003`) |
| `scripts/mcp_launcher.py` | Launcher path that applies `restrict_to` before import; read to keep the gate on the production launch path. | `scripts/mcp_servers/server.py` (`REQ-003`) |

## Acceptance Criteria
- `REQ-001`: Starting a server module via `runpy.run_module(<module>, run_name="__main__")` with the real `run_http()` records exactly one load of that server's own config file, for all ten servers and `python -m mcp_servers.mdq`.
- `REQ-002`: The posture that `_enforce_startup_posture_gate()` checks equals the posture exposed by the served app's `/health` response.
- `REQ-003`: `ConfigLoader.restrict_to` is in effect before the first config load on the `python -m` path, or the residual window is recorded in the implementation procedure.
- `REQ-004`: The updated regression test fails on the current code (two loads) and passes after the fix; `test_posture_gate_start_path.py` still passes.

## Tests
- Parametrized regression over all ten server modules plus `python -m mcp_servers.mdq` that runs the real `run_http()` (stubbing only uvicorn run or socket creation) and asserts a single config load (`REQ-001`/`REQ-004`).
- `test_posture_gate_start_path.py`: extend the mdq entry-point assertions to cover the real `run_http()` path (`REQ-001`).

## Documentation Impact
Update the MCP lifecycle documentation only if it states when config isolation takes effect or how many times the server module executes. State the boundary and failure behavior, not implementation details. Name the target doc via `docs/00_index.md` "Document References by Task" → mcp domain. Run the `docs/` checkers from `routing.md` for any edited doc.

## Assumptions
- The `__main__` blocks of all ten servers follow the same pattern as `git_server.py` (`_enforce_posture_gate()` + instantiate + `run_http()`), verified for `git_server.py`, `shell_server.py`, `web_search_server.py`, and `mdq/__main__.py` in Step 3.
- Making `__main__` delegate to a canonical import does not change which config file each server loads; it only changes *when* the module body runs.
- The chosen approach keeps `uvicorn.Config(self.app_module, ...)` working for the launcher and the Nuitka binaries.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether the two-copy posture can actually differ in production-like environments (the probe only showed two loads and one gate failure) | probe showed two loads and one gate failure; production launch uses the launcher, not `python -m` | record in the implementation procedure; confirm with owner if the `python -m` path is operator-facing | `False` |
| `UNK-02` | whether any server's module-level side effects (for example log file handlers in `Logger(...)`) behave incorrectly when created twice | not tested in this review | enumerate per-server module-level side effects during implementation; add to validation | `False` |
| `UNK-03` | whether `python -m` is a supported launch mode for operators or only for development | not stated in docs or config | confirm with owner; affects whether startup validation is worth adding | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/server.py` | Modify | all launch paths (launcher, binaries, `python -m`) and every server | 7 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/git/git_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/shell/shell_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/web_search/web_search_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/github/github_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/mdq/__main__.py` | Modify | `python -m mcp_servers.mdq` entry point only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/read_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/write_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/delete_server.py` | Modify | that server's `python -m` / direct-run path only | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/test_config_isolation_import.py` | Modify | that regression test only | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/test_posture_gate_start_path.py` | Modify | that test file only | N/A | N/A | not applicable (rsynced) |

## Design
**Open decision — single-execution mechanism (drives `REQ-001`):**
- **Approach (a) centralized in `server.py`.** Make `_enforce_startup_posture_gate()` and `run_http()` operate on the module instance already running instead of re-importing it. Under `python -m`, guard the re-import with `sys.modules.get(module_name)` so the second copy is never created. This fixes all ten servers and `mdq` from one edit point and leaves the `__main__` blocks unchanged. Downside: the `__main__` block still runs module-level code once as `__main__`; the gate must then read posture from that same instance.
- **Approach (b) per-module `__main__` delegation.** Rewrite each `if __name__ == "__main__":` block to `from mcp_servers.<pkg> import <server>` and call `<Server>().run_http()`, so the module is imported under its real name (already in `sys.modules`) and `run_http()`'s gate resolves the same instance. Fixes the double import at the source but touches all eleven entry files.
- Record the chosen approach and its blast-radius trade-off in the implementation procedure. Approach (a) is lower blast radius (one file); approach (b) is more explicit but touches every server.

**Secondary correction — diagnostic accuracy (`REQ-002`/`REQ-003`):** The `except SystemExit` in `run_http` logs "Posture-gate failure during startup" for any `SystemExit` from `server.run()`, which is not a posture-gate failure (the gate runs before the `try`). Rephrase the message and state the post-start loopback check's actual timing/skip conditions in its docstring. Keep re-raising the `SystemExit` and `sys.exit(1)` unchanged.

**Baseline (Step 5):** radon rates `run_http` B(6) and `build_tools_response` B(7); `bandit -ll` reports no high/medium findings; `lint-imports` 6 kept / 0 broken; `server.py` churn 7 commits in 30 days (high-churn file — scope the edit tightly).

## Implementation steps
1. **Phase 1: Choose the single-execution mechanism and document it.** Decide approach (a) vs (b) (Requirement `REQ-001`); record the blast-radius trade-off in the implementation procedure. No file change yet.
2. **Phase 2: Apply the chosen fix.** Under (a), edit `MCPServer._enforce_startup_posture_gate` / `run_http` in `scripts/mcp_servers/server.py` to serve the already-running instance; under (b), rewrite the `if __name__ == "__main__":` blocks of the ten `*_server.py` modules and `scripts/mcp_servers/mdq/__main__.py` to delegate to a single canonical import. Keep the posture gate on every launch path and keep `restrict_to` before the first config load (`REQ-001`/`REQ-003`).
3. **Phase 3: Correct the diagnostic mislabel.** Rephrase the `except SystemExit` message in `run_http` and update the `_LoopbackVerifyingServer` docstring to state its post-bind timing and skip conditions (`REQ-002`). Do not reorder any startup check or change exit codes.
4. **Phase 4: Repair the tests.** Rewrite `test_a_server_module_executes_once_under_python_m` in `tests/mcp_servers/test_config_isolation_import.py` to run the real `run_http()` and assert a single config load; extend `tests/mcp_servers/test_posture_gate_start_path.py` to cover the real `run_http()` path (`REQ-004`).
5. **Phase 5: Deployment & verification.** Run the validation commands below; confirm the updated regression test fails on current code and passes after the fix.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/server.py` | Unit / integration | `uv run pytest tests/mcp_servers` | new and existing tests pass; updated regression test fails pre-fix |
| All ten servers + `mcp_servers.mdq` | Integration (parametrized) | real `run_http()` with uvicorn run stubbed | exactly one config load per module |
| `scripts/mcp_servers/server.py` | Static | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | clean |
| Reference table | Static | `uv run python tools/generate_reference_table.py --check` | no drift |

## Risks
- **Risk**: approach (b) touches all eleven entry files, raising merge-conflict risk with sibling issues `mcpstartup003` and `mcpstartup004` that also edit `scripts/mcp_servers/server.py`. → **Mitigation**: sequence the edits against those plans; prefer approach (a) (single-file) when the blast radius matters.
- **Risk**: high 30-day churn (7 commits) on `server.py` means the file may have moved during planning. → **Mitigation**: re-verify the target sections at Step 8 freeze against current content.
- **Risk**: making `__main__` delegate to a canonical import could change which module-level code runs before `run_http()` for some servers. → **Mitigation**: verify each server's module-level side effects are idempotent under a single import.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Choose the single-execution mechanism (a centralized / b per-module) | Pending | — | — | Open design decision in Design section |
| 2 | Apply the chosen single-execution fix | Pending | — | — | `server.py` and/or the eleven entry files |
| 3 | Correct the `SystemExit` diagnostic mislabel | Pending | — | — | `run_http` message + `_LoopbackVerifyingServer` docstring |
| 4 | Repair the regression and mdq entry-point tests | Pending | — | — | `test_config_isolation_import.py`, `test_posture_gate_start_path.py` |
| 5 | Deployment & verification | Pending | — | — | run validation commands; regression test fails pre-fix |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-132004_mcpstartup001_python-m-double-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-213404
- **Related target files**: `scripts/mcp_servers/server.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/file/delete_server.py`, `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/github/github_server.py`, `scripts/mcp_servers/mdq/__main__.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/web_search/web_search_server.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/mcp_servers/test_posture_gate_start_path.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
