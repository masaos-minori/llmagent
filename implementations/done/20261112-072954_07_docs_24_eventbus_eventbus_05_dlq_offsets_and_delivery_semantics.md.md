## Goal

Rewrite the Cleanup Procedure in `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (lines 177-193) to be foreign-key-safe: delete the dependent `dlq_outbox` rows before the `events` rows inside one transaction with foreign keys enabled, and replace the false claim that "the schema defines no foreign keys" (`REQ-003` / `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The current procedure (lines 181-193) states "The schema defines no foreign keys" and gives a bare `DELETE FROM events WHERE seq <= ?;`. With foreign keys enforced this fails when dependent `dlq_outbox` rows exist, and with them off it leaves orphan outbox rows — both wrong (`Plan Background`, `Plan Risks`).
- Foreign keys ARE enforced: `scripts/eventbus/schema.py` runs `PRAGMA foreign_keys=ON`, and `scripts/eventbus/schema.sql` declares `dlq_outbox.event_id PRIMARY KEY REFERENCES events(event_id)`.
- The operator still stops the EventBus service and backs up `eventbus.sqlite` before running (existing precaution, line 179) — keep it.
- `consumer_delivery` orphans and `consumer_offsets` behavior are unchanged from the current text.

## Design decisions
- Replace the "no foreign keys" paragraph with a factual statement that foreign keys are enforced and the dependent-row deletion order exists precisely because of them.
- Give a two-statement transaction: `DELETE FROM dlq_outbox …` then `DELETE FROM events …`, so the FK constraint is satisfied in one atomic unit.
- Preserve the surrounding bullet points (orphan `consumer_delivery`, DLQ `dlq_at` rows, `consumer_offsets` cutoff guidance) and only correct the FK claim and the SQL command.

## Alternatives considered
- Deleting via `events.dlq_at IS NOT NULL` filter instead of the `dlq_outbox` table: rejected — the FK lives on `dlq_outbox`, so its rows must be the ones deleted first; `dlq_at` alone does not cover the outbox record.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. Replace the sentence at line 181 ("The schema defines no foreign keys, so the statement affects related data as follows:") with a statement that foreign keys are enforced on the EventBus connection.
2. Rewrite the SQL command block (lines 189-191) to the two-statement transaction that deletes dependent `dlq_outbox` rows first.
3. Keep the surrounding bullets (lines 183-185) about `consumer_delivery` orphans, DLQ rows, and `consumer_offsets`, correcting only what the FK statement implies.
4. Do not alter other sections of `eventbus_05`.

### Method
Replace lines 181-193 with:

> The connection the EventBus opens enforces foreign keys (`PRAGMA foreign_keys=ON` in `scripts/eventbus/schema.py`), and `dlq_outbox.event_id` references `events(event_id)` (`scripts/eventbus/schema.sql`). The statement below therefore deletes the dependent `dlq_outbox` rows **before** the `events` rows, inside a single transaction, so the FK constraint is satisfied and no orphan outbox row is left behind.
>
> - `consumer_delivery` rows for the deleted events are not removed and remain as orphans.
> - DLQ rows (`events.dlq_at IS NOT NULL`) with a `seq` at or below the cutoff are deleted like any other event and can no longer be requeued.
> - `consumer_offsets` rows are not changed. Choose a cutoff at or below every consumer's committed offset so that no consumer loses undelivered events.
>
> Use the following SQL command:
>
> ```sql
> BEGIN;
> DELETE FROM dlq_outbox WHERE event_id IN (SELECT event_id FROM events WHERE seq <= ?);
> DELETE FROM events WHERE seq <= ?;
> COMMIT;
> ```
>
> Replace each `?` with the desired cutoff sequence number. After deletion, run `VACUUM` to reclaim disk space.

### Details
- Two `?` placeholders: bind the same cutoff value to both statements. Executing under one `BEGIN`/`COMMIT` makes the dependent-first order atomic — if the second statement fails, nothing is deleted.
- The orphan `consumer_delivery` and unchanged `consumer_offsets` bullets are carried over verbatim except for the FK claim; their substance is unchanged from the current document.
- Do not add a `dlq_outbox` retention note here — outbox retention is covered by ADR-006/ADR-008.

## Compatibility considerations
- Documentation-only. Overlap: `eventbus_05`'s Cleanup Procedure (lines 177-193) is also targeted by `plans/20261111-112439_adrrev019_docs-stale-statements.md`, which adds an `events.jsonl` line-count note to this same procedure. Implement this FK-safe rewrite first; adrrev019's additive note can then be layered on top without contradicting it. Re-run `tools/check_plan_target_overlaps.py` after editing.
- `check_docs_consistency.py --domain eventbus` must pass against the corrected FK statement and `schema.py`/`schema.sql`.

## Security considerations
- None: operator maintenance instructions only. The `?` placeholders (never string-interpolated cutoffs) keep the command parameter-safe.

## Rollback considerations
- N/A: revert the commit; the edit is localized to this document.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass (FK statement matches `schema.py`/`schema.sql`).
- `uv run python tools/check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_japanese.py` — pass.

## Completion criteria
- `eventbus_05` no longer states the schema has no foreign keys; it states foreign keys are enforced and deletes dependent `dlq_outbox` rows before `events` in one transaction.
- `check_docs_consistency.py --domain eventbus` passes.

## Out of Scope
- The `events.jsonl` line-count note that adrrev019 adds to this procedure — implement after this rewrite.
- Any change to `schema.py`/`schema.sql` (read-only for this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-151301 | 20261112-151301 | Changed: docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md. Step 3b: added PRAGMA foreign_keys = ON to the SQL block (a manual sqlite3 session does not enforce foreign keys by default); documented order verified against schema.sql in an in-memory database |
| 2 | Add or update tests per Validation plan | Completed | 20261112-151301 | 20261112-151301 | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261112-151301 | 20261112-151301 | No code changed in this cycle; end-of-batch full suite follows seq 11 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261112-151301 | 20261112-151301 | check_docs_consistency eventbus, content-policy strict, quality, japanese pass; check_docs_structure only the 3 pre-existing over-ceiling files |

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
- **Requirement ID**: `REQ-003` — make the manual cleanup procedure foreign-key-safe (dependent `dlq_outbox` rows first, in one transaction) and stop claiming the schema has no foreign keys
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`