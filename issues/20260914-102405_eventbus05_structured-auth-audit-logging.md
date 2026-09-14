# Integrate structured authentication and privileged-operation auditing

## Priority
Medium

## Summary
Authentication failures, authorization failures, replay, and DLQ requeue operations currently lack one shared structured audit vocabulary and request identity, risking audit gaps or duplicate records; this issue introduces one structured, non-secret audit record per security-relevant outcome, and separately scopes `CI-005`'s cross-process applicability to EventBus specifically.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` `CI-005` ("ADR-004 INV-03 — fail-closed for missing config not implemented") is filed against the shared `scripts/shared/config_loader.py::load_config()`, so its scope may extend beyond the Shared/DB area to EventBus, Agent, RAG, and MCP processes individually — this issue's scope includes confirming whether EventBus's portion is already covered by existing tests.

## Problem
Authentication and authorization failures, and privileged actions (replay, DLQ requeue), are not consistently logged through one structured audit helper with a shared vocabulary (request ID, principal identifier, route, target), risking either missing audit coverage or duplicate records once authentication is centralized (per `eventbus02`).

## Reason for Change
Authentication failures, authorization failures, replay, and DLQ requeue require one audit vocabulary and one request identity to avoid gaps and duplicate records.

## Implementation Intent
Emit one structured, non-secret audit record for each security-relevant outcome, built on the principal introduced in `eventbus02`. Separately, review `CI-005`'s stated scope against EventBus's actual configuration-loading behavior and either confirm it as resolved for EventBus or split out the remaining EventBus-specific gap as its own tracked item.

## Target Files or Areas
- `scripts/eventbus/audit.py`
- `scripts/eventbus/auth.py`
- `scripts/eventbus/replay_route.py`
- `scripts/eventbus/dlq_route.py`
- `tests/eventbus/test_eventbus_auth.py`
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `scripts/eventbus/config.py`
- `tests/eventbus/test_eventbus_config.py`

## Required Changes
- Log authentication and authorization failures through the structured audit helper.
- Audit replay and DLQ requeue as privileged actions.
- Include request ID, principal identifier, route, and target without logging raw tokens.
- Prevent duplicate records when authentication is centralized.
- Review the scope of `CI-005` across EventBus, Agent, RAG, and MCP processes.
- Mark the EventBus portion resolved if tests confirm the current behavior.
- Split remaining process-specific gaps into separate issues.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- HTTP 401 and 403 outcomes produce structured audit records.
- Replay and DLQ requeue produce privileged-action records.
- Raw credentials never appear in logs.
- Audit tests validate required fields and outcomes.
- `CI-005` names the exact processes and missing safeguards still in scope.
- EventBus claims are backed by configuration tests.
- Resolved statements are removed from the active issue inventory according to documentation policy.

## Testing Expectations
Add or update unit, integration, and regression tests for all affected boundaries (see Acceptance Criteria). Run the relevant test suites, static analysis, and type checks.

## Documentation Impact
Update `docs/00_governance_03_issue-and-uncertainty-management.md`'s `CI-005` entry (and remove it from the active inventory if EventBus's portion is confirmed resolved by tests, per that document's own removal rule) only after implementation evidence is available — do not update ahead of the code/test change.

## Out of Scope
- Unrelated refactoring outside the identified behavioral boundary.

## Dependencies
Builds on `eventbus02`'s principal model for the audit record's principal identifier field; `eventbus10` (ADR/known-issue reconciliation) may reference this issue's `CI-005` scoping outcome.

## Unresolved Questions
Whether EventBus's current configuration loading already satisfies `CI-005`'s fail-closed requirement, or whether it needs a code change — resolve during this issue's own review step (Required Changes), not before filing it. Non-blocking.

## AI Implementation Instruction
Keep changes scoped to audit logging (`scripts/eventbus/audit.py`) and the `CI-005` scoping review; do not implement `eventbus02`'s principal model here if it is not yet done — coordinate ordering with that issue instead. Confirm that failure paths do not expose credentials, tokens, payloads, or sensitive configuration. Only remove or edit `CI-005`'s governance entry after the EventBus-specific behavior has been verified by a passing test, per that document's own Known Issues removal rule — do not mark it resolved based on code inspection alone.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-102405
- **Related target files**: scripts/eventbus/audit.py, scripts/eventbus/auth.py, scripts/eventbus/replay_route.py, scripts/eventbus/dlq_route.py, tests/eventbus/test_eventbus_auth.py, docs/00_governance_03_issue-and-uncertainty-management.md, scripts/eventbus/config.py, tests/eventbus/test_eventbus_config.py
