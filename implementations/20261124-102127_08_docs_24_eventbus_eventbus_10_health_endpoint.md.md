## Goal
Document the retention and capacity signals, warning versus critical readiness behavior, and the separate retention health state in the health endpoint document, marked as not yet implemented (REQ-006, REQ-008).

## Scope
**Release unit**: eventbus-docs

- Edits only `docs/24_eventbus/eventbus_10_health_endpoint.md`; applied with the other documents of the release unit because the EventBus documents cross-link and are validated together.

## Assumptions
- The amended ADR-006 (Decision Details 15 to 20, Replay Contract, INV-17 to INV-22) is the contract; the document links to it instead of restating numbers.
- Where current code differs, the document cites EVENTBUS-001 (code still appends `events.jsonl`) or EVENTBUS-002 (no retention, purge, capacity signal, replay floor, or HTTP 410); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search the repository for links to its anchor (`rg -n "#<anchor>" docs`); no link to a retired heading exists today (checked in Step 3a), and a new link must not point to a removed heading.

## Design decisions
- One new section after "Possible Degraded Reasons"; existing reasons and tiers stay unchanged.
- Signals are named as in ADR-006 Decision Detail 20; response field names and thresholds are stated as undefined.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/24_eventbus/eventbus_10_health_endpoint.md`

### Procedure
1. Add "Retention and Capacity Signals": database size, WAL size, archive size, DLQ artifact size, audit-log size, and free disk; event count, purge-eligible count, retention-blocked count, oldest retained event age, purge lag, last retention run, last result, last deleted count.
2. State warning versus critical behavior: a warning is reported without making readiness false; a critical disk shortage and a retention-state inconsistency make readiness false (HTTP 503 with a degraded reason).
3. State that the retention task has its own health state, separate from the DLQ task and the authorization sweep.
4. State that none of these fields, reasons, or thresholds exists in `health_route.py` yet and that the implementation defines their names and values (EVENTBUS-002).

### Method
- Use the Edit tool; match the heading levels and table style of "Possible Degraded Reasons".

### Details
- Do not add rows to the existing degraded-reasons table, because those reasons exist in code.
- Keep the existing statement that HTTP 503 is returned for any degraded reason and explain that a warning adds no degraded reason.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The signals, warning versus critical behavior, and the retention health state are documented; the document states they are not implemented (EVENTBUS-002); the existing reasons table is unchanged.

## Out of Scope
- Any other file, code, configuration, the API manifest, and the generated block of `eventbus_08_reference_api.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | Release unit eventbus-docs |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006, REQ-008 (health and capacity)
- **Source issue**: issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-101736_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-102127
- **Related target files**: `docs/24_eventbus/eventbus_10_health_endpoint.md`
