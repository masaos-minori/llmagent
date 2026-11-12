## Goal
Remove the former per-domain `migrate` policy note, the `formerly (mis)labeled rpo_window_seconds` sentence, and the rename blockquote from `db_07` (`REQ-004` / `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- Passages: the `policy` row (`... the former per-domain migrate policy and its ledger fields were removed by the compatrm001 plan`), the `backup_duration_seconds` row (`The field formerly (mis)labeled rpo_window_seconds.`), and the blockquote starting `The drill artifact field rpo_window_seconds was renamed to`.
- The blockquote also states that `rpo_seconds` and `rto_seconds` are distinct measurements derived from recorded event timestamps; keep that as a plain current-tense sentence if the table rows do not already say it.
- Overlap: adrrev019 edits another passage of `db_07` (a stale count or timestamp statement) and adrrev014 edited it earlier; compatible.

## Design decisions
- Table rows keep their definitions without history; the blockquote is removed or reduced to the current measurement definition.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. `policy` row: `recreate for every domain: the drill records the current-schema-only recovery policy.`
2. `backup_duration_seconds` row: delete the `formerly (mis)labeled` sentence.
3. Remove the rename blockquote; keep the `rpo_seconds`/`rto_seconds` definition if it exists nowhere else.

### Method
- `rg -n 'formerly|renamed|former |compatrm001' docs/41_db/db_07_*.md` before and after.

### Details
- Check the field list against `db/recovery.py` through `check_docs_consistency.py --domain db`.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` — pass (UNK-05).

## Completion criteria
- No `former`, `renamed`, or plan ID wording remains in the edited passages; field definitions are intact.

## Out of Scope
- Recovery behavior; the table additions of other Plans.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-175944 | 20261112-175944 | docs/41_db/db_07_api_and_operations-recovery-and-reference.md (rpo/rto definitions already in table rows; blockquote removed) |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-175944 | 20261112-175944 | checkers and check_docs_consistency --domain db pass |

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
- **Requirement ID**: `REQ-004` — remove former-policy and rename notes
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
