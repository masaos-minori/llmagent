## Goal
State that EventBus-generated timestamps are UTC with a `Z` suffix in `eventbus_06` (`REQ-003` / `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- `now_iso()` in `scripts/eventbus/json_utils.py` returns `%Y-%m-%dT%H:%M:%SZ`; `dlq.py` uses the same format; `published_at` is publisher-supplied and stored unchanged (checked). UNK-04: the maintainer confirms `Z` as the documented format.
- Overlap: adrrev017 row 11 edits the foreign-key bullet; adrrev014 edits other passages; compatible.

## Design decisions
- One bullet in the schema/column description, scoped to timestamps the EventBus generates, not to `published_at`.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. Add a bullet near the column descriptions: EventBus-generated timestamps (for example `dlq_at` and `requested_at`) are UTC strings in the form `YYYY-MM-DDTHH:MM:SSZ`; `published_at` is stored as supplied by the publisher.

### Method
- Verify each named column in `schema.sql` and its writer before naming it.

### Details
- Do not claim a validation rule that the code does not enforce.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_needs_confirmation_inventory.py` — pass.

## Completion criteria
- The timestamp format is stated once, scoped correctly.

## Out of Scope
- Changing timestamp code; Agent-side clients.

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
- **Requirement ID**: `REQ-003` — document the timestamp format
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
