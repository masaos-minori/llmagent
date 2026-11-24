## Goal
Remove the JSONL replica, its append guard, and the SQLite/JSONL count comparison from the persistence document, and add the replay-floor and retention-timestamp statements (REQ-002, REQ-004).

## Scope
**Release unit**: eventbus-docs

- Edits only `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`; applied with the other documents of the release unit because the EventBus documents cross-link and are validated together.

## Assumptions
- The amended ADR-006 (Decision Details 15 to 20, Replay Contract, INV-17 to INV-22) is the contract; the document links to it instead of restating numbers.
- Where current code differs, the document cites EVENTBUS-001 (code still appends `events.jsonl`) or EVENTBUS-002 (no retention, purge, capacity signal, replay floor, or HTTP 410); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search the repository for links to its anchor (`rg -n "#<anchor>" docs`); no link to a retired heading exists today (checked in Step 3a), and a new link must not point to a removed heading.

## Design decisions
- Rename the consistency procedure heading to a SQLite-only title and keep its steps; Step 2 keeps the gap-is-not-loss rule.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. Front matter: remove the `jsonl-archive` and `jsonl archive` keywords.
2. Replace the "JSONL Archive" section with a short "No Event Replica" section: `eventbus.sqlite` is the only system of record; no `events.jsonl` is created (ADR-006 INV-18; code still appends one, EVENTBUS-001); audit logs are separate; DLQ files are derived.
3. Idempotency Contract: delete the "JSONL append guard" bullet.
4. Rename "SQLite/JSONL Consistency Check and Recovery Procedure" to "SQLite Consistency Check and Recovery Procedure"; in Step 2 remove the JSONL row-count comparison and the two following sentences, keeping the gap-is-not-loss statement.
5. Timestamps bullet and `published_at` ownership: add that retention decisions use an EventBus-generated timestamp, never `published_at`, and that no such column exists yet (EVENTBUS-002).
6. Replay Behavior: add that positions before `earliest_available_seq` (new) fail with HTTP 410 `replay_position_expired` (new) (EVENTBUS-002).

### Method
- Use the Edit tool on exact lines; confirm with `rg -n -i jsonl docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` that only the EVENTBUS-001 citation remains.

### Details
- The Keywords list is at the end of the file; edit it together with the front matter.
- Do not touch the Recreate procedure or the per-consumer sections.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/check_docs_structure.py`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- No JSONL replica, guard, count comparison, or keyword remains except the one EVENTBUS-001 citation; the replay-floor and timestamp statements are present.

## Out of Scope
- Any other file, code, configuration, the API manifest, and the generated block of `eventbus_08_reference_api.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-102645 | 20261124-102645 | Changed: docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md |
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
- **Requirement ID**: REQ-002 (JSONL removal, timestamp), REQ-004 (replay floor)
- **Source issue**: issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-101736_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-102127
- **Related target files**: `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`