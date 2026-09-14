# Harden SSE lifecycle, heartbeat, idle timeout, and broker health

## Priority
Medium

## Summary
Heartbeat, idle-timeout, disconnect handling, and broker-availability reporting for SSE subscriptions are coupled runtime-lifecycle concerns currently handled inconsistently; this issue unifies them under one configuration and failure policy so subscriptions stay observable/releasable and health reporting degrades in a controlled way.

## Background
N/A: covered by Summary — this is a direct code-level finding in the SSE subscription and health-check paths, not derived from a prior design decision document.

## Problem
When the broker is unavailable, the health endpoint risks raising an internal exception rather than returning a controlled degraded response, and there is no `sse_idle_timeout` configuration key (only `sse_heartbeat_interval` currently exists per the source review), so idle-subscription behavior and its interaction with heartbeats is undefined.

## Reason for Change
Heartbeat, idle timeout, disconnect handling, and broker availability are coupled runtime-lifecycle concerns and should use one configuration and failure policy.

## Implementation Intent
Keep subscriptions observable and releasable during idle or degraded operation, and return controlled health results rather than propagating internal exceptions.

## Target Files or Areas
- `scripts/eventbus/health_route.py`
- `tests/eventbus/test_eventbus_health.py`
- `scripts/eventbus/subscribe_route.py`
- `tests/eventbus/test_eventbus_subscribe.py`
- `scripts/eventbus/config.py`
- `config/eventbus.toml`
- `tests/eventbus/test_eventbus_config.py`

## Required Changes
- Report `broker_unavailable` as a degraded reason when the broker is unavailable.
- Read the backlog threshold from EventBus configuration or guard broker access.
- Return a controlled HTTP 503 response instead of raising an internal exception.
- Evaluate the heartbeat deadline in the timeout branch of the live-delivery loop.
- Emit heartbeat comments independently of event arrival.
- Define how heartbeat activity interacts with the idle timeout.
- Add `sse_idle_timeout` to the dataclass, known keys, type validation, and configuration loader.
- Define its default and valid range.
- Validate its relationship with `sse_heartbeat_interval`.
- Update configuration documentation and examples.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- The health endpoint returns HTTP 503 with a stable response body when broker initialization fails.
- The endpoint does not dereference a missing broker.
- Tests cover startup, shutdown, and broker-initialization failure states.
- An idle subscription receives periodic heartbeats at the configured interval.
- Heartbeat generation does not prevent client-disconnect detection.
- Tests cover multiple heartbeat intervals without published events.
- A valid `sse_idle_timeout` can be loaded from TOML.
- Unknown or invalid values fail during startup.
- Configuration tests cover defaults and cross-field validation.

## Testing Expectations
Add or update unit, integration, and regression tests for all affected boundaries (see Acceptance Criteria). Run the relevant test suites, static analysis, and type checks.

## Documentation Impact
Update active design documents (configuration reference and examples for `sse_idle_timeout`) and the known-issue inventory only after implementation evidence is available.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
N/A: none — this issue is independent of the other issues in this batch.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Keep changes scoped to SSE lifecycle/heartbeat/idle-timeout and broker-health reporting; do not rewrite unrelated route handlers. Preserve existing public request/response shapes unless a fix explicitly requires a change. Confirm that failure paths do not expose credentials, tokens, payloads, or sensitive configuration. Stop and report if `sse_heartbeat_interval`'s existing default/range convention is unclear rather than inventing a new one for `sse_idle_timeout`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102344
- **Related target files**: scripts/eventbus/health_route.py, tests/eventbus/test_eventbus_health.py, scripts/eventbus/subscribe_route.py, tests/eventbus/test_eventbus_subscribe.py, scripts/eventbus/config.py, config/eventbus.toml, tests/eventbus/test_eventbus_config.py
