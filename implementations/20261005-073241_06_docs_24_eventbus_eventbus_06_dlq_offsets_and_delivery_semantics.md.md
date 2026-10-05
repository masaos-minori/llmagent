## Goal

Align the offset semantics description in the EventBus DLQ/Offsets/Delivery Semantics document with Option B: resume position accounts for both high-water mark and lowest unacked event.

## Scope

- Modify `docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md`: update the offset semantics paragraph to reflect Option B behavior.

## Assumptions

- The document exists and contains an offset semantics section that needs updating.
- The offset semantics should describe both the high-water mark (offset) and the low-water mark (lowest unacked seq).

## Design decisions

- Document that the offset remains a high-water mark (non-decreasing).
- Document that resume position uses `max(lowest_unacked_seq, stored_offset)`.
- Note that no loss of unacked events occurs on reconnect.

## Alternatives considered

- Replace the entire offset semantics section: rejected because only the resume position computation changes; the offset definition itself remains valid.
- Add a separate "Low-Water Mark" subsection: rejected because the low-water mark is derived on demand, not persisted separately.

## Implementation

### Target file

`docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md`

### Procedure

Update the offset semantics paragraph to reflect Option B behavior.

### Method

1. Locate the offset semantics section in the document.
2. Update the paragraph to describe the new resume position computation.

### Details

**Change — Update offset semantics paragraph:**

Before:
```markdown
The consumer offset tracks the highest acknowledged sequence number. On reconnect,
the consumer resumes from the next sequence after the offset.
```

After:
```markdown
The consumer offset tracks the highest acknowledged sequence number (high-water mark).
On reconnect, the resume position is computed as `max(lowest_unacked_seq, stored_offset)`,
where `lowest_unacked_seq` is the minimum sequence among events where
`consumer_delivery.acked_at IS NULL` AND `seq <= stored_offset`. This ensures no
unacked event is skipped on reconnect while still allowing fast-forward past already-
acked events.

For consumers that ACK in order, `lowest_unacked_seq = stored_offset + 1` when all
events up to the offset are acked, so the resume position equals `stored_offset + 1`
(fast-forward). For consumers with out-of-order ACKs, the low-water-mark fallback
ensures previously skipped events are re-delivered.
```

## Compatibility considerations

- Documentation-only change — no behavioral risk.
- The updated semantics provide clarity for consumers implementing their own recovery logic.

## Security considerations

- No security impact. Documentation update only.

## Rollback considerations

- Revert to the original offset semantics paragraph if the underlying implementation changes.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md | Static: format, lint | `uv run ruff format` / `ruff check` on the file | Clean; no new errors |
| Full suite | Regression | `uv run pytest tests/` | No new failures |

## Completion criteria

- [ ] Offset semantics paragraph updated to describe Option B behavior.
- [ ] Resume position formula documented: `max(lowest_unacked_seq, stored_offset)`.
- [ ] Low-water-mark fallback behavior documented for out-of-order ACK scenarios.
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.

## Out of scope

- Changes to `delivery_repo.py` (separate procedure document).
- Changes to `subscribe_route.py` (separate procedure document).
- Adding an index on `consumer_delivery(acked_at)` (separate procedure document).
- Creating regression tests (separate procedure document).

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261004-095313_eventbus001_eventbus-out-of-order-ack-skips-lower-seq-events-on-resume.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-100000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-073241
- **Related target files**: docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md
