## Goal

Correct three diagnostic inaccuracies in `MCPServer.run_http()` and `_LoopbackVerifyingServer.startup` in `scripts/mcp_servers/server.py` without changing any startup behavior (`REQ-001`/`REQ-002`/`REQ-003`). Reword the `except SystemExit` log line so it attributes an exit to `server.run()` rather than the posture gate, update the post-start verification docstring to state its post-bind timing and skip conditions, and remove the redundant function-local `import logging`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The plan's three corrections are independent and localized to `run_http()` and `_LoopbackVerifyingServer`; no other caller depends on the exact log wording (UNK-01 resolved below — see Security considerations).
- The module-level `import logging` at `server.py` `L16` remains valid after removing the function-local copy at `L277`; `logging.getLogger(...)` at `L330` resolves to the module-level name.
- `uvicorn` paths that can raise `SystemExit` from `server.run()` do not include a legitimate posture-gate signal that must be preserved (UNK-02; Low impact either way — recorded here, not enforced).
- The posture gate (`_enforce_startup_posture_gate()`) runs before the `try` at `L327`, so a gate `SystemExit` never reaches the `except SystemExit` handler; the handler only ever sees exits originating inside `server.run()`.

## Design decisions
- **Reword, do not delete, the `except SystemExit` message (REQ-001).** Replace `"Posture-gate failure during startup: %s"` with wording that attributes the exit to `server.run()` (for example `"Error while running server: %s"`), keep the `.error(...)` severity, keep the bare `raise`, and keep the trailing `if not server.started: sys.exit(1)`. The re-raise preserves the original `SystemExit` code (`e`), satisfying REQ-001's "same exit code".
- **Enhance the `_LoopbackVerifyingServer` docstring to state timing + skip conditions (REQ-002).** The existing class docstring (`server.py` `L303-305`) says the check verifies loopback "right after startup"; extend it to state that the check runs *after* `super().startup()` creates the listening sockets (post-bind, defense in depth) and that `startup()` returns early — skipping the check — when `self.should_exit` is set (startup aborted) or `self.servers` is empty (no server object). Keep the pre-bind `http_host` allow-list (`L281-286`) as the authoritative guard.
- **Remove only the redundant `import logging` (REQ-003).** Delete the function-local `import logging` at `L277`; leave `import sys` (still needed for `sys.exit(1)` at `L336`) and the module-level `import logging` at `L16` untouched.

## Alternatives considered
- **Delete the `except SystemExit` handler entirely.** Rejected — it preserves the re-raise semantics and the `sys.exit(1)` follow-up; deleting it would change control flow. Only the message text changes.
- **Rename the log level or add structured fields.** Rejected — out of scope; REQ-001 only requires the message to stop claiming a posture-gate failure. Keep it a single `.error(msg, e)` call.
- **Move the loopback check before socket creation.** Rejected by the plan's Scope — the pre-bind `http_host` allow-list stays authoritative; ordering is frozen.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Locate the `except SystemExit` handler in `run_http()`, `server.py` `L329-333`:
```python
        except SystemExit as e:  # noqa: BLE001 — SystemExit originating from server.run() itself; logged and re-raised, with the sys.exit(1) follow-up below
            logging.getLogger(type(self).__name__).error(
                "Posture-gate failure during startup: %s", e
            )
            raise
```
2. Change the message string from `"Posture-gate failure during startup: %s"` to a wording that attributes the exit to `server.run()` and does not mention the posture gate, for example `"Error running server during startup: %s"`. Keep the `logging.getLogger(...).error(...)` call, the bare `raise`, and the `# noqa: BLE001` comment intact.
3. Locate the `_LoopbackVerifyingServer` class docstring, `server.py` `L303-305`:
```python
            """Verifies the actual bound socket address is loopback right
            after startup, confirming the OS-level bind matches the
            already-validated `http_host` rather than trusting it blindly."""
```
4. Extend that docstring to state (a) the check runs after `super().startup()` creates the listening sockets (post-bind, defense in depth) and (b) `startup()` skips the check when `self.should_exit` is set or `self.servers` is empty. Keep the reference to the pre-bind `http_host` allow-list as the authoritative guard.
5. Remove the redundant function-local `import logging` at `server.py` `L277`, leaving the module-level `import logging` at `L16`.

### Method
Three localized edits inside `run_http()` / `_LoopbackVerifyingServer`: one string replacement (message), one docstring extension, one line deletion (import). No signature, control-flow, ordering, or behavior change.

### Details
Import region before edit, `server.py` `L277-278`:
```python
        import logging
        import sys
```
After edit:
```python
        import sys
```
`logging.getLogger(...)` at `L330` resolves to the module-level `logging` (`L16`); nothing else in `run_http()` references the local binding.

Message edit, `server.py` `L330-332`:
```python
            logging.getLogger(type(self).__name__).error(
                "Error running server during startup: %s", e
            )
```
The bare `raise` immediately after still re-raises the original `SystemExit(e)` with its exit code unchanged (REQ-001).

Docstring edit, `server.py` `L303-305` →
```python
            """Verifies the actual bound socket address is loopback after
            startup, confirming the OS-level bind matches the
            already-validated `http_host` rather than trusting it blindly.

            This runs after ``super().startup()`` has created the listening
            sockets, so it is a post-bind defense-in-depth check; the pre-bind
            ``http_host`` allow-list (checked before the socket is created) is
            the authoritative guard. ``startup()`` returns early and skips this
            check when ``self.should_exit`` is set (startup aborted) or
            ``self.servers`` is empty (no server object exists)."""
```
Keep the surrounding method body (`await super().startup(sockets=sockets)` then the `if self.should_exit or not getattr(self, "servers", None): return` guard) unchanged.

### Companion test files
- `tests/mcp_servers/test_mcp_server_base.py`
  - Procedure: add one test asserting a `SystemExit` from `server.run()` is re-raised with the same exit code and logged with the new (non-posture-gate) wording; no change to existing tests.
  - Validation: `uv run pytest tests/mcp_servers/test_mcp_server_base.py` passes after the `server.py` edits.

## Compatibility considerations
- Purely cosmetic: startup ordering, the posture gate, the loopback allow-list, the re-raise, and the `sys.exit(1)` follow-up are all unchanged. An empty/non-loopback bind, config-isolation failure, and gate failures behave identically.
- The log message text changes; any external matcher on the old string `"Posture-gate failure during startup"` stops matching (see Security considerations / UNK-01).

## Security considerations
- No security-posture change: the empty-token refusal, the loopback-only bind enforcement, and the posture gate are untouched.
- UNK-01 (alerting/doc match on the old string): searched the repo — `"Posture-gate failure during startup"` appears only in `scripts/mcp_servers/server.py` `L331` (the line being changed) and in documentation (issue/plan references), never in a runtime alert rule or application matcher. Rewording is safe; if a future external alert matches the string, update that alert.

## Rollback considerations
- Revert the commit; all three edits are isolated to one message string, one docstring, and one import line. Behavior is byte-identical apart from the log wording.

## Validation plan
- `uv run pytest tests/mcp_servers/test_mcp_server_base.py` — existing tests pass plus the new message/re-raise assertion (REQ-001/REQ-004).
- `uv run pytest tests/mcp_servers/test_posture_gate_start_path.py` — posture-gate ordering unaffected.
- `uv run ruff check scripts/mcp_servers` — no unused/redefined import; the removed `import logging` leaves no dangling reference (REQ-003).
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` — clean.

## Completion criteria
- `REQ-001`: a `SystemExit` from `server.run()` is re-raised with the same exit code and a log message that does not mention the posture gate.
- `REQ-002`: the `_LoopbackVerifyingServer.startup` docstring states the post-bind timing and the `self.should_exit` / empty-`self.servers` skip conditions.
- `REQ-003`: `ruff check` reports no unused or redefined import in `server.py` (the redundant `import logging` removed).
- `REQ-004`: existing tests pass and a test asserts the corrected message and re-raise.

## Out of Scope
- Changing the order of the loopback allow-list check, config-isolation check, posture gate, and socket creation.
- Any change to `_enforce_startup_posture_gate()` behavior or the double-execution problem tracked in `issues/20261107-132004_mcpstartup001_python-m-double-execution.md`.
- Changing the loopback allow-list values (`127.0.0.1`, `::1`), uvicorn config, log levels, or exit codes.
- The `import sys` (still required by `sys.exit(1)`).

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
- **Requirement ID**: `REQ-001` (SystemExit message + re-raise), `REQ-002` (post-start docstring timing/skip), `REQ-003` (redundant `import logging` removed)
- **Source issue**: `issues/20261107-132117_mcpstartup004_run-http-diagnostics-cleanup.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-214719_mcpstartup004_run-http-diagnostics-cleanup.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-085934
- **Related target files**: `scripts/mcp_servers/server.py`, `tests/mcp_servers/test_mcp_server_base.py`
