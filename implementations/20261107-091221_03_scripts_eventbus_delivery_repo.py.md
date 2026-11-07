## Goal

- scripts/eventbus/delivery_repo.py — make nack_event consumer_id required (AC-003, REQ-004)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- The `ValueError` guard runs before any query so the tightened contract cannot partially write delivery state.
- No deprecated signature, wrapper, or alias is left behind (REQ-004, REQ-005).

## Alternatives considered

- Keep `consumer_id: str | None = None` and runtime-assert non-None: rejected — REQ-004 removes the old signature; enforcement belongs in the type contract.

## Implementation
### Target file
`scripts/eventbus/delivery_repo.py`
### Procedure
1. Signature (lines 37-43): replace the parameter block so it reads
   ```python
   def nack_event(
       conn: sqlite3.Connection,
       event_id: str,
       consumer_id: str,
       last_nack_attempt: str | None = None,  # REQ-001: idempotency key for NACK
   ) -> NackResult:
   ```
   (remove the `| None` union, the default, and the internal-only comment).
2. Add the empty-value guard as the first statement of the function body, before any
   query:
   ```python
   if not consumer_id:
       raise ValueError("consumer_id must be a non-empty string")
   ```
3. Update the function docstring: state that `consumer_id` is required and must be
   non-empty, and delete the "internal-only" sentence.
4. Unconditionalize the three branches (the bodies stay identical, only the
   `if consumer_id is not None:` wrappers are removed and the bodies dedented):
   - the per-consumer ACK guard at line 76 (and its internal-only comments),
   - the `consumer_delivery` upsert block (lines 117-133 region) including its
     "if consumer_id is provided" comment,
   - the count read-back block (lines 136-149 region).
5. Delete the trailing `return NackResult("ok")` (line 150): with the read-back block
   unconditional, the `consumer_delivery` row always exists after the upsert, and the
   block's `return NackResult("ok", consumer_failure_count=...)` is the only success
   exit. Keep the inner `if consumer_row:` defensive check as-is.
6. Keep every other part of the function untouched: `not_found` / `invalid_state`
   early returns, the idempotency-key gate, `conn.commit()` / rollback semantics.
### Method
REQ-004 / AC-003. `nack_event()` (line 37) takes `consumer_id: str | None = None` with
an "internal-only: the /nack route always supplies consumer_id" comment (line 41), and
three `if consumer_id is not None:` branches exist: the per-consumer ACK guard (line
76), the `consumer_delivery` upsert (lines 117-133 region), and the per-consumer
count read-back (lines 136-149 region). The final `return NackResult("ok")` (line 150)
is the success-without-delivery-state path the Issue requires deleted: an internal
caller could not represent consumer state. The /nack route already validates the
pair via `authorize_event_pair()` and always passes consumer_id (docs 05, 06), so the
optional parameter only enables unauthenticated internal misuse.
### Details
Signature, guard, and branch structure only; all SQL statements stay byte-identical.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: nothing (Phase 1 start of the `nack-contract` release unit).
  - Blocks: doc 13 (its NACK matrix tests exercise the new contract), sibling documents 29, 30 (docs
  describe the required-consumer NACK contract).
  - Release unit: nack-contract (Phase 1). Signature tightening and the test updates land
  in one commit; no deprecated signature is kept.

## Security considerations

- The consumer_id-required contract closes the unauthenticated internal NACK path (Issue security constraint / AC-003): failure state is only ever written per validated consumer.

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: `grep -n "consumer_id is not None\|internal-only" scripts/eventbus/delivery_repo.py`
  Expected: no matches (docstring and code both clean).
- Command: `grep -n "return NackResult(\"ok\")$" scripts/eventbus/delivery_repo.py`
  Expected: no matches (only the `consumer_failure_count=` form remains).
- Command: `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q`
  Expected: the doc 13 matrix passes: valid consumer OK, missing argument raises
  `TypeError`, empty string raises `ValueError` before any query, duplicate idempotency
  key does not double-increment, multi-consumer independence (AC-003).
- Command: `uv run pytest tests/eventbus/ -q`
  Expected: all NACK route integration tests (400/403/404/409/422) still pass (AC-004).
  ever per-consumer (AC-003).

## Completion criteria

- no call pattern without `consumer_id` exists; failure state is only (AC-003, REQ-004)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tighten `nack_event` in `scripts/eventbus/delivery_repo.py` — Plan Phase 1 | Pending | — | — | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Pending | — | — | |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-005 / AC-003
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `scripts/eventbus/delivery_repo.py`
