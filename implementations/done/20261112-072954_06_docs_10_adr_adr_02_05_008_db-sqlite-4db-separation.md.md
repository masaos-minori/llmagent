## Goal

Extend ADR-008's `eventbus.sqlite` contents line (Decision Detail #4, line 117) to include the `dlq_outbox` durable promotion record, with a pending maintainer-approval record, so the outbox is named among the `eventbus.sqlite` contents (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The current Decision Detail #4 (line 117) reads "`eventbus.sqlite`: canonical store for Events, Offsets, Delivery, and the DLQ. Owned by the EventBus service." and omits the `dlq_outbox` table, which appears in `eventbus_03/06/08` but in no ADR (Plan Background).
- The edit is decision-text only and needs a pending maintainer approval record (UNK-04), tracked by adrrev012.
- This Plan edits only Decision Detail #4; ADR-008's Decision Details #7/#8 and `## Known Deviations` are owned by adrrev009 (already landed) and adrrev012 respectively — do not touch them.

## Design decisions
- Extend the existing sentence in Decision Detail #4 rather than adding a new detail number, preserving the list's structure and the "Owned by the EventBus service" clause.
- Add a single `Current Decision Approval (pending)` line to ADR-008's Approval Record, mirroring the phrasing used in the ADR-006 procedure.

## Alternatives considered
- Adding a new Decision Detail #15 for the outbox: rejected — the outbox is part of the `eventbus.sqlite` contents already enumerated in #4; a new number would fragment the ownership statement.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Edit Decision Detail #4 (line 117) to name the `dlq_outbox` table among the `eventbus.sqlite` contents.
2. Append one `Current Decision Approval (pending)` line to ADR-008's Approval Record.
3. Do not alter Decision Details #1-#13/#14+, the Known Deviations, or any other ADR.

### Method
1. Decision Detail #4 (line 117) becomes:
> 4. `eventbus.sqlite`: canonical store for Events, Offsets, Delivery, the `dlq_outbox` durable promotion record, and the DLQ. Owned by the EventBus service.

2. Approval Record (append before the closing paragraph):
> - **Current Decision Approval (pending)**: Adding the `dlq_outbox` durable promotion record to the `eventbus.sqlite` contents in Decision Detail #4 is a decision-text change awaiting maintainer approval; tracked by the approval-ledger Plan (adrrev012). No approval is fabricated.

### Details
- The `dlq_outbox` DDL and its `pending`/`done`/`failed` status lifecycle are specified in `scripts/eventbus/schema.sql` and `eventbus_03`; this ADR names the table and defers the operational detail to those references, consistent with how #4 already summarizes each DB's contents.
- Keep the edit to the single sentence in #4; the shared-fingerprint recovery wording and Known Deviations (SHARED-001/002, owned by adrrev009) are out of scope.

## Compatibility considerations
- Documentation-only. Overlap: ADR-008 is also edited by adrrev009 (Decision #7/#8 wording, Known Deviations — already landed) and adrrev012 (`## Known Deviations` only). This Plan touches only Decision Detail #4 and this ADR's Approval Record — distinct locations.
- Re-run `tools/check_plan_target_overlaps.py` after editing to confirm no collision with adrrev012's Known Deviations region.

## Security considerations
- None: data-ownership wording only.

## Rollback considerations
- N/A: revert the commit; the edit is localized to this document.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `check_adr_preservation.py` — pass (preservation reports only the intended #4 text change).
- `uv run python tools/check_db_separation.py` — pass (the `eventbus.sqlite` contents now include the outbox consistently with ADR-006).
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_japanese.py` — pass.

## Completion criteria
- ADR-008 Decision Detail #4 names the `dlq_outbox` table among the `eventbus.sqlite` contents.
- ADR-008 carries one `Current Decision Approval (pending)` line for this edit; no approval is fabricated.
- `check_db_separation.py`, `check_adr_structure.py`, `check_adr_authority.py`, `check_adr_preservation.py`, and `check_docs_consistency.py --domain eventbus` pass.

## Out of Scope
- The ADR-008 Recovery Detail #7/#8 wording and Known Deviations (SHARED-001/002) — owned by adrrev009.
- The manual cleanup foreign-key rewrite — that is `eventbus_05` (seq 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-151147 | 20261112-151147 | Changed: docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md (Decision Detail 4 + pending approval line; plan ID omitted from doc text) |
| 2 | Add or update tests per Validation plan | Completed | 20261112-151147 | 20261112-151147 | N/A: documentation-only; tests/tools passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261112-151147 | 20261112-151147 | ADR structure/authority/matrix/reference, check_db_separation, known-deviation-sync pass; preservation reports only the intended Decision/Approval change; check_docs_structure: ADR-008 stays over its ceiling (36570 vs 34206), pre-existing (was 36197) and not re-recorded per user decision |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261112-151147 | 20261112-151147 | docs checkers pass (quality, content-policy strict, japanese, consistency eventbus) |

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
- **Requirement ID**: `REQ-001` — ADR-008 Decision Detail 4 includes the `dlq_outbox` among the `eventbus.sqlite` contents
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`