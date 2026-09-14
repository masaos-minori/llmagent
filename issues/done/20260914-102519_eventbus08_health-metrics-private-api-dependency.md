# Harden health metrics and remove private metrics API dependencies

## Priority
Medium

## Summary
The EventBus health endpoint currently depends on accessing another module's underscore-prefixed (private) metrics internals; this issue exposes the needed measurements through a supported interface and ensures a metrics-read failure degrades the health response rather than failing the whole endpoint.

## Background
N/A: covered by Summary — this is a direct code-level finding in the health endpoint's metrics dependency, not derived from a prior design decision document.

## Problem
The health endpoint (`scripts/eventbus/health_route.py`, via `route_helpers.py`) reads measurements by accessing another module's underscored/private internals rather than a supported public interface, and a metrics-read failure is not confirmed to degrade gracefully rather than failing the entire health check.

## Reason for Change
The health endpoint must remain reliable when dependencies or metrics are unavailable.

## Implementation Intent
Return stable degraded responses using supported metrics interfaces rather than reaching into another module's private internals.

## Target Files or Areas
- `scripts/eventbus/health_route.py`
- `scripts/eventbus/route_helpers.py`
- `tests/eventbus/test_eventbus_health.py`

## Required Changes
- Expose required measurements through application-owned state or supported public interfaces.
- Handle metric-read failures without failing the whole health endpoint.
- Add compatibility tests for the metrics implementation used by the project.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- The health endpoint does not access underscored metrics internals.
- Metric collection failure produces a controlled degraded response or omitted metric.
- Existing response fields remain documented.

## Testing Expectations
Add or update unit, integration, and regression tests for all affected boundaries (see Acceptance Criteria), including compatibility tests for the metrics implementation. Run the relevant test suites, static analysis, and type checks.

## Documentation Impact
Update active design documents and the known-issue inventory only after implementation evidence is available.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
N/A: none — this issue is independent of the other issues in this batch, though it touches `scripts/eventbus/health_route.py` alongside `eventbus04`.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Keep changes scoped to the health endpoint's metrics access path; do not rewrite unrelated route handlers. Preserve existing documented response fields unless a fix explicitly requires a change. Confirm that failure paths do not expose credentials, tokens, payloads, or sensitive configuration.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102519
- **Related target files**: scripts/eventbus/health_route.py, scripts/eventbus/route_helpers.py, tests/eventbus/test_eventbus_health.py
