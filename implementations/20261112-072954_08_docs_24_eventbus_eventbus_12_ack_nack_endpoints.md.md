## Goal

Remove the obsolete NACK state-transition row from `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (line 74) that describes an "inline DLQ file write failed" path which has not existed since dlqbox001 made DLQ promotion a database-only transaction, and state that promotion is a DB transaction with artifact generation deferred to the outbox (`REQ-004` / `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 74 is the only place describing an inline DLQ file-write failure; line 40's `dlq_promoted: true` remains valid (promotion still sets it) and is untouched.
- `scripts/eventbus/dlq.py` promotes via `insert_outbox_row` (a `dlq_outbox` row written inside the caller's promotion transaction); the dead-letter artifact is generated later by the outbox worker (`process_outbox`), not at NACK time (dlqbox001).
- Removing the row does not leave a dangling reference; the remaining rows still describe the full live/NACK/DLQ lifecycle.

## Design decisions
- Delete only the single table row (line 74); do not renumber or reword the other rows, preserving the table's existing semantics.
- Add one sentence near the state-transition table stating that DLQ promotion is a DB transaction whose artifact generation is deferred to the outbox, so readers understand why the file-write-failure row was removed.

## Alternatives considered
- Rewriting the row to describe outbox failure instead of deleting it: rejected — outbox generation failures are covered by the `eventbus_03` failure table and the `dlq_outbox` status lifecycle; this table documents ACK/NACK persistence side effects, not outbox generation.

## Implementation
### Target file
`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure
1. Delete the row at line 74: `| Initial NACK, inline DLQ file write failed | 200 (no `dlq_promoted`) | Per-consumer failure count increases; the event stays live (`dlq_at` NULL) and the next sweep promotes it |`.
2. Add one clarifying sentence adjacent to the ACK/NACK State Transition Table stating that DLQ promotion is a DB transaction (the `dlq_outbox` row) and that dead-letter artifact generation is deferred to the outbox worker.
3. Do not alter any other row, the idempotency section, or other sections.

### Method
1. Remove the line-74 row entirely.
2. Insert after the table (before the `**NACK idempotency key scope and retention.**` bullet at line 82):
> DLQ promotion on NACK is a database transaction that writes the `dlq_outbox` row; the dead-letter artifact is generated later by the outbox worker, so a NACK never fails on a DLQ file write. Outbox generation failures are recorded on the outbox row and reported through `/health` (see `eventbus_03`).

### Details
- Keep `dlq_promoted: true` semantics (line 40) intact; the removed row's "no `dlq_promoted`" branch no longer applies because promotion either writes the outbox row (promoted) or it does not.
- The surviving rows already cover "the next sweep promotes it" (the background-sweep path); the removed inline-file-write variant was redundant and factually stale.

## Compatibility considerations
- Documentation-only. No other Plan targets `eventbus_12`; `check_docs_consistency.py --domain eventbus` must pass.

## Security considerations
- None: endpoint behavior documentation only.

## Rollback considerations
- N/A: revert the commit; the edit is localized to this document.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_japanese.py` — pass.

## Completion criteria
- `eventbus_12` has no inline-DLQ-file-write state-transition row.
- The surrounding text states that DLQ promotion is a DB transaction with artifact generation deferred to the outbox.
- `check_docs_consistency.py --domain eventbus` passes.

## Out of Scope
- Documenting outbox generation failures in detail — that is `eventbus_03` (seq 10).

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
- **Requirement ID**: `REQ-004` — remove the obsolete "inline DLQ file write failed" NACK state row
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`
