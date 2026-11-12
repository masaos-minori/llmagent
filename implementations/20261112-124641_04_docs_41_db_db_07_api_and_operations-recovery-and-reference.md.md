## Goal
Add the `dlq_outbox` query to the section 11a EventBus inventory and say four tables (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- `scripts/eventbus/schema.sql` defines `events`, `consumer_delivery`, `consumer_offsets`, and `dlq_outbox`; the block queries the first three and the lead-in says `its three tables` (checked).
- Overlap: adrrev017 row 10 removes history notes elsewhere in this file; compatible.

## Design decisions
- Extend the existing bash block by one statement in the same form.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Change the comment `column names of its three tables` to `four tables`.
2. Add `SELECT group_concat(name) FROM pragma_table_info('dlq_outbox');`.

### Method
- Keep the read-only `mode=ro` connection form and the statement style of the neighbours.

### Details
- Verify the table names against `schema.sql` before writing.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_needs_confirmation_inventory.py` — pass.

## Completion criteria
- The inventory block queries four tables and says four.

## Out of Scope
- Other 11a text.

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
- **Requirement ID**: `REQ-001` — EventBus inventory lists four tables
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
