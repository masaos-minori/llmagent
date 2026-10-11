## Goal
- Make `ack_event_for_consumer()` in `scripts/eventbus/delivery_repo.py` behave as its contract says: a pending delivery row becomes acked (`REQ-007`), an already-acked event returns its `seq` (`REQ-005`), and the docstring describes all four cases including the DLQ case (`REQ-005`).

## Scope
- Replace the `COALESCE` in the ACK UPSERT with `MAX`.
- Look up `seq` for every found, non-DLQ event, while keeping the offset UPSERT inside the `newly_acked` branch.
- Correct the docstring.
- No signature change, no schema change, no change to other functions.

## Assumptions
- Verified in the current file: the UPSERT is `acked = COALESCE(consumer_delivery.acked, excluded.acked)` and `consumer_delivery.acked` is `INTEGER NOT NULL DEFAULT 0` (`scripts/eventbus/schema.sql`). A pending row (`acked = 0`) therefore never becomes `1` (reproduced in sqlite).
- `seq` is assigned only inside `if newly_acked:`, so a duplicate ACK returns `(True, False, None)` although the docstring, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, and `test_offset_does_not_regress_on_older_seq` expect `(True, False, seq)`.
- A scratch-worktree run with `MAX(consumer_delivery.acked, excluded.acked)` turned five more tests green (the ACK endpoint, repeated-ACK, NACK-after-ACK 409, and concurrent-ACK tests).

## Design decisions
- Use `MAX(consumer_delivery.acked, excluded.acked)`: an existing `1` stays `1`, a pending `0` becomes `1`, and no schema change is needed.
- Keep the existing-row read before the write so `newly_acked` still means "this call changed the row from missing/pending to acked".
- Move the `seq` lookup out of the `if newly_acked:` branch; keep the `consumer_offsets` UPSERT (with its `excluded.offset > consumer_offsets.offset` guard) inside it, so a duplicate ACK never moves the offset.
- Return value stays a 3-tuple; the DLQ case keeps returning `(True, False, None)`.

## Alternatives considered
- Restore the 4-value return with a DLQ flag: rejected by the Plan.
- Replace the UPSERT with `acked = 1`: equivalent here, but `MAX` keeps the intent "never un-ack" explicit.
- Leave the UPSERT and edit the five tests: rejected, because the tests encode the documented behavior and the current behavior is the defect.

## Implementation
### Target file
`scripts/eventbus/delivery_repo.py`

### Procedure
1. Re-read `ack_event_for_consumer()` and confirm the three anchors below are unchanged.
2. Change the UPSERT conflict clause from `COALESCE(consumer_delivery.acked, excluded.acked)` to `MAX(consumer_delivery.acked, excluded.acked)`.
3. Hoist the `SELECT seq FROM events WHERE event_id = ?` lookup and `seq = int(row["seq"])` out of `if newly_acked:`, keeping the offset UPSERT under `if newly_acked:`.
4. Rewrite the docstring's return description.

### Method
- Edit only the UPSERT string, the `seq` lookup block, and the docstring; leave the existence check, the DLQ check, the commit, and the rollback unchanged.
- Keep the single `conn.commit()` at the end so the delivery-state UPSERT and the offset advancement stay in one transaction (ADR-006 INV-16).

### Details
- Docstring return text: `(True, True, seq)` newly acked; `(True, False, seq)` found and already acked by this consumer; `(True, False, None)` found but the event is in the DLQ, nothing written; `(False, False, None)` not found.
- Do not mention line numbers in the docstring.

## Compatibility considerations
- Callers: `scripts/eventbus/ack_route.py` (lazy import through `eventbus.db`) and tests. The route already re-reads `seq` for the duplicate case, so returning it earlier is compatible.
- Behavior change: a consumer's pending row is now marked `acked = 1`, so a later NACK from the same consumer returns 409 as the documentation states, and a duplicate ACK reports `already_acked`.
- The offset still never moves backward.

## Security considerations
- No new input handling; SQL stays parameterized.
- The MAX expression is a constant string with no interpolation.

## Rollback considerations
- Single-file change; revert with `git revert` of the implementing commit, or `git checkout -- scripts/eventbus/delivery_repo.py` before it is committed.
- Rows already written with `acked = 1` stay valid; rows left at `0` by the old behavior are not rewritten.

## Validation plan
- `uv run pytest tests/eventbus tests/db`: only the five failures named in the Plan's Out-of-Scope remain.
- `uv run pytest tests/eventbus/test_eventbus_crash_ack.py`: INV-16 atomicity tests still pass.
- `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, and `uv run bandit -r scripts/eventbus -c pyproject.toml` report no new findings.

## Completion criteria
- The UPSERT turns a pending row into `acked = 1` and never lowers it.
- A duplicate ACK returns `(True, False, seq)`; the DLQ case returns `(True, False, None)`.
- The docstring matches the code and the endpoint documentation.
- The offset UPSERT is still inside the `newly_acked` branch and the transaction is still committed once.

## Out of scope
- Signature or return-shape changes, schema changes, `nack_event()`, and other eventbus modules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the UPSERT to `MAX` | Pending | — | — | |
| 2 | Hoist the `seq` lookup and keep the offset UPSERT under `newly_acked` | Pending | — | — | |
| 3 | Correct the docstring | Pending | — | — | |
| 4 | Add or update tests per Validation plan | Pending | — | — | N/A: covered by existing tests listed in Validation plan and by procedures 01, 02, 05 |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 6 | Update documentation, if in scope | Pending | — | — | N/A: documentation is handled by procedure 06 |

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
- **Requirement ID**: `REQ-005` (return `seq`, docstring), `REQ-007` (ACK UPSERT)
- **Source issue**: issues/20261011-075321_eb012ack_resolve-ack_event_for_consumer-return-contract-mismatch-between-code-and-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-153619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-175858
- **Related target files**: scripts/eventbus/delivery_repo.py
