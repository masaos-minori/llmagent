# Define StateStore ownership and give it a close path

## Priority
Medium

## Summary
The workflow StateStore has no defined owner or shutdown path: the orchestrator opens one at construction and nothing ever closes it, while the engine adapter can flip an ownership flag that makes a later turn close the shared store. Define who owns the store, when it closes, and remove the latent use-after-close path.

## Background
Code review evidence (Verified for the code facts; the failure trigger is Speculative):
- The orchestrator constructs a StateStore during startup and no close/shutdown path exists for it anywhere in the agent code (grep-verified: no close call for the workflow store).
- The adapter holds a shared StateStore reference plus an `_owns_state_store` flag that becomes True only when `task-init` is called directly with no injected store; the turn-execution finally then closes the store it "owns" — which is the same object the adapter was constructed with, so subsequent turns on that adapter operate on a closed store.
- Today production always injects the orchestrator's store, so the closing branch is only reachable through direct adapter use (integration-style code paths).
Related archived work: `issues/done/20260913-160555_statestore_double_close.md` (resolved double-close; the ownership question it exposed is still open) and `issues/done/20261103-134147_wfreview002_session-persister-state-store-connection-leak.md` (resolved leak in an adjacent component).

## Problem
- Every agent process (REPL, service) leaks the workflow database connection at shutdown; cleanup relies on interpreter garbage collection.
- The ownership flag encodes two conflicting models (injected-shared vs created-owned) in one object, and mixing the two calling styles closes a store other components still reference.

## Reason for Change
Resource-lifecycle correctness for a long-running production process, and removal of a time-bomb branch: any future direct adapter use (the resume-path work) activates the shared-close bug silently.

## Implementation Intent
Pick one ownership model: the component that creates the store closes it; injected stores are never closed by the receiver. Express it in construction (e.g. the adapter never closes a store it did not create, tracked from the constructor rather than from a per-call flag), and add a shutdown path that closes the orchestrator's store when the agent process stops.

## Target Files or Areas
- scripts/agent/orchestrator.py (store creation, shutdown wiring)
- scripts/agent/workflow_engine_adapter.py (ownership flag, turn finally)
- scripts/agent/workflow/state_store.py (close method surface)
- scripts/agent/lifecycle.py or the startup/shutdown coordinator (shutdown hook placement)

## Required Changes
- Decide and document the ownership rule (creator closes; injector keeps ownership).
- Make the close decision depend on construction-time ownership, not on which method was called last.
- Add an explicit close on agent shutdown for the orchestrator-owned store.

## Constraints
- Closing must be idempotent (double close must not raise).
- Do not close the shared store between turns — tool runner and diagnostics still use it.
- Keep public constructor signatures compatible; tests inject stores extensively.

## Acceptance Criteria
- A process shutdown closes the workflow store exactly once.
- Direct adapter construction (own store) closes its store; injected-store usage never closes it.
- No code path closes a store another live component references.

## Testing Expectations
- Unit test: adapter with injected store never closes it across multiple turns, including after a task-init call without a store argument.
- Unit/integration test: shutdown path closes the store (observable via a probe or closed-connection error).
- Existing orchestrator tests remain green.

## Documentation Impact
State the ownership/shutdown boundary (creator closes, injector retains) in the agent state-and-persistence documentation as a responsibility statement.

## Out of Scope
- The dead-alias cleanup and inert test patches (separate issue).
- Facade bypass patterns (separate issue).
- Connection pooling or async I/O changes.

## Dependencies
- Sequence before `issues/20261107-203215_wfaudit002_tool-state-key-collisions.md` follow-up wiring and before any production wiring of the resume path (they would otherwise hit the shared-close bug).
- Context: `issues/done/20260913-160555_statestore_double_close.md` (resolved; verify current behavior against it).

## Unresolved Questions
- Which component is the designated owner in the REPL path vs the service path (the orchestrator instance appears process-lifetime in both; confirm before wiring the shutdown hook).

## AI Implementation Instruction
Do not add close calls ad hoc in turn paths. Centralize the ownership decision at construction and shutdown. Keep close idempotent. If the shutdown coordinator is the right hook site, wire there rather than in the orchestrator constructor.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203219
- **Related target files**: scripts/agent/orchestrator.py, scripts/agent/workflow_engine_adapter.py, scripts/agent/workflow/state_store.py, scripts/agent/lifecycle.py
