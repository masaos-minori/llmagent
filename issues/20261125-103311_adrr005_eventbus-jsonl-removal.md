# Remove the EventBus events.jsonl append and its failure metric

## Priority
Medium

## Summary
Make `eventbus.sqlite` the only EventBus event store by removing the `events.jsonl` append after the SQLite commit and its failure metric, as ADR-006 INV-18 requires.

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issue 009):
- Confirmed: `scripts/eventbus/publish_route.py` appends to `events.jsonl` after the commit (`:84-97`) and keeps `eventbus_jsonl_append_failure_total` (`:26`); three test files still reference the file (`tests/eventbus/test_eventbus_phase1.py`, `test_eventbus_publish_contract.py`, `test_eventbus_publish.py`).
- The approval exists: ADR-006's Approval Record covers Decision Details 15 to 17 and INV-17, INV-18, INV-21 (previously `AAL-040`). Known Issue `EVENTBUS-001` (Medium, open) tracks the mismatch and asks for this implementation issue.
- Not found: any other EventBus recovery or rebuild path that treats the JSONL as authoritative; the other JSONL references under `scripts/` belong to the Agent memory model (issues/20261125-103316_adrr010_agent-memory-schema.md).

## Problem
The publish route writes an incomplete replica that can be mistaken for a backup or recovery source and that ADR-006 forbids.

## Reason for Change
The ADR-approved design and the implementation disagree; the replica has no consumer.

## Implementation Intent
Remove the append and the metric without touching the security audit log, which stays non-authoritative; close the Known Issue only with runtime and repository-scan evidence.

## Target Files or Areas
- `scripts/eventbus/publish_route.py`
- `tests/eventbus/test_eventbus_phase1.py`, `tests/eventbus/test_eventbus_publish_contract.py`, `tests/eventbus/test_eventbus_publish.py`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

## Required Changes
- Delete the JSONL append and `eventbus_jsonl_append_failure_total`; update the tests that expect the file.
- Add a publish integration test that no `events.jsonl` is created and a repository scan test for EventBus replica or rebuild dependencies.
- Record the evidence for ADR-006 INV-18 and remove `EVENTBUS-001` after the evidence passes.

## Constraints
- Keep security audit logging unchanged and explicitly non-authoritative.
- Do not edit ADR decisions or approval records.

## Acceptance Criteria
- A publish commits only to SQLite and creates no `events.jsonl`.
- The repository scan finds no EventBus replica or rebuild dependency; audit-log regression tests pass.
- The `EVENTBUS-001` closure cites passing evidence.

## Testing Expectations
Publish integration test, repository scan test, existing audit-log regression tests, the ADR checkers, and the whole suite.

## Documentation Impact
Known Issue removal and the ADR-006 INV-18 evidence; no new decision text.

## Out of Scope
- Retention and replay (issues/20261125-103310_adrr004_eventbus-retention-replay.md).

## Dependencies
- Coordinate with issues/20261125-103310_adrr004_eventbus-retention-replay.md where both edit the EventBus governance evidence.

## Unresolved Questions
- `不明`: whether any operational script outside `scripts/` reads `events.jsonl` (`deploy/` and `tools/` showed none).

## AI Implementation Instruction
Remove only the JSONL path and its metric; keep audit logs; do not close the Known Issue without passing evidence.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103311
- **Related target files**: `scripts/eventbus/publish_route.py`, `tests/eventbus/test_eventbus_publish.py`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
