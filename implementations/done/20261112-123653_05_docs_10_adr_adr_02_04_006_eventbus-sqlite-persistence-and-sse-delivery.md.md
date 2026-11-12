## Goal
Add ADR-008 to ADR-006's front matter `related` and Related ADRs, and state that ADR-006 owns INV-15 (loopback binding), with a pending approval record (`REQ-001`, `REQ-002`, `REQ-008` / `AC-1`, `AC-2`).

## Scope
**Release unit**: authority-model

## Assumptions
- Front matter `related` lacks ADR-008; the Related ADRs list has ADR-002, ADR-004, ADR-013 only; the body already cites ADR-008 (checked).
- Edit regions: front matter, Related ADRs, and the INV-15 line. Other Plans edit other regions: adrrev014 (Scope, Data Ownership, Replay Contract), adrrev015 (INV-13, test rows, requeue paragraph), `rmcompat005` (DLQ leftovers). Compatible.
- Baseline (Step 3a, 2026-11-12): `check_docs_structure.py` already reports ADR-004, ADR-008, and `deployment_01` over their ceilings (pre-existing, unrelated to this Plan).
- The ADR is 25626 bytes against a 25651 ceiling, so this and the other EventBus Plans' growth exceeds it (see Details).

## Design decisions
- Ownership is stated in one clause on INV-15, not a new section.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Add `adr_02_05_008_db-sqlite-4db-separation.md` to the front matter `related`.
2. Add `- ADR-008: SQLite 4DB Separation` to Related ADRs.
3. INV-15: add that ADR-006 owns the loopback-binding decision and ADR-013 layers authentication on top.
4. Append a `Current Decision Approval (pending)` line.

### Method
- INV-15 after: `The EventBus binds only to a loopback address (this ADR owns the decision; ADR-013 layers authentication on top); a non-loopback host fails configuration validation.`
- Approval line: approver, date, scope 不明; tracked by adrrev012.

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); no approval or reviewer name is written (UNK-05).
- Size gate: `tools/check_docs_structure.py` records a per-file ceiling equal to the accepted size, so any growth of this document fails `check_docs_structure.py`. The ceiling table is outside this Plan's target files; re-recording it follows the existing ceiling re-record chore (`plans/done` / `implementations` docsize series). Report the new size; do not edit the tool here (non-blocking `Needs confirmation`).
- The model edge `ADR-006 -> ADR-008` comes from row 01; execute with it.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_authority.py`, `check_adr_preservation.py` (only intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- ADR-008 is in the front matter and Related ADRs; INV-15's ownership is stated; a marked pending approval line exists; the front-matter check passes with row 01.

## Out of Scope
- INV-13, test rows, requeue paragraph (adrrev015); Scope, Data Ownership, Replay Contract (adrrev014).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112 | 20261112 | implemented per Procedure/Method: ADR-008 added to front matter related + Related ADRs; INV-15 ADR-006 ownership clause; pending approval line added |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112 | 20261112 | adr structure/inv-matrix/reference/authority/quality/content_policy--strict/japanese pass. preservation: 4 intended ERRORs (front matter, INV-15, Related ADRs ADR-008, Approval) + Invariants WARNING, all explained. docs structure: size-gate 29228>28672 non-blocking per Details |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | `check_docs_structure.py` size gate: ADR-006 grew 28672 -> 29228 bytes, over the 28672 ceiling. Non-blocking per Procedure > Details; the ceiling re-record is a separate docsize chore (the ceiling table is not edited here). New size 29228 reported for human confirmation. | no (non-blocking) | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` / `REQ-002` / `REQ-008` — ADR-008 in front matter and Related ADRs; INV-15 ownership; pending approval
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
