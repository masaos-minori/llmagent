## Goal

Update ADR-006 to record the design decision (Option B) for handling out-of-order ACKs, preserving the at-least-once delivery guarantee without requiring consumer-side ordering discipline.

## Scope

- Modify `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`: add Known Issues section documenting Option B choice and rationale.

## Assumptions

- The at-least-once delivery statement in ADR-006 is correct and should be preserved.
- Consumers can handle duplicate deliveries — confirmed by the at-least-once baseline.
- The Known Issues section exists in ADR-006 (verified at line 386).

## Design decisions

- Record Option B as the chosen approach: compute resume position as `max(lowest_unacked_seq, stored_offset)`.
- Document that consumers cannot reliably ACK in strict seq order under network partition or broker reordering.
- Note that the existing high-water-mark offset remains useful for fast-forwarding already-acked events; the new logic adds a low-water-mark fallback below it.

## Alternatives considered

- Option A (ordered ACK as consumer obligation): rejected because it contradicts the at-least-once baseline stated in ADR-006.
- Option C (track both low-water mark and high-water mark separately): rejected because it adds schema complexity; the query-based approach derives the low-water mark on demand without persistent state.

## Implementation

### Target file

`docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

Add a Known Issues section documenting Option B choice, rationale, and behavior change.

### Method

1. Locate the Known Issues section in ADR-006.
2. Add entries for EVENTBUS-001 with Option B resolution.

### Details

**Change — Add Known Issues section to ADR-006:**

```markdown
## Known Issues

### EVENTBUS-001: Out-of-order ACK skips lower-seq events on reconnect

**Status**: Resolved (by design decision)

**Resolution**: Option B — resume position accounts for lowest unacked event.

**Rationale**: Preserves at-least-once guarantee without requiring ordered ACKs.
Consumers cannot reliably ACK in strict seq order under network partition or
broker reordering. The existing high-water-mark offset remains useful for
fast-forwarding already-acked events; the new logic adds a low-water-mark
fallback below it.

**Behavior change**: Resume position now uses `max(lowest_unacked_seq, stored_offset)`
instead of `stored_offset` alone. This ensures no unacked event is skipped on
reconnect while still allowing fast-forward past already-acked events.
```

## Compatibility considerations

- Documentation-only change — no behavioral risk.
- The Known Issues section provides traceability between the ADR and the implementation fix.

## Security considerations

- No security impact. Documentation update only.

## Rollback considerations

- Remove the Known Issues section entry if the underlying implementation changes.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md | Static: format, lint | `uv run ruff format` / `ruff check` on the file | Clean; no new errors |
| Full suite | Regression | `uv run pytest tests/` | No new failures |

## Completion criteria

- [ ] Known Issues section added to ADR-006 documenting Option B choice.
- [ ] Rationale documented: preserves at-least-once guarantee without requiring ordered ACKs.
- [ ] Behavior change documented: resume position uses `max(lowest_unacked_seq, stored_offset)`.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

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
- **Related target files**: docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md