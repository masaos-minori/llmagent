# Stop bypassing the StateStore facade with raw-connection call-outs

## Priority
Low

## Summary
The engine and the orchestrator obtain the store's raw database connection and pass it back into the store's own operation functions, bypassing the facade the store module documents. Route these calls through facade methods so the persistence boundary stays auditable.

## Background
Code review evidence (Verified):
- The StateStore module documents itself as the facade whose public methods take an explicit database argument so callers own transaction boundaries.
- The engine calls the store's connection getter and passes the result into the store-level idempotency function (stage-start guard) and the artifact recorder, instead of calling facade methods.
- The orchestrator does the same for the recovery entry: it passes the store's own connection back into the store's recovery method.
- Precedent for boundary review in this area: `plans/done/20261105-085959_wfreview004_workflow-adapter-and-engine-private-attribute-access.md` (resolved; private-attribute access cleanup — the connection getter pattern is the persistence-side remainder of the same boundary story).

## Problem
The connection getter is a facade escape hatch: today it happens to be used against the same store, but the pattern permits any caller to extract the connection and drive the tables behind the facade's back, making ownership and transaction-boundary review depend on reading call sites instead of the facade surface.

## Reason for Change
Small architectural tightening in a domain that keeps growing consumers (engine, tool runner, diagnostics). Cheapest to fix while there are only a handful of call-outs; every new consumer copied the pattern would make the facade nominal.

## Implementation Intent
Add or reuse facade methods for the three bypassed operations (stage-start guard, artifact recording, stale-attempt recovery) so callers pass business arguments, not connections. Keep the explicit-database-argument design for transaction ownership: the facade method may still accept a caller-provided connection for transaction grouping — the point is that the store's own functions are reached through the store's documented surface.

## Target Files or Areas
- scripts/agent/workflow/state_store.py (facade methods)
- scripts/agent/workflow/workflow_engine.py (call sites)
- scripts/agent/orchestrator.py (recovery call site)
- scripts/agent/workflow_engine_adapter.py (stage-definition build path, if it participates)

## Required Changes
- Give the store facade entry points for the guard, the artifact write, and the recovery sweep.
- Replace the three raw-connection call-outs.
- Review whether the connection getter can be narrowed to internal/test-only use after the replacement.

## Constraints
- Transaction grouping semantics must not change: multi-statement operations that currently share one caller-owned transaction must keep sharing one.
- Tests legitimately use the raw connection for fixture setup; only production call-outs are in scope.
- No signature churn beyond what the replacement requires.

## Acceptance Criteria
- No production call site obtains a connection from the store to call the store's own ops functions.
- Facade methods exist for the three operations and are covered by existing tests (retargeted, not duplicated).
- The facade docstring matches the enforced usage.

## Testing Expectations
- Retarget existing engine/orchestrator tests to the facade methods; suites green.
- Grep-based verification of zero production connection-getter call-outs (excluding tests) recorded in the PR text.

## Documentation Impact
If the state-and-persistence doc describes the facade contract, confirm the wording matches the enforced surface. No new doc pages.

## Out of Scope
- Removing the connection getter if tests need it (decision noted in Dependencies).
- Async or connection-pooling redesigns.
- The ownership/close issues for the same class.

## Dependencies
- Coordinate with `issues/20261107-203219_wfaudit006_state-store-lifecycle-ownership.md` (same class, adjacent code; avoid conflicting refactors in the same file pair).
- Context: `plans/done/20261105-085959_wfreview004_workflow-adapter-and-engine-private-attribute-access.md` (resolved precedent).

## Unresolved Questions
- Should the connection getter be marked internal (leading-underscore rename) or kept public for test use? (Needs confirmation with the owner.)

## AI Implementation Instruction
Preserve transaction boundaries exactly as they behave today; this is a call-path change, not a semantics change. Do not add convenience wrappers that hide caller-owned transactions from tests.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203228
- **Related target files**: scripts/agent/workflow/state_store.py, scripts/agent/workflow/workflow_engine.py, scripts/agent/orchestrator.py, scripts/agent/workflow_engine_adapter.py
