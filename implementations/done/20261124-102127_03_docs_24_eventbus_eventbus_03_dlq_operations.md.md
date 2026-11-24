## Goal
Remove JSONL failure handling from the publish and failure-summary text, add the HTTP 410 resume rule to the subscribe contract, and state the derived-artifact lifecycle and recorded outcomes in DLQ reconciliation (REQ-002, REQ-004, REQ-005).

## Scope
**Release unit**: eventbus-docs

- Edits only `docs/24_eventbus/eventbus_03_dlq_operations.md`; applied with the other documents of the release unit because the EventBus documents cross-link and are validated together.

## Assumptions
- The amended ADR-006 (Decision Details 15 to 20, Replay Contract, INV-17 to INV-22) is the contract; the document links to it instead of restating numbers.
- Where current code differs, the document cites EVENTBUS-001 (code still appends `events.jsonl`) or EVENTBUS-002 (no retention, purge, capacity signal, replay floor, or HTTP 410); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search the repository for links to its anchor (`rg -n "#<anchor>" docs`); no link to a retired heading exists today (checked in Step 3a), and a new link must not point to a removed heading.

## Design decisions
- Replace text in place; keep every existing heading so inbound anchors stay valid.
- One short "Retention floor" rule in the subscribe section; the detail lives in `eventbus_05`.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/24_eventbus/eventbus_03_dlq_operations.md`

### Procedure
1. POST /publish: replace the "JSONL Append Failure" paragraph with a "Post-commit side effects" paragraph: a successful SQLite commit is publish success; broker notification is best-effort and cannot roll back a committed event; the EventBus creates no `events.jsonl` (ADR-006 INV-18), and current code still appends one (EVENTBUS-001).
2. GET /subscribe and the `since_seq`/Offset Precedence Rules: add that a resume position before `earliest_available_seq` (new) fails with HTTP 410 `replay_position_expired` (new) and no offset is advanced; mark it not yet implemented (EVENTBUS-002). Keep the existing precedence order.
3. DLQ Reconciliation: state that DLQ JSON files are derived and reconstructable, that `events.dlq_at` and `dlq_outbox` are authoritative, that `pending` and `failed` outbox rows are never deleted automatically, that reconciliation counts (`orphans`, `mismatch`, `interrupted_tmp`) and `*.corrupt` quarantine are the recorded outcomes, and that no derived artifact is deleted automatically.
4. Failure Behavior Summary: replace the "JSONL append failure" row with a broker-notification row (200 returned, failure logged, event remains in SQLite) unless one already exists, and add a row for a resume position before the retention floor (410, offset unchanged; EVENTBUS-002).

### Method
- Locate each place with `rg -n -i "jsonl|since_seq|Failure Behavior Summary" docs/24_eventbus/eventbus_03_dlq_operations.md`; use the Edit tool on the exact paragraph or table row.

### Details
- Do not change the Orphan, Missing, Temp, Mismatch, or Corrupt subsections' behavior statements; only add the lifecycle and outcome sentences.
- A requeued artifact moves to `{deadletter_dir}/requeued/` through `archive_dlq_record`; state that these files are derived too and are not deleted automatically.

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
- No JSONL append, failure row, or `events.jsonl` replica statement remains; the HTTP 410 resume rule and the DLQ artifact lifecycle are stated; each unimplemented behavior cites EVENTBUS-002.

## Out of Scope
- Any other file, code, configuration, the API manifest, and the generated block of `eventbus_08_reference_api.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-102610 | 20261124-102610 | Changed: docs/24_eventbus/eventbus_03_dlq_operations.md |
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
- **Requirement ID**: REQ-002 (JSONL removal), REQ-004 (resume 410), REQ-005 (DLQ artifacts)
- **Source issue**: issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-101736_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-102127
- **Related target files**: `docs/24_eventbus/eventbus_03_dlq_operations.md`