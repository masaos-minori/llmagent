## Goal

Confirm that `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` is consistent with REQ-004/REQ-006: no ADR invariant references the removed event-level `events.acked_at`, and ACK/NACK state invariants describe per-consumer `consumer_delivery` state.

## Scope

Verify `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` only. No functional edit is required for REQ-004/REQ-006 unless a Plan revision directs otherwise (see Out of scope / Plan Gap). Specifically:

- Confirm INV-10 (line 234) does not reference an event-level acked flag; it describes connection exclusivity + consumer_id binding.
- Confirm INV-12 (line 236) does not reference `events.acked_at`.
- Confirm INV-16 (line 240) references `ack_event_for_consumer()` correctly.
- Confirm the data model summary (lines 443-444) explicitly states "no event-level `acked_at` column".

Referenced/updated by other documents (not modified here): the ACK/NACK endpoint doc `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (row 8) and the Known Issues ledger `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (row 9).

## Assumptions

- ADR invariants are normative; any wording change must stay consistent with the implementation and the endpoint contract doc.
- The invariant numbering and positions (lines 232-237) are stable.

## Design decisions

- **Minimal, consistent edits**: change only the invariant wording that references ACK/NACK state; preserve the existing INV structure, numbering, and cross-references (e.g. ADR-013 INV-02).
- **Per-consumer framing**: describe ACK/NACK state as living in `consumer_delivery` (per consumer), consistent with rows 1-2.

## Alternatives considered

- Rewriting the whole INV list: rejected — scope is the ACK/NACK persistence invariants only.

## Implementation

### Target file

`docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

1. Read INV-10 (line 234) and confirm whether its substantive content (connection exclusivity + consumer_id binding) already covers per-consumer ACK/NACK state; if the ACK/NACK clause implies an event-level acked flag, reword it to reference `consumer_delivery` per-consumer state. **Already confirmed** — INV-10 describes connection exclusivity + consumer_id binding only; no event-level acked flag reference.
2. Review INV-12 (line 239) and INV-16 (line 246) for references to event-level `acked_at`; align them with per-consumer `consumer_delivery.acked_at` where they describe ACK persistence. **Already confirmed** — neither INV-12 nor INV-16 references `events.acked_at`.
3. Preserve all other invariants and cross-references unchanged. **Already confirmed**.
4. Confirm the data model summary (lines 443-444) explicitly states "no event-level `acked_at` column". **Already confirmed**.

### Method

- Sentence-level edits to the identified invariant bullets; no renumbering, no new invariants unless a genuine gap is found (flag as Plan Gap).

### Details

- INV-10 currently reads: "On ACK and NACK, a caller may use only the `consumer_id` values bound to its token." Verify this still holds after REQ-001/003; the connection-exclusivity half is unchanged. **Already confirmed** — INV-10 describes connection exclusivity + consumer_id binding only.
- INV-16 references `ack_event_for_consumer()` — that function is modified under REQ-005 (row 1); ensure the invariant's "single transaction" claim remains accurate. **Already confirmed** — INV-16 correctly describes the single-transaction guarantee.
- Data model summary (lines 443-444): explicitly states "no event-level `acked_at` column; ACK state is per-consumer in `consumer_delivery`".

## Compatibility considerations

- Documentation-only; no runtime impact. Ensure consistency with the endpoint contract doc (row 8) and the implementation.

## Security considerations

- No security impact.

## Rollback considerations

- Revert the edited invariant bullets to restore prior wording.

## Validation plan

- Manual documentation review: invariants match the per-consumer implementation and the endpoint doc.
- Internal-link / reachability check via `tools/check_docs_structure.py`.
- `tools/check_docs_quality.py` and `tools/check_docs_content_policy.py` if doc-quality gates run on docs changes.

## Completion criteria

- No ADR invariant references the removed event-level `events.acked_at`. **Already met**.
- ACK/NACK state invariants describe per-consumer `consumer_delivery` state. **Already met**.
- INV numbering and cross-references preserved. **Already met**.

## Out of scope

- The endpoint contract doc (`eventbus_12`, row 8).
- The Known Issues ledger (`governance_03`, row 9).
- The implementation that drops `acked_at` (rows 1-2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | All items already consistent with REQ-004/REQ-006 |
| 2 | Add or update tests per Validation plan | Completed | — | — | Tests updated in prior cycle |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy passed in prior cycle |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | |

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
- **Requirement ID**: `REQ-006` (documentation update) with `REQ-004` (drop `events.acked_at`) consistency
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-132618
- **Related target files**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
