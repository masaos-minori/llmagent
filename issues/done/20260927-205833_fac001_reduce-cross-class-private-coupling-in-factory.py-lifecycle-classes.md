# Reduce cross-class private coupling in factory.py lifecycle classes

## Priority
Medium

## Summary
Reduce the private cross-class coupling between `_ServerLifecycleRouter` and
`_SubprocessLifecycleManager` in `scripts/agent/factory.py` so the router
coordinates through the manager's public `LifecycleManagerProtocol` surface
instead of reaching into its private `_http_mgr` attribute.

## Background
`scripts/agent/factory.py` assembles `AgentContext` services; service injection
into `ctx.services` is separated from `AgentREPL` to enable testing. Two lifecycle
classes implement `LifecycleManagerProtocol`:

- `_ServerLifecycleRouter` — coordinator (state tracking, cooldown, shutdown guard).
- `_SubprocessLifecycleManager` — subprocess operations (start/restart/shutdown).

Both are wired into `ToolExecutor` and used exclusively through the protocol by
external callers (`scripts/shared/tool_executor.py`,
`scripts/shared/tool_transport_invoker.py`).

## Problem
`_ServerLifecycleRouter` accesses `_SubprocessLifecycleManager._http_mgr` (a private
instance attribute) at 12 call sites — lines 268, 275, 278, 287, 293, 314, 318, 337,
352, 360, 367, 382 — to perform operations that `_SubprocessLifecycleManager` already
exposes through its public `LifecycleManagerProtocol` methods (`ensure_ready`,
`shutdown_all`, `restart`, `get_process_snapshot`, `cleanup_server_resources`, ...).
This couples the coordinator to the manager's private internals across a class
boundary.

## Reason for Change
Maintainability and testability risk. The private access forces both classes to
evolve together: a rename or move of `_http_mgr` in the manager would break the
router silently. It also makes the router hard to unit-test in isolation, since
tests must stand up the real manager plus its `_http_mgr`. Because every external
interaction already goes through the protocol, routing the router through the
manager's public surface reduces coupling without changing any external behavior.

## Implementation Intent
Move the router's dependency on the manager from its private `_http_mgr` to its
public protocol surface. Where the router performs a passthrough the manager
already implements publicly, delegate to that method. Where the router wraps an
operation with shutdown-guard or cooldown logic, keep the wrapper but drive its
leaf operations through the manager's public protocol methods rather than
`_http_mgr`. Preserve the `LifecycleManagerProtocol` contract and all observable
behavior (state transitions, cooldown timing, process snapshots) exactly.

## Target Files or Areas
- `scripts/agent/factory.py` (primary)
- Reference: `scripts/agent/lifecycle_protocol.py` (protocol definition)
- Reference: `scripts/agent/http_lifecycle.py` (`HttpServerLifecycleManager` owns `_http_mgr`)
- Reference: `tests/agent/test_agent_factory.py` (existing regression coverage)

## Required Changes
- Replace direct `_subprocess_mgr._http_mgr.*` calls that have a matching public
  manager method with a call to that public method.
- For guarded wrappers (`ensure_ready`, `restart`, `start_http_subprocess`) that
  currently reach `_http_mgr` for leaf ops, route those leaf ops through the
  manager's public protocol methods where their semantics match; keep the
  shutdown-guard and cooldown handling intact.
- Drop any import or attribute introduced solely to support the private access;
  leave unrelated members untouched.
- Update the module/class docstrings only if they describe the private-delegation
  mechanism.

## Constraints
- Preserve the `LifecycleManagerProtocol` contract exactly — external callers use
  only the protocol.
- Preserve observable behavior: state-machine transitions (`assert_valid_transition`),
  cooldown window (`_COOLDOWN_SECONDS`), shutdown guard, and process-snapshot contents.
- Do not change which class owns `_http_mgr` or alter `HttpServerLifecycleManager`.
- Keep both classes implementing the protocol; do not collapse them into one.

## Acceptance Criteria
- No remaining `_subprocess_mgr._http_mgr` references in `_ServerLifecycleRouter`
  except where a public-method equivalent genuinely does not exist (such exceptions
  are documented in-code).
- Every `LifecycleManagerProtocol` method behaves identically before and after
  (verified by the existing lifecycle tests).
- No public API added or removed.
- `mypy` and `ruff` pass on the changed module.

## Testing Expectations
Run `tests/agent/test_agent_factory.py` (covers shutdown guard, cooldown,
`get_subprocess_server_configs`, lifecycle transitions); prefer the full `tests/agent/`
suite. Run `mypy` and `ruff` on `scripts/agent/factory.py`.

## Documentation Impact
Update the module docstring only if it currently describes the private-delegation
mechanism. No `docs/*.md` update required — public API and protocol unchanged.

## Out of Scope
- Refactoring other parts of `factory.py` (builder functions, `build_agent_context`
  sequential wiring).
- Changing `HttpServerLifecycleManager` or the `LifecycleManagerProtocol` definition.
- Collapsing the two lifecycle classes into a single class.
- Any behavioral or policy change.

## Dependencies
N/A: none

## Unresolved Questions
- Scope confirmation: is the intended refactor limited to reducing
  `_http_mgr` coupling, or does it include a broader restructure of `factory.py`
  (e.g. splitting the file, extracting builders, collapsing the two lifecycle
  classes)?
- Which of the 12 `_http_mgr` calls lack a clean public-method equivalent and
  therefore must stay (or warrant a thin public method added to the manager)?
- Is the two-class split (router + subprocess manager) itself desirable, or should
  coordination live in a single class?

## AI Implementation Instruction
Make a minimal, behavior-preserving change only. Do not expand scope beyond
reducing `_subprocess_mgr._http_mgr` access via the manager's public protocol
surface. Do not touch builder functions, `build_agent_context`,
`HttpServerLifecycleManager`, or the protocol definition. If a call has no public
equivalent, either add a thin documented public method to
`_SubprocessLifecycleManager` or leave the access with a one-line note — do not
invent new behavior. Preserve shutdown-guard, cooldown, and state-machine behavior
exactly. Run the existing lifecycle tests plus `mypy`/`ruff`; stop and report if
the `LifecycleManagerProtocol` contract cannot be preserved.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-205833
- **Related target files**: `scripts/agent/factory.py`
