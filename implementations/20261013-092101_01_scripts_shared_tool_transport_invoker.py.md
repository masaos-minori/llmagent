## Goal

Document and make visible the meaning of a `0`/negative per-server `tool_concurrency_limits`
value in `ToolTransportInvoker._ensure_semaphores`: a `0`/negative limit means "unlimited"
(no semaphore created), consistent with the unconfigured default, and a warning is emitted
when such a limit is seen for a known server key.

## Scope

- **In-Scope**:
  - Extend the `_ensure_semaphores` docstring in `scripts/shared/tool_transport_invoker.py`
    to state that a `0`/negative limit means "unlimited" (no semaphore created), consistent
    with the unconfigured default. (REQ-001)
  - Emit a `logger.warning` inside `_ensure_semaphores` for each known server key whose
    limit is `0`/negative, stating it is treated as unlimited (no semaphore). Preserve the
    existing `if n > 0` filter (behavior unchanged). (REQ-002)
- **Out-of-Scope**: Changing positive-limit semantics, semaphore acquisition order
  (`_execute_with_semaphore` / `_maybe_semaphore`), unknown-key warning handling, or the
  config reference doc (that is a separate row).

## Assumptions

- Option (a) is the resolved semantics: `0`/negative = "unlimited", documented + warned,
  NOT coerced to a minimum of `1`.
- `_ensure_semaphores` runs once per process (guarded by `if self._semaphores is None`), so
  the warning fires once per process.
- A "known server key" is one present in `self._server_configs` (set in `__init__`); the new
  warning targets only known keys, leaving the existing unknown-key warning untouched.

## Design decisions

- **Additive, behavior-preserving**: keep the existing `if n > 0` filter unchanged (0/
  negative still yields no semaphore = unlimited); only add a docstring sentence and a
  warning loop. Observable behavior for valid configs is unchanged.
- **Warn inside `_ensure_semaphores`, not `__init__`**: the Plan locates the warning here
  because the method is already guarded to run once per process, and it is the single place
  that iterates the limits when building semaphores.

## Alternatives considered
N/A: coercing `0` → `1` (option b) is explicitly rejected by the Plan as a potential
throughput regression; this document records only the resolved option (a).

## Implementation
### Target file
`scripts/shared/tool_transport_invoker.py`

### Procedure
1. Open `ToolTransportInvoker._ensure_semaphores` (lines 90-97).
2. Extend its docstring (currently line 91: `"""Lazily create concurrency semaphores from configuration limits."""`)
   to state that a `0`/negative limit means "unlimited" (no semaphore created), consistent
   with the unconfigured default.
3. Inside the `if self._semaphores is None and self._concurrency_limits:` guard (line 92),
   before the dict comprehension that builds `self._semaphores`, add a loop that finds each
   known server key whose limit is `0`/negative and emits a `logger.warning` stating it is
   treated as unlimited (no semaphore).
4. Do not modify the `if n > 0` filter, `_maybe_semaphore`, the unknown-key warning in
   `__init__` (lines 46-53), or semaphore acquisition.

### Method
Two edits inside `_ensure_semaphores`: a docstring extension and one warning loop. No new
imports (the module-level `logger` at line 24 is reused).

### Details
Current `_ensure_semaphores` (lines 90-97):
```python
    def _ensure_semaphores(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }
```
Proposed:
```python
    def _ensure_semaphores(self) -> None:
        """Lazily create concurrency semaphores from configuration limits.

        A `0` or negative limit means "unlimited": no semaphore is created for that
        server, exactly matching the unconfigured default (key omitted). Known server
        keys with a `0`/negative limit are warned about once (this method runs once
        per process) so the chosen meaning is visible instead of a silent drop.
        """
        if self._semaphores is None and self._concurrency_limits:
            # REQ-002: 0/negative limits resolve to "unlimited" (no semaphore). Warn
            # once per process for known server keys so the meaning is visible;
            # unknown keys are handled in __init__. Behavior is unchanged.
            for key, n in self._concurrency_limits.items():
                if n <= 0 and key in self._server_configs:
                    logger.warning(
                        "tool_concurrency_limits: %r is %d; treated as unlimited "
                        "(no semaphore created).",
                        key,
                        n,
                    )
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }
```
Evidence the claim matches control flow: `_ensure_semaphores()` is called once per logical
call at line 267 and is memoized via `if self._semaphores is None` (line 92), so the warning
fires once per process. `_maybe_semaphore` (lines 100-109) returns `nullcontext` for a
missing key, so a `0`-limit server runs unbounded — the documented behavior. The module
logger is `logging.getLogger(__name__)` (`shared.tool_transport_invoker`, line 24). The
config-field contract (`# Per-server concurrent call limit; empty = unlimited`,
`scripts/agent/config_dataclasses.py` lines 199-200) supports the "unlimited" reading.

## Compatibility considerations
N/A: additive and behavior-preserving for valid configs; a `0`/negative limit resolves to
the same state as omitting the key (the unconfigured default), so no throughput regression.

## Security considerations
N/A: no secret handling or fail-closed path touched. The warning surfaces operator intent;
it does not change access control.

## Rollback considerations
Revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/tool_transport_invoker.py` | Static lint/type on modified `_ensure_semaphores` | `uv run ruff check scripts/shared/tool_transport_invoker.py` · `uv run mypy --no-namespace-packages scripts/shared` | clean |
| `tests/shared/test_tool_transport_invoker.py` | New unit test for `0`/positive limit behavior | `uv run pytest tests/shared/test_tool_transport_invoker.py` | new + existing pass |
| `tests/shared/` | Shared-module suite regression | `uv run pytest tests/shared/` | all pass |

## Completion criteria
`_ensure_semaphores` docstring states `0`/negative = unlimited (no semaphore), a warning is
emitted for a `0`/negative limit on a known key, the `0`-limit/positive-limit test passes,
and `ruff`, `mypy`, and the shared-module suite pass.

## Out of scope
`scripts/shared/tool_transport_invoker.py` test (REQ-003) and the config reference doc
(`docs/23_agent/agent_08_03_configuration-tools-memory.md`, REQ-001) are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 2 | Document `0`/negative = unlimited in `_ensure_semaphores` docstring, emit warning for `0`/negative known-key limit (`tool_transport_invoker.py`) | Pending | — | — | REQ-001, REQ-002 |
| 3 | Add `0`-limit (unlimited + warning) and positive-limit (bounded) test; run ruff/mypy/shared-suite | Pending | — | — | REQ-003, REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: structural non-issue | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002` (document `0`/negative = unlimited in `_ensure_semaphores`; warn for `0`/negative known-key limit)
- **Source issue**: `issues/20261012-185224_mcp003_concurrency-limit-of-zero-silently-disables-the-per-server-semaphore-in-tooltransportinvoker.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261012-232916_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-092101
- **Related target files**: `scripts/shared/tool_transport_invoker.py`
