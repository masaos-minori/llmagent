## Goal

Record the NACK idempotency invariant and retention policy in `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` and close EVENTBUS-023 (`adr_02_04_006:278`): the route no longer mints a per-request attempt identifier, so a repeated NACK for the same delivery attempt deduplicates against the remembered key (`REQ-003`, `REQ-004`).

## Scope

- **In-Scope** (`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` only):
  - Add an idempotency-invariant + retention bullet to "Implementation Notes".
  - Close EVENTBUS-023 in "Known Deviations" (`adr_02_04_006:278`): mark it resolved with the fix reference.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01) — the fix.
  - Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
  - Contract doc (`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, seq 07).
  - Tests (seq 05/06).

## Assumptions

- The idempotency invariant belongs alongside the other persistence invariants (INV-13 etc.) in "Implementation Notes", next to the existing NACK/DLQ bullet (`adr_02_04_006:271`).
- Closing EVENTBUS-023 means relabeling its "Known Deviations" entry as resolved with a fix date and reference; the issue itself is closed in Issue 5 (`issues/20261023-154326_eventbus005_nack-idempotency-retries.md`).
- UNK-03 recommended = latest-key-only: the retention policy is "one remembered key per `(consumer_id, event_id)`".

## Design decisions

- **Invariant next to INV-13.** The NACK idempotency invariant is a persistence behavior like the DLQ-promotion invariant already at `adr_02_04_006:271`; placing it there keeps the invariant catalogue coherent.
- **Close by relabel.** The "Known Deviations" list uses a "Known Issue" label; closing EVENTBUS-023 relabels that entry "Resolved" with the fix reference rather than deleting it, preserving the governance audit trail.

## Alternatives considered

- **New "Resolved Issues" subsection:** moving closed issues out of "Known Deviations" into a separate list. Rejected as heavier — a targeted relabel of the single entry is sufficient and preserves the existing structure.
- **Leave EVENTBUS-023 as a Known Issue:** rejected — the defect is fixed; leaving it labeled "Known Issue" misrepresents current state.

## Implementation

### Target file

`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

1. Add an idempotency-invariant bullet to "Implementation Notes" after the INV-13 bullet (`adr_02_04_006:271`).
2. Relabel the EVENTBUS-023 entry in "Known Deviations" (`adr_02_04_006:278`) from "Known Issue" to "Resolved" with the fix date and reference.
3. Run the documentation checkers.

### Method

"Implementation Notes" (`adr_02_04_006:267-271`) documents the offset store, INV-07, and the INV-13 DLQ-promotion threshold. "Known Deviations" (`adr_02_04_006:273-278`) lists unresolved issues including EVENTBUS-023 at `adr_02_04_006:278` ("a repeated NACK request is counted again; the route generates a new attempt identifier per request"). The edits below are additive (new invariant bullet) and a targeted relabel of the single EVENTBUS-023 line.

```markdown
<!-- adr_02_04_006 — add after the INV-13 bullet (adr_02_04_006:271) -->
- NACK idempotency (REQ-003): the per-consumer `consumer_delivery_failure_count` is
  incremented once per distinct delivery-attempt key; a NACK that repeats the same
  `consumer_last_nack_attempt` key is a no-op. Deduplication is latest-key-only (one
  remembered key per `(consumer_id, event_id)`); a non-latest key counts as a new
  attempt. The route passes the caller-supplied key unchanged (no per-request UUID),
  so genuine network/proxy retries of one attempt deduplicate rather than double-count.
```

```markdown
<!-- adr_02_04_006 — close EVENTBUS-023 (adr_02_04_006:278) -->
- **Resolved**: EVENTBUS-023 — fixed 2026-10-25 (the route now passes the caller-supplied
  idempotency key, so a repeated NACK deduplicates instead of being counted again;
  tracked in governance_03 Part 1)
```

### Details

- **`REQ-003` (no double count):** the new invariant records that a repeated delivery-attempt key is a no-op and a distinct key increments once — the fix for EVENTBUS-023.
- **`REQ-004` / UNK-03 (retention):** the latest-key-only retention policy is recorded as the canonical scope; a bounded-set adoption would be a schema change (not adopted).
- **EVENTBUS-023 closure:** the defect ("route generates a new attempt identifier per request") is resolved by seq 01 (caller key) + seq 02 (live guard); the entry is relabeled "Resolved" with the fix date, preserving the governance trail.

## Compatibility considerations

- N/A: documentation-only edit to an ADR; no code, schema, or behavioral change.

## Security considerations

- N/A: no credentials, secrets, or authorization changes.

## Rollback considerations

- N/A: revert the doc edit (`git checkout docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| ADR integrity | Current-source verification | `uv run python tools/stale_detector.py {this doc}` | All referenced constructs found; EVENTBUS-023 resolved |
| Structure check | Structure | `uv run python tools/check_workitem_structure.py {this doc}` | No findings |

## Completion criteria

- The idempotency invariant + latest-key-only retention policy are recorded in "Implementation Notes".
- EVENTBUS-023 in "Known Deviations" is relabeled "Resolved" with the fix date/reference.
- `stale_detector.py` and `check_workitem_structure.py` pass.

## Out of Scope

- Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
- Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
- Contract doc (`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, seq 07).
- Tests (seq 05/06).
- UNK-03 bounded-set retention — recorded as not adopted.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the NACK idempotency invariant + retention policy; close EVENTBUS-023 in Known Deviations | Pending | — | — | Docs-only; latest-key-only recorded |
| 2 | Run the documentation checkers (`stale_detector.py`, `check_workitem_structure.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-120857_eventbus005_nack-idempotency-retries.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-203128
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
