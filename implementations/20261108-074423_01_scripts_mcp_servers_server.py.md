## Goal

Make `scripts/mcp_servers/server.py` correct on the `python -m` / direct-run launch path: stop `_enforce_startup_posture_gate()` from executing the server module body a second time, and make the `run_http()` startup diagnostics describe what the code actually does — without changing startup behavior, exit codes, or the pre-bind check ordering (`REQ-001`/`REQ-002`/`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Plan's open single-execution mechanism decision (approach (a) centralized vs (b) per-module `__main__` delegation) is mutually exclusive across this whole Plan; pick one and apply it consistently to `server.py` and the eleven entry files. This document covers the `server.py` side of whichever approach is chosen.
- Under approach (b), the entry files import the module under its real name, so `_enforce_startup_posture_gate()`'s `importlib.import_module(module_name)` already resolves the running instance and needs no change here — only the diagnostic corrections apply.
- Under approach (a), the gate must be guarded so the second copy is never created; the entry-file documents implement the delegation-free variant.
- The `SystemExit` mislabel, the `_LoopbackVerifyingServer` docstring, and the redundant `import logging` are corrected under both approaches.

## Design decisions
- **Single-execution mechanism (drives `REQ-001`):** record the chosen approach in the implementation before coding. Approach (a) guards the re-import in `_enforce_startup_posture_gate()` with `sys.modules.get(module_name)` (one-file fix, leaves entry files unchanged). Approach (b) rewrites each entry file's `if __name__ == "__main__":` to a single canonical import and leaves this file's gate untouched (only diagnostics corrected). Do not mix approaches within this Plan.
- **Diagnostic corrections are approach-independent:** the `except SystemExit` reword, the `_LoopbackVerifyingServer` docstring, and the `import logging` removal apply regardless of the `REQ-001` mechanism.

## Alternatives considered
- Leaving the `except SystemExit` message unchanged: rejected — it misattributes any `server.run()` exit to the posture gate.
- Reordering the loopback allow-list after socket creation: rejected — the pre-bind `http_host` allow-list is the authoritative guard; the post-start check stays defense-in-depth.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Apply the chosen single-execution mechanism to the gate (`REQ-001`): guard the re-import under approach (a); leave the gate as-is under approach (b) and confirm the module is already in `sys.modules` via the entry-file delegation.
2. Correct the three diagnostics in `run_http()` / `_LoopbackVerifyingServer` (`REQ-002`/`REQ-003`).

### Method
Edit `_enforce_startup_posture_gate` (current L257-259) and `run_http` (current L266-337) in `scripts/mcp_servers/server.py`.

### Details
- **Single execution (`REQ-001`):** Under approach (a), change L257-259 from `importlib.import_module(module_name)` to read the already-loaded instance: `sys.modules.get(module_name)`, then fall back to raising the same `RuntimeError` when the module defines no `_enforce_posture_gate`. Keep the `if not module_name.startswith("mcp_servers."):` early return. Under approach (b), make no change here — verify the entry files import under the real module name so this gate resolves the same instance.
- **`SystemExit` mislabel (`REQ-002`):** In `run_http`, reword the `except SystemExit` handler (current L329-333) so the log message attributes the exit to `server.run()` and does not claim a posture-gate failure. Keep `raise` (re-raise unchanged) and the `if not server.started: sys.exit(1)` follow-up (current L336-337) unchanged.
- **`_LoopbackVerifyingServer` docstring (`REQ-002`):** Update the class docstring (current L303-305) to state that `startup()` runs after `super().startup()` creates the listening sockets and returns early when `self.should_exit` is set or `self.servers` is empty; the pre-bind `http_host` allow-list (current L282-286) remains the authoritative guard.
- **Redundant import (`REQ-003`):** Remove the function-local `import logging` (current L277); the module-level `logging` import remains. `import sys` (current L278) stays.

## Compatibility considerations
- Exit codes and the fail-fast gate-`SystemExit` propagation (before any socket) are unchanged; only the log wording for a `server.run()` `SystemExit` changes.
- Approach choice must not break `uvicorn.Config(self.app_module, ...)` for the launcher and Nuitka binaries.

## Security considerations
- The posture gate must still fail closed when a module defines no `_enforce_posture_gate`; approach (a) preserves the `RuntimeError` on missing gate.
- Loopback-only binding is unchanged; the pre-bind allow-list stays the authoritative check.

## Rollback considerations
- N/A: revert the commit; the change is diagnostic-only plus a guarded import that restores the prior re-import behavior on revert.

## Validation plan
- `uv run pytest tests/mcp_servers/test_posture_gate_start_path.py` — pass.
- `uv run pytest tests/mcp_servers` — new and existing tests pass.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` — clean.
- `uv run python tools/generate_reference_table.py --check` — no drift.

## Completion criteria
- `REQ-001`: `_enforce_startup_posture_gate()` does not execute the server module body a second time under `python -m` (approach (a) guards the import; approach (b) resolves the already-imported instance).
- `REQ-002`: the `except SystemExit` log does not mention the posture gate; the `_LoopbackVerifyingServer` docstring matches its post-bind timing and skip conditions.
- `REQ-003`: `ruff check` reports no unused/redefined `logging` import in `server.py`.

## Out of Scope
- Rewriting the eleven entry-file `__main__` blocks (that is approach (b)'s work, covered by the entry-file documents of this Plan).
- Changing the loopback allow-list values, the config-isolation ordering, or any exit code.
- Any change to `_enforce_startup_posture_gate` fail-closed semantics beyond the approach-(a) import guard.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (single execution), `REQ-002` (diagnostic accuracy), `REQ-003` (config-isolation ordering before first load)
- **Source issue**: `issues/20261107-132004_mcpstartup001_python-m-double-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-213404_mcpstartup001_python-m-double-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-074423
- **Related target files**: `scripts/mcp_servers/server.py`
