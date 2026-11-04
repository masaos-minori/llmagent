## Goal
- Make `_ServerLifecycleRouter.start_http_subprocess` a genuine explicit start: it no longer returns early because of the runtime failure cooldown, and it signals a start suppressed by shutdown with a new typed `StartSuppressedError` (new) instead of returning `None` (`REQ-001`: second startup attempt reaches the subprocess layer; `REQ-002`: suppression is a typed signal; `REQ-004`: runtime cooldown unchanged).

## Scope
**Release unit**: startup-start-contract

- One new exception class and one method of `scripts/agent/lifecycle_router.py`. `ensure_ready`, `restart`, `_in_cooldown`, and `_run_lifecycle_transition` are not changed. The characterization tests are separate procedures (`tests/agent/test_agent_factory.py`, `tests/agent/test_lifecycle.py`).

## Assumptions
- The router's `start_http_subprocess` has exactly one non-test caller, `McpServerStarter._start_http_subprocess_once` (repository search over `scripts/`, checked in Step 3a); `ensure_ready` calls the subprocess manager's own `start_http_subprocess` directly and applies `_in_cooldown` itself, as does `restart`.
- `FAILED -> STARTING` is a valid transition in `agent/lifecycle.py`, so the second start is not rejected by the state machine.
- `StartSuppressedError` (new) is consumed by the sibling procedure for `scripts/agent/startup_mcp_starter.py` (later `seq`), which maps it to `StartupInterrupted`.
- Only `TestCooldownCharacterization` pre-seeds `_failed_starts` in `tests/agent/test_lifecycle.py`; its rewrite is the sibling procedure for that file.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Define `StartSuppressedError` (new) as a `RuntimeError` subclass in this module, raised only by the shutdown guard of the start entry; the message names the server key.
- Drop the cooldown check from the start entry rather than adding a bypass flag: the entry is the explicit startup path, and runtime restarts reach the subprocess manager through `ensure_ready` and `restart`, which keep their checks. The method adds no branch (a `return None` becomes a `raise`, and one `if` is removed), so its complexity does not grow.

## Alternatives considered
- A bypass flag on the start entry, or a separate startup entry on the router: rejected by the Plan's Decision 1 because the only caller already is the startup path, and the shared `LifecycleManagerProtocol` signature stays unchanged.
- A result object instead of an exception: rejected by the Plan's Decision 2; a typed error cannot be mistaken for success.

## Implementation
### Target file
`scripts/agent/lifecycle_router.py`

### Procedure
1. Add the exception class `StartSuppressedError` (new) after the module helper `_is_http_subprocess_server` and before `_SubprocessLifecycleManager`.
2. In `_ServerLifecycleRouter.start_http_subprocess` (the router's own method, not the same-named method of `_SubprocessLifecycleManager`), replace the shutdown branch's `return None` with the raise and delete the `_in_cooldown` early return.
3. Update that method's docstring.

### Method
Add the class:

```python
class StartSuppressedError(RuntimeError):
    """Raised when a start is refused because the lifecycle router is shutting down."""
```

Replace the head of the router's `start_http_subprocess`.

Before:

```python
        """Start a single HTTP subprocess MCP server; returns the Popen object or None."""
        if self._shutting_down:
            _logger.debug(
                "Lifecycle: start_http_subprocess(%r) ignored — shutting down",
                server_key,
            )
            return None
        if self._in_cooldown(server_key):
            return None
        captured: subprocess.Popen[bytes] | None = None
```

After:

```python
        """Start a single HTTP subprocess MCP server and return its Popen object.

        This is the explicit start entry: the failure cooldown, which only throttles
        automatic restarts in ``ensure_ready`` and ``restart``, does not apply here.
        Raises StartSuppressedError when shutdown has begun.
        """
        if self._shutting_down:
            raise StartSuppressedError(
                f"start of MCP server {server_key!r} suppressed: shutting down"
            )
        captured: subprocess.Popen[bytes] | None = None
```

### Details
- The method signature and return annotation stay unchanged (`LifecycleManagerProtocol` and `_SubprocessLifecycleManager` share it).
- `_in_cooldown` stays: `ensure_ready` and `restart` still use it, so it is not dead code.
- `_logger.debug` for the suppressed branch is dropped because the raised error carries the same information.

## Compatibility considerations
- Behavior change for callers that relied on `None` after shutdown or during the cooldown: the only production caller is the starter (sibling procedure maps the error); mocks that replace the router are unaffected.
- `ensure_ready` and `restart` cooldown behavior is unchanged (`REQ-004`).

## Security considerations
N/A: no input handling, credential, or trust-boundary change; the error message contains only the server key.

## Rollback considerations
Revert the commit, or revert this file by single path. The release unit must be reverted together: reverting only this file leaves the starter importing a missing name and the characterization tests asserting `None`.

## Validation plan
- `uv run ruff format --check` and `uv run ruff check` on `scripts/agent/lifecycle_router.py`.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus` with no new errors; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `uv run python tools/check_module_size.py`.
- `uv run pytest tests/agent/test_agent_factory.py tests/agent/test_lifecycle.py -q`. Two characterization tests are an allowed red state until their sibling procedures rewrite them (release unit): `tests/agent/test_lifecycle.py::TestCooldownCharacterization::test_start_http_subprocess_returns_none_in_cooldown` and `tests/agent/test_agent_factory.py::TestRouterPostShutdownGuards::test_start_http_subprocess_returns_none_after_shutdown_all`; record both in the Failure Log.

## Completion criteria
- `start_http_subprocess` of the router no longer consults the cooldown and raises `StartSuppressedError` (new) when shutting down (`AC-1`, `AC-3`).
- `ensure_ready` and `restart` still refuse inside the cooldown window (`AC-4`).

## Out of Scope
- The starter's mapping to `StartupInterrupted`, the protocol docstring, the characterization tests in `tests/agent/test_lifecycle.py` and `tests/agent/test_agent_factory.py`, and the new integration-style tests (separate procedures).
- The cooldown window, `ensure_ready`, `restart`, and `_run_lifecycle_transition`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 20261104 | Added `StartSuppressedError`; dropped the cooldown early return and raised on shutdown. |
| 2 | Run the targeted tests of the Validation plan and record the allowed red states | Done | 20261104 | Red-state tests rewritten by #05 and #06; both pass after the unit lands. |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Done | 20261104 | ruff clean; mypy clean; lint-imports 6 kept; bandit 0 med/high; full suite 11467 passed. |

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
- **Requirement ID**: `REQ-001` (start entry ignores the cooldown), `REQ-002` (typed suppression signal), `REQ-004` (runtime cooldown unchanged)
- **Source issue**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095204_startretry001_startup-retry-blocked-cooldown.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-140850
- **Related target files**: `scripts/agent/lifecycle_router.py`
