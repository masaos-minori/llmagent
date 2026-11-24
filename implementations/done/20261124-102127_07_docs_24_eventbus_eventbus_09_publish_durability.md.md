## Goal
Remove the JSONL append step, failure scenarios, counter, and repair statements from the publish durability document while keeping SQLite-commit success and best-effort broker notification (REQ-002).

## Scope
**Release unit**: eventbus-docs

- Edits only `docs/24_eventbus/eventbus_09_publish_durability.md`; applied with the other documents of the release unit because the EventBus documents cross-link and are validated together.

## Assumptions
- The amended ADR-006 (Decision Details 15 to 20, Replay Contract, INV-17 to INV-22) is the contract; the document links to it instead of restating numbers.
- Where current code differs, the document cites EVENTBUS-001 (code still appends `events.jsonl`) or EVENTBUS-002 (no retention, purge, capacity signal, replay floor, or HTTP 410); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search the repository for links to its anchor (`rg -n "#<anchor>" docs`); no link to a retired heading exists today (checked in Step 3a), and a new link must not point to a removed heading.

## Design decisions
- Keep the existing headings except the JSONL Append Failure subsection, which is removed; the disk and permission scenarios are rewritten around the SQLite commit.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/24_eventbus/eventbus_09_publish_durability.md`

### Procedure
1. Canonical Store: state `eventbus.sqlite` is the only system of record, no event replica exists, audit logs are separate, and DLQ files are derived; update the Authority model sentence and the Rationale list (remove the JSONL item).
2. Publish Success Criterion: remove the JSONL append step and renumber the flow; the commit is the only step that decides success; broker notification is best-effort.
3. Failure Scenarios: delete "JSONL Append Failure"; reword "Both Failures Simultaneously" around broker-notification failure only or fold it into the Broker Notification Failure subsection; rewrite "Disk-Full Scenario" and "Permission Failure Scenario" so a failed SQLite commit returns a non-success response and a failure after the commit affects only side effects; critical disk shortage is a retention and health signal (EVENTBUS-002).
4. Recovery Procedure: remove the JSONL backfill statements; recovery of event data reads from SQLite, and no replica exists.
5. Metrics: drop `eventbus_jsonl_append_failure_total` from the list; cite EVENTBUS-001 once for the code difference.
6. Keywords: remove `jsonl`.

### Method
- Use the Edit tool; check with `rg -n -i jsonl docs/24_eventbus/eventbus_09_publish_durability.md` that only the EVENTBUS-001 citation remains.

### Details
- Keep the Requeue Delivery Semantics section unchanged, including its existing owner-decision reference.
- The broker counters and `eventbus_dlq_file_write_failure_total` statements stay.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run pytest tests/eventbus/test_eventbus_publish_contract.py -q`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- No JSONL append step, scenario, counter, or repair statement remains except the one EVENTBUS-001 citation; the document states that a successful SQLite commit is publish success.

## Out of Scope
- Any other file, code, configuration, the API manifest, and the generated block of `eventbus_08_reference_api.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-102712 | 20261124-102712 | Changed: docs/24_eventbus/eventbus_09_publish_durability.md |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261124-102753 | 20261124-102753 | Release unit eventbus-docs eventbus consistency, docs structure/quality/content-policy, known-deviation sync, needs-confirmation inventory, reference drift checks and 77 tests pass; preservation findings are intended |

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
- **Requirement ID**: REQ-002 (publish durability)
- **Source issue**: issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-101736_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-102127
- **Related target files**: `docs/24_eventbus/eventbus_09_publish_durability.md`