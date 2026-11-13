## Goal
Update ADR-006's INV-08 verification row (cited test name and wording) and the `events` column list, keeping the INV-08 invariant text itself unchanged (REQ-006 / AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation and have drifted (the INV-08 row is at line 250 and the column list at line 350 in the current file); locate each passage by its quoted text and skip and report it if it is already correct.
- Run this document after row 16 (`20261113-173721_16_tests_eventbus_test_eventbus_dlq_promotion.py.md`) because it must cite the renamed test `test_dlq_requeue_records_lineage_not_consumer_delivery_failure_count` (row 16 fixes the new name).
- Overlaps already judged in the Plan Assumptions: adrrev015 (archived: `implementations/done/20261112-123307_04_...`), adrrev016, and adrrev014 all edited other regions of this ADR — their edits are already in the current text; re-read the table before editing and touch only the INV-08 row and the column list.
- INV-08 ("state, count, and history of ... Requeue are persisted") stays as written: the Requeue count and history remain persisted through the `redelivered_from` descendant lineage (Plan REQ-006); a maintainer rewrite of INV-08 itself is UNK-03 — if requested, a pending approval record per `governance_05` is added by the maintainer, not by this procedure.

## Design decisions
- Verification-row wording is adjusted to describe lineage persistence; the Invariants list text and the INV-08 number are untouched, so `ADR-006 INV-08` citations elsewhere stay valid (no renumbering).

## Alternatives considered
- Replace the cited test with the untouched `test_nack_increments_consumer_delivery_failure_count` row only: rejected — the Plan keeps the requeue test (renamed) cited because it still proves Requeue persistence without the removed column.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Automated Tests table, INV-08 row (line 250 region): replace the cited `...::test_dlq_requeue_increments_dlq_requeue_count_not_consumer_delivery_failure_count` with `...::test_dlq_requeue_records_lineage_not_consumer_delivery_failure_count`; change the row's decision-text cell from "NACK counters and requeue counters are persisted per Event" to "NACK counters are persisted per Event; Requeue history is persisted as the `redelivered_from` descendant lineage". Keep the `test_nack_increments_consumer_delivery_failure_count` citation.
2. Implementation notes, `events` table bullet (line 350 region): remove `dlq_requeue_count` and `consumer_id` from the column list; keep the parenthetical "(no event-level `acked_at` column; ACK state is per-consumer in `consumer_delivery`)".

### Method
- Text-anchored edits; no other row of the Automated Tests table is touched (the line 236-region citations keep their test names per the Plan Design).

### Details
- No new approval record is written (INV-08 decision text is unchanged; UNK-03 stays open for a maintainer rewrite).

## Compatibility considerations
- `check_adr_preservation.py` compares invariant decision text: the INV-08 Invariants-list entry must remain byte-identical; only the verification mapping and the implementation-notes column list change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| ADR integrity | Docs | `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/check_known_deviation_sync.py` | No findings |
| Citation | Search | `rg -n "dlq_requeue_count" docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` (after this edit) | No match |

## Completion criteria
- AC-6 for ADR-006: INV-08 cites the renamed test, the column list matches the new `schema.sql`, and no invariant text changed.

## Out of Scope
- INV-08's invariant text (unchanged), INV-13 and the re-verified rows edited by adrrev015 (already applied), the `eventbus_12` NACK row (its own adrrev014 procedure, already applied).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006 / AC-6
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
