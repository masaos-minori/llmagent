# Update the canonical EventBus DLQ/offset specification doc

## Goal

Update `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` to describe the redesigned requeue/redelivery model, the lifetime-vs-cycle failure count split, and the SQLite-canonical/JSON-archive DLQ state policy as the canonical specification, replacing the current text (line ~36) that documents today's flag-only behavior as intended.

## Scope

- Replace the requeue-behavior description (around line ~36) with the redesigned model.
- Document the lifetime-vs-cycle failure count split.
- Document the SQLite-canonical/JSON-archive DLQ state policy.

## Assumptions

- Current text states the flag-only behavior ("clears `dlq_at` and increments `dlq_requeue_count` (`delivery_failure_count` is not reset)") as canonical (confirmed by reading line ~36 directly).
- The doc follows the project's documentation conventions (English language, structured headings).

## Design decisions

- Rewrite the requeue section to describe:
  1. Redelivery creates a new row with fresh UUID v4 `event_id`.
  2. `redelivered_from` points to the original event.
  3. `cycle_failure_count` resets to 0 on redelivery; `delivery_failure_count` carries forward.
  4. Active subscribers receive the redelivered event via `EventBroker.publish()`.
  5. Reconnecting subscribers reach it via the `seq > since_seq` replay path.
  6. DLQ JSON file is archived to `requeued/` subdirectory.
- Keep the existing offset semantics unchanged (they are out of scope for this Plan).

## Alternatives considered

- Adding a separate "Redelivery" section: rejected because the requeue behavior is central to the DLQ lifecycle and should replace the existing description rather than being appended.
- Keeping the old text alongside the new: rejected because the old behavior is no longer correct.

## Compatibility considerations

- This is a documentation-only change — no code or schema impact.
- External consumers relying on the documented spec will see the updated behavior description.

## Security considerations

- No security surface change.

## Rollback considerations

- Reverting means restoring the old flag-only requeue description.

## Validation plan

- Run `uv run python tools/check_docs_quality.py docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` to confirm no structural findings.
- Run `uv run python tools/check_docs_structure.py docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` to confirm no structural findings.
- Manual review: verify the rewritten section accurately describes the new redelivery model.

## Completion criteria

- Line ~36 text is replaced with the redesigned requeue/redelivery model description.
- Lifetime-vs-cycle failure count split is documented.
- SQLite-canonical/JSON-archive DLQ state policy is documented.
- Documentation quality checks pass.

## Out of scope

- Code changes to implement the new behavior.
- Test updates.
- Changes to other documentation files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace requeue-behavior description with redesigned model | Completed | — | — | |
| 2 | Document lifetime-vs-cycle failure count split | Completed | — | — | |
| 3 | Document SQLite-canonical/JSON-archive DLQ state policy | Completed | — | — | |

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md
