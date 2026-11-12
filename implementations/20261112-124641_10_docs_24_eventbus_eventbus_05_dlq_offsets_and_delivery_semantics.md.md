## Goal
Add the `events.jsonl` line-count note to the Cleanup Procedure of `eventbus_05` (`REQ-003` / `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan; locate each passage by its quoted text, and skip and report it if it is already correct (Phase 1 rule).
- The Cleanup Procedure deletes from `events` in SQLite only; `events.jsonl` (secondary store) is not pruned, and the retention paragraph says the file grows until the operator rotates it (checked).
- Overlap: adrrev014 (row 07 of its procedures) and `plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md` edit other passages of this file; edit this paragraph after them.
- Execute after the adrrev017 procedures (this Plan `Depends on` them) so each passage is edited once on cleaned text.

## Design decisions
- One bullet in the effects list of the Cleanup Procedure.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. Add a bullet: manual deletion does not touch `{storage_dir}/events.jsonl`, so after a cleanup the archive has more lines than `events` has rows; the archive is not a source for counts.

### Method
- Place it after the `consumer_offsets` bullet; keep the SQL block unchanged.

### Details
- Do not describe a rotation tool that does not exist.

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
- The Cleanup Procedure states the `events.jsonl` line-count effect.

## Out of Scope
- JSONL retention policy.

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
- **Requirement ID**: `REQ-003` — manual deletion leaves `events.jsonl` longer than the database
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
