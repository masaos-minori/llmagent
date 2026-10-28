## Goal
Record in ADR-006 Implementation Notes that the database itself enforces at most one
redelivery descendant per original (REQ-006). Decisions and Invariants are not touched.

## Scope
- Edit `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
  only: one new bullet in the `## Implementation Notes` section (starts line 267).
- Reference only: `scripts/eventbus/schema.sql` (seq 01), `scripts/eventbus/dlq_repo.py`
  (seq 02), `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (unchanged, cited).

## Assumptions
- `## Implementation Notes` currently contains a bullet
  "DLQ requeue commits or rolls back as one unit, and the route runs all SQLite
  access inside the global database lock (INV-08, INV-16)." (verified this cycle,
  section lines 267-275); the new bullet sits next to it.
- No HTML comment markers exist in this ADR file (verified this cycle); the file's
  convention is plain inline `name` references, which the new bullet follows.
- The ADR Decisions and Invariants sections already describe requeue semantics
  without naming an enforcement layer, so no Invariant or Decision text changes are
  needed (Plan Out-of-Scope).

## Design decisions
- One bullet, phrased as current behavior with the index name and the code path, so
  `tools/check_adr_preservation.py` sees only an Implementation Notes addition:
  state that the partial unique index `idx_events_redelivered_from` (new) on
  `events(redelivered_from)` (ADR-008 recreate policy for existing databases)
  enforces the at-most-one-descendant rule, that `redeliver_event()` maps the
  violation to `already_redelivered` (HTTP 409), and that the pre-insert check is a
  fast classification path, not the enforcement layer.
- No test node cited in the bullet: Implementation Notes bullets may cite tests (the
  DLQ promotion bullet does), but the new mechanism's tests are named in seq 03/04/05
  docs; keeping the ADR bullet citation-free avoids coupling the ADR to test renames.

## Alternatives considered
- Amending the existing "DLQ requeue commits or rolls back as one unit" bullet:
  rejected — that bullet documents the lock/transaction boundary (INV-08, INV-16);
  merging constraint enforcement into it would obscure which layer guarantees what.
- Adding an Invariant: rejected — explicitly out of Plan scope.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. In `## Implementation Notes`, after the "DLQ requeue commits or rolls back as one
   unit" bullet, insert one bullet:
   "- Redelivery uniqueness is enforced by the database: the partial unique index
   `idx_events_redelivered_from` (new) on `events(redelivered_from)` permits at most one
   redelivery descendant per original; `redeliver_event()` maps the index violation
   to `already_redelivered` (HTTP 409) and the pre-insert check only classifies the
   sequential case. Existing databases are recreated on this schema change per
   ADR-008."
2. No other section changes.

### Method
Single bullet insertion; match the section's existing bullet style (bold-free,
inline code for identifiers).

### Details
- Section position verified this cycle: Implementation Notes is the section right
  before `## Known Deviations`; the insertion does not touch Decisions, Invariants,
  Verification, or Known Deviations.

## Compatibility considerations
- `tools/check_adr_preservation.py` compares Decisions/Invariants content; an
  Implementation Notes-only edit must report no unintended ERROR.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: remove the bullet on revert.

## Validation plan
- `uv run python tools/check_adr_preservation.py` — no unintended ERROR.
- `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_reference.py`.
- `uv run python tools/stale_detector.py docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`.

## Completion criteria
- Implementation Notes state database enforcement, the mapping to
  `already_redelivered`/409, and the ADR-008 recreate policy.
- Decisions, Invariants, Verification, Known Deviations byte-identical.
- ADR checkers report no errors for this file.

## Out of Scope
`eventbus_06` and `eventbus_04` docs (seq 07-08), ADR-008 itself (reference only),
any Invariant/Decision/Verification edit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Checker-gated, no new tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document's change IS the doc |

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
- **Requirement ID**: REQ-006 (ADR-006 Implementation Notes record database enforcement)
- **Source issue**: issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-200340
- **Related target files**: docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md
