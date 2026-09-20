# Refactor scripts/agent/factory.py — reduce complexity, fix dead code, improve type safety

## Priority
Medium

## Summary
Refactor `scripts/agent/factory.py` to address SRP violations, remove dead code, standardize builder function patterns, and improve type annotations across the module.

## Background
`factory.py` is the central assembly point for AgentContext services. It contains two large classes (`_ServerLifecycleRouter`, ~200 lines), seven `_build_*` helper functions, and the main `build_agent_context()` orchestrator. The module has accumulated complexity over time through incremental additions without architectural review.

## Problem
The module has five concrete problems:
- Dead constant `_COOLDOWN_TIMEOUT_SEC` is defined but never referenced anywhere in the codebase.
- `_ServerLifecycleRouter` violates SRP: it manages lifecycle states, cooldown logic, subprocess coordination, process snapshots, resource cleanup, and config filtering — six distinct responsibilities in one class.
- Builder functions have inconsistent return patterns: some return tuples (`_build_llm_client`, `_build_tool_executor`, `_build_history_manager`), others return single values. Memory builders use `object` type annotations instead of proper generics.
- `build_agent_context()` is a god function that sequentially wires all services without clear responsibility boundaries.
- `_ServerLifecycleRouter` accesses private attributes (`_http_mgr._http_procs`) from outside its owning module, breaking encapsulation.

## Adversarial Validation

| Claim | Status | Evidence |
|---|---|---|
| `_COOLDOWN_TIMEOUT_SEC` is unused | Confirmed | Only defined at `factory.py:46`; grep finds zero references elsewhere |
| `_ServerLifecycleRouter` violates SRP | Confirmed | 16 methods covering 6 distinct responsibilities: state management, cooldown logic, lifecycle transitions, subprocess coordination, process snapshot API, resource cleanup/config filtering |
| Builder functions have inconsistent return patterns | Partially confirmed | `_build_llm_client`, `_build_tool_executor`, `_build_history_manager` return tuples; memory builders return single values. Callers consume tuples correctly (lines 510-512), so not a functional bug but a consistency concern |
| `build_agent_context()` is a god function | Confirmed | Sequentially wires all services without clear responsibility boundaries |
| Private attribute access breaks encapsulation | Confirmed but fix differs | `factory.py:196` accesses `self._http_mgr._http_procs` directly; however `HttpServerLifecycleManager` already has a public `verify_running()` method serving this purpose — no new method needed, just replace the access |
| Memory builders use `object` type annotations | Confirmed | `_build_embedding_client` and `_build_jsonl_store` return `-> object` |
| Tests mock `_ServerLifecycleRouter` | Confirmed | 38+ references in `tests/agent/test_lifecycle.py` and `tests/agent/test_agent_factory.py` |

## Reason for Change
This refactor reduces cognitive load for future contributors, eliminates dead code that confuses readers, and makes the service assembly pipeline more testable by isolating each builder into a clearly bounded unit. No behavioral change is required — this is purely structural.

## Implementation Intent
Apply these changes in order, each preserving public behavior:

1. **Remove dead code**: Delete `_COOLDOWN_TIMEOUT_SEC`. Keep `_COOLDOWN_SECONDS` as the sole cooldown constant.

2. **Split `_ServerLifecycleRouter`**: Extract subprocess lifecycle methods (`ensure_ready`, `start_http_subprocess`, `restart`, `shutdown_idle`) into a new `_SubprocessLifecycleManager` class. Keep state/cooldown logic in `_ServerLifecycleRouter` as a coordinator. Both implement `LifecycleManagerProtocol`.

3. **Standardize builder patterns**: Each `_build_*` function should return a single typed value (not a tuple). For multi-return builders, introduce a named dataclass or return via keyword arguments. Replace `object` type annotations in memory builders with proper generic bounds.

4. **Fix private attribute access**: Replace `self._http_mgr._http_procs.get(server_key)` with `self._http_mgr.verify_running(server_key)` — `HttpServerLifecycleManager` already has a public `verify_running()` method that serves this purpose; no new method is needed.

5. **Simplify `build_agent_context`**: Introduce a `ServiceAssembly` class that holds the assembled services, making the wiring step explicit and testable.

## Target Files or Areas
- `scripts/agent/factory.py` (primary)
- `scripts/agent/lifecycle_protocol.py` (may need protocol updates if `_ServerLifecycleRouter` interface changes)
- `scripts/agent/http_lifecycle.py` (no changes needed — `verify_running()` already exists)
- `scripts/agent/context.py` (`AppServices` constructor may need signature update)

## Required Changes
- Remove `_COOLDOWN_TIMEOUT_SEC` constant (line 46).
- Split `_ServerLifecycleRouter` into `_ServerLifecycleRouter` (state/cooldown coordinator) and `_SubprocessLifecycleManager` (subprocess operations).
- Replace private `_http_procs` access in `_ServerLifecycleRouter.start_http_subprocess()` with `self._http_mgr.verify_running(server_key)` — `HttpServerLifecycleManager` already exposes this public method.
- Standardize `_build_llm_client`, `_build_tool_executor`, `_build_history_manager` to return single typed values (introduce dataclasses for multi-value returns).
- Replace `object` type annotations in `_build_embedding_client`, `_build_retriever`, `_build_jsonl_store`, `_build_injection_service`, `_build_ingestion_service` with proper generic type parameters.
- Update `build_agent_context()` to use the standardized builders and optionally introduce a `ServiceAssembly` holder.

## Constraints
- Must preserve the `LifecycleManagerProtocol` contract — no breaking changes to the protocol interface.
- Must preserve `AppServices` constructor signature compatibility (or update both simultaneously).
- Must not change any runtime behavior — all changes are structural.
- Must maintain backward compatibility with existing tests that mock `_ServerLifecycleRouter`.

## Acceptance Criteria
- [ ] `_COOLDOWN_TIMEOUT_SEC` is removed; `_COOLDOWN_SECONDS` remains and is the only cooldown constant.
- [ ] `_ServerLifecycleRouter` no longer contains subprocess start/restart/shutdown methods — those live in `_SubprocessLifecycleManager`.
- [ ] `HttpServerLifecycleManager.verify_running(server_key: str) -> bool` replaces the private `_http_procs` access in `_ServerLifecycleRouter.start_http_subprocess()`.
- [ ] All `_build_*` functions return single typed values (no tuple returns).
- [ ] Memory builder functions use proper generic type parameters instead of `object`.
- [ ] Existing tests pass after refactor (behavior lock requirement).
- [ ] Type checker passes on the module.

## Testing Expectations
- Run existing test suite for `scripts/agent/` to confirm behavior lock.
- Verify type checking passes (`uv run mypy scripts/agent/factory.py`).
- Verify `LifecycleManagerProtocol` conformance for both `_ServerLifecycleRouter` and `_SubprocessLifecycleManager`.
- Manual verification: ensure agent startup still initializes all services correctly.

## Documentation Impact
Update module docstring in `factory.py` to reflect the new two-class architecture for lifecycle management. Update `lifecycle_protocol.py` docstring to note both implementations.

## Out of Scope
- Refactoring `HttpServerLifecycleManager` itself (already well-separated per its own docstring).
- Changing `AgentContext` or `AppServices` structure beyond what is necessary for builder standardization.
- Adding new features or changing service initialization order.
- Refactoring memory layer builders beyond type annotation fixes.

## Dependencies
N/A: none

## Unresolved Questions
- Should `_SubprocessLifecycleManager` also implement `LifecycleManagerProtocol`, or should `_ServerLifecycleRouter` remain the sole protocol implementer delegating to it?
- What is the preferred naming convention for the dataclass holding multi-value builder results (e.g., `LlmClientResult`, `ToolExecutorResult`)?
- Does `AppServices` need a new field for `RuntimeToolRegistry` that appears in its constructor but is not wired by `build_agent_context()`?

## AI Implementation Instruction
When implementing this issue:
- Do not rewrite unrelated files in `scripts/agent/`.
- Preserve the exact public behavior of every method — verify with existing tests.
- After splitting `_ServerLifecycleRouter`, ensure both classes pass `isinstance` checks against `LifecycleManagerProtocol`.
- If any builder function's tuple return is consumed elsewhere in the codebase, update those callers simultaneously.
- Stop and report open questions from the Unresolved Questions section before proceeding.
- Do not add new dependencies or change import structure beyond what is necessary.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-135039
- **Adversarial validated at**: 20260920-135039
- **Related target files**: scripts/agent/factory.py, scripts/agent/lifecycle_protocol.py, scripts/agent/http_lifecycle.py, scripts/agent/context.py
