## Goal
Rewrite `the duplicate table-level FOREIGN KEY was removed at version 6` as a current schema fact (`REQ-004` / `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- Overlap: adrrev019 edits another passage of this document (compatible).
- Verify against `scripts/eventbus/schema.sql` that `dlq_outbox` has the single inline `PRIMARY KEY REFERENCES events(event_id)` and no table-level foreign key.

## Design decisions
- Keep the testable fact: `PRAGMA foreign_key_list(dlq_outbox)` returns exactly one entry.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. Rewrite the bullet to `dlq_outbox carries a single inline PRIMARY KEY REFERENCES events(event_id) and no table-level FOREIGN KEY, so PRAGMA foreign_key_list(dlq_outbox) returns exactly one entry.`

### Method
- Remove `the duplicate ... was removed at version 6`.

### Details
- No version history remains in the bullet.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` — pass (UNK-05).

## Completion criteria
- The bullet states the current schema only.

## Out of Scope
- Schema changes; other EventBus documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — state the `dlq_outbox` foreign key as a current fact
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
