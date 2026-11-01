# Factory leaks client on build failure

## Priority
Low

## Summary
`build_agent_context()` creates the shared `httpx.AsyncClient` first, then sequentially calls several more service builders before assigning `ctx.services`. If a later builder raises, the client is never closed, and this path runs before `StartupOrchestrator.run()`'s rollback `try`, so that rollback does not cover it. The leak window is wider than the builders: `ComponentInitializer._initialize` keeps going after `build_agent_context` (command registry, workflow definition and schema checks, orchestrator initialization), and a failure in any of them also leaks `ctx.services.http`.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's session/lifecycle subsystem (`scripts/agent/factory.py`, `scripts/agent/startup.py`).

## Problem
`scripts/agent/factory.py::build_agent_context()` (a synchronous `def`) builds `http` via `_build_llm_client()` first, then calls `_build_tool_executor()`, `_build_history_manager()` and `_build_memory_services()` and constructs `RepositoryGateway(...)`, assigning `ctx.services` only at the end. `StartupOrchestrator.run()` calls `ComponentInitializer(...).initialize()` before its `try`, which begins at `_start_servers()`, so an exception from `build_agent_context()` or from the later `_initialize` steps leaves the client open. `httpx.AsyncClient.aclose()` is a coroutine and cannot be awaited inside the synchronous factory or `_initialize`.

## Reason for Change
Impact is low: a startup failure here ends the process, so the OS reclaims the socket and the only visible effect is a `ResourceWarning` at exit. It would matter if a caller ever retried startup in-process.

## Implementation Intent
Make cleanup possible from the async caller: for example have `StartupOrchestrator.run()` close `ctx.services.http` (or a partially built client) in an `except` that also covers the post-factory initialization steps, or have the factory expose the client before later builders run. Do not await inside the synchronous factory.

## Target Files or Areas
- `scripts/agent/factory.py` (`build_agent_context()`)
- `scripts/agent/startup.py` (`StartupOrchestrator.run()`, `ComponentInitializer._initialize`)

## Required Changes
- Ensure the HTTP client is closed on failure of any step after `_build_llm_client()`, including the steps in `ComponentInitializer._initialize` that follow `build_agent_context()`, using an async-capable cleanup at the caller.
- Add a test that makes a later step raise and asserts the client was closed before the exception propagates.

## Constraints
- Do not change the builder call order or `ctx.services` assignment timing beyond what the cleanup needs.
- Keep `StartupOrchestrator.run()`'s existing rollback of started servers intact; the cleanup must not run it twice.

## Acceptance Criteria
- A failure anywhere after `_build_llm_client()` and before the REPL starts results in the HTTP client being closed before the exception propagates.
- Normal (non-failing) startup is unaffected.

## Testing Expectations
Unit test injecting a failure into one of the later builders and asserting `http.aclose()` (or equivalent) was called. Run `tests/agent/test_factory.py` and `tests/agent/test_startup.py` after the change.

## Documentation Impact
N/A: no operator-facing documentation describes this internal cleanup gap today.

## Out of Scope
- Rollback of started MCP servers (existing behavior).

## Dependencies
N/A: none.

## Unresolved Questions
- Which side owns the cleanup (the orchestrator or the factory): a design choice for the owner; the factory is synchronous, so the orchestrator is the simpler place.

## AI Implementation Instruction
Add the cleanup at the async caller (or expose the client early); do not await in the synchronous factory. Add the regression test described above before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180345
- **Related target files**: scripts/agent/factory.py, scripts/agent/startup.py
