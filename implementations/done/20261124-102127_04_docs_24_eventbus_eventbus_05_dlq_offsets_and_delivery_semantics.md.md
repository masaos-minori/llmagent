## Goal
Replace the TTL, manual cleanup SQL, and JSONL retention text with the state-aware retention model, the DLQ artifact and archive lifecycle, and the replay-floor rule (REQ-003, REQ-004, REQ-005, REQ-007).

## Scope
**Release unit**: eventbus-docs

- Edits only `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`; applied with the other documents of the release unit because the EventBus documents cross-link and are validated together.

## Assumptions
- The amended ADR-006 (Decision Details 15 to 20, Replay Contract, INV-17 to INV-22) is the contract; the document links to it instead of restating numbers.
- Where current code differs, the document cites EVENTBUS-001 (code still appends `events.jsonl`) or EVENTBUS-002 (no retention, purge, capacity signal, replay floor, or HTTP 410); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search the repository for links to its anchor (`rg -n "#<anchor>" docs`); no link to a retired heading exists today (checked in Step 3a), and a new link must not point to a removed heading.

## Design decisions
- The Retention section becomes the single place that defines retention; other documents link to it.
- No manual deletion procedure is supported, so the SQL block and its pragma text are removed without a substitute statement.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. Retention > TTL Policy and Cleanup Procedure: remove the "retained until explicitly deleted" text and the manual `DELETE` SQL block with its foreign-key and orphan notes; state that no manual deletion procedure is supported and that retention is performed by a dedicated task, not yet implemented (EVENTBUS-002).
2. Add Retention Model: retention participants (persistent source of truth is an open owner decision, no purge runs until it is approved), why authorization TTL expiry, connected subscribers, offsets, and existing `consumer_delivery` rows are each insufficient, and explicit decommission.
3. Add Purge Eligibility and Blockers: never by age alone (an EventBus-generated timestamp, never the publisher-supplied `published_at`; no such column exists yet); every active participant acknowledged or decommissioned; blockers are incomplete DLQ work, `dlq_outbox` rows in `pending` or `failed` status, a legal hold, and required requeue lineage.
4. Add Purge Unit and Execution: an event and its dependent `consumer_delivery` and `dlq_outbox` rows are deleted as one transaction, dependents first; bounded batch size and per-cycle limit; scheduled, dedicated task separate from the DLQ repair loop; stops between batches at shutdown; values undefined (EVENTBUS-002).
5. Replace "JSONL Archive Retention" with DLQ Artifact and Archive Lifecycle: active DLQ files and `requeued/` files are derived and reconstructable; outbox `pending`, `done`, and `failed` retention (`pending` and `failed` never deleted automatically); orphan, mismatched, and temporary files are reported and never deleted automatically; verified database archives from `python -m eventbus.db_tools rotate` need bounded growth by generation, age, and total size, a minimum number of verified recovery generations, and protection of the latest verified candidate, with values undefined and no retention logic existing today (EVENTBUS-002).
6. `since_seq` Precedence: add HTTP 410 `replay_position_expired` (new) for a start position before `earliest_available_seq` (new), no silent offset advance, and `since_seq=0` on `/replay` meaning the earliest retained event; keep the `/subscribe` order.
7. Reliability Limits: replace the SQLite/JSONL divergence bullet with the bounded-history and expired-position statement.

### Method
- Edit section by section with the Edit tool; keep the `## Retention` heading and the `### Requeue Semantics`, `### Consumer Identity` anchors unchanged.
- Link to ADR-006 Decision Details 18 to 20 instead of restating them.

### Details
- `{deadletter_dir}/requeued/` is created by `archive_dlq_record`; archives are written by `db_tools.py rotate` through the SQLite backup API and verified before they count (checked in Step 3a).
- The file grows by roughly 3 KB; it stays far below the 32768-byte default document limit.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/check_docs_content_policy.py`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The manual SQL and JSONL retention text are gone; retention participants, predicates, blockers, purge unit, task, artifact and archive lifecycle, and the replay-floor rule are stated; every undefined value cites EVENTBUS-002.

## Out of Scope
- Any other file, code, configuration, the API manifest, and the generated block of `eventbus_08_reference_api.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-102633 | 20261124-102633 | Changed: docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md |
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
- **Requirement ID**: REQ-003 (retention), REQ-004 (replay floor), REQ-005 (DLQ lifecycle), REQ-007 (archives)
- **Source issue**: issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-101736_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-102127
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`