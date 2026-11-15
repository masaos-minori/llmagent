# Ctrl-C and SIGTERM are ignored during the validation and prompt stages of startup

## Priority
Medium

## Summary
`AgentREPL.run` installs a handler that turns SIGINT and SIGTERM into a shutdown event, replacing Python's default `KeyboardInterrupt`. During startup only `McpServerStarter` looks at that event. The component initialization, the service and posture probes, tool discovery, the RAG consistency check and the prompt setup never look at it, so a signal sent during those stages is recorded and then ignored until startup finishes or fails by itself. Make every startup stage honor the shutdown request.

## Background
- Found by an adversarial review of the agent startup path (`scripts/agent`) at commit `490fccc50`.
- Evidence (Explicit in code): `SignalHandler.register` calls `loop.add_signal_handler` for SIGTERM and SIGINT with a handler that sets `ctx.conv.shutdown_requested` and the shared event; it is registered before `StartupOrchestrator.run`.
- Evidence (Explicit in code): `StartupOrchestrator.__init__` passes `shutdown_event` only to `McpServerStarter`; `StartupValidationPipeline`, `ReadinessReporter`, `PromptSetup` and `ComponentInitializer` are built without it. `check_readiness`, `collect_server_postures` and `McpToolDiscoveryService.discover_all` take only the context.
- Evidence (Explicit in code): the RAG consistency step waits up to a fixed bound and the probes use per-request timeouts, executed in sequence per server.
- The user-facing input loop does honor `shutdown_requested` once it runs (`repl_input_loop`). The gap is the window before it starts.
- History, not overlapping: `issues/done/20261021-093421_repl001_sigint-sigterm-never-reach-repl-input-loop.md` connected the event to the input loop; it did not cover the startup stages.

## Problem
While one of the unguarded stages is running, Ctrl-C has no visible effect and the default interrupt is no longer available, so an operator facing a hung or slow dependency (an unreachable server, a slow consistency check) cannot stop the process short of SIGKILL. After startup completes, the already-set event ends the session, but only after the full wait and the banner.

## Reason for Change
Slow or hung dependencies are exactly the situation in which an operator reaches for Ctrl-C. The behavior is an operational hazard rather than a correctness bug, so it is Medium, not High.

## Implementation Intent
Give the startup stages one shared shutdown check, in the same way `McpServerStarter` already races its waits against the event. At the stage boundaries `StartupOrchestrator.run` should stop and raise `StartupInterrupted`, and the long awaits (probes, discovery, the executor-backed check) should be raced against the event so they can be abandoned. Rollback of spawned servers on an interrupted startup is already implemented and must keep working.

## Target Files or Areas
- scripts/agent/startup.py (`StartupOrchestrator.run`)
- scripts/agent/startup_validation.py (`StartupValidationPipeline.check_services`)
- scripts/agent/startup_prompt_setup.py (`PromptSetup.setup_prompt`)
- scripts/agent/startup_component_init.py (`ComponentInitializer.initialize`)
- tests/agent/test_startup.py, tests/agent/test_startup_rollback.py, tests/agent/test_repl.py

## Required Changes
- Pass the shutdown event to the validation pipeline and the prompt setup.
- Check the event between startup stages, and raise `StartupInterrupted` when it is set.
- Race the long awaits in `check_services` (readiness and posture probes, discovery, the RAG consistency wait) against the event.
- Add tests that set the event during each stage and assert prompt exit, rollback of started servers and no traceback.

## Constraints
- `StartupInterrupted` MUST keep its current handling in `AgentREPL.run` and `main`.
- No stage may be skipped on a normal run; the check changes behavior only when the event is set.
- Do not weaken the fail-closed outcome of any validation stage.

## Acceptance Criteria
- Setting the shutdown event during the readiness probes, tool discovery, the consistency check or the prompt setup ends startup with `StartupInterrupted` within a small bound, after the servers started so far are stopped.
- Without the event, the startup sequence and its outcomes are unchanged.
- `uv run pytest tests/agent/test_startup.py tests/agent/test_startup_rollback.py tests/agent/test_repl.py tests/agent/shared/test_startup_validation_pipeline.py` passes with the new cases.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass.

## Testing Expectations
Unit tests per stage using fakes that block until cancelled and an event set after a short delay. One test through `StartupOrchestrator.run` asserting rollback. No test depends on real signals.

## Documentation Impact
Update the agent startup and shutdown design document: state that every startup stage observes the shutdown request, and what is rolled back. Describe behavior only, with no timeouts or values.

## Out of Scope
- Changing signal registration or the Windows fallback.
- The input loop's handling after startup.
- Changing the executor-thread behavior of the RAG check (see the dependency).

## Dependencies
- `issues/20261115-214906_startrev006_rag-check-timeout-executor.md` — related: abandoning the consistency wait on shutdown has the same executor limitation described there; coordinate the two.

## Unresolved Questions
- Which stages are acceptable to leave uninterruptible if they are short and local (for example the workflow definition preflight)? (Assumption: only synchronous, bounded local steps.)

## AI Implementation Instruction
Keep changes minimal and confined to the listed files. Reuse the existing event-race pattern; do not add a second mechanism. Do not change signal registration.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-214904
- **Related target files**: scripts/agent/startup.py, scripts/agent/startup_validation.py, scripts/agent/startup_prompt_setup.py, scripts/agent/startup_component_init.py, tests/agent/test_startup.py, tests/agent/test_startup_rollback.py, tests/agent/test_repl.py
