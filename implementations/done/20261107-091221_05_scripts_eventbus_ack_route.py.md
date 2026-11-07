## Goal

- scripts/eventbus/ack_route.py — import delivery operations from delivery_repo (AC-002, REQ-002, REQ-005)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Keep the module-private `_nack_event` alias so every call site and the authorization flow stay byte-identical.

## Alternatives considered

- Drop the `_nack_event` alias and rename call sites: rejected — churn with no benefit; the alias is module-private, not a facade.

## Implementation
### Target file
`scripts/eventbus/ack_route.py`
### Procedure
1. Replace line 14:
   ```python
   from eventbus.delivery_repo import nack_event as _nack_event
   ```
   Keeping the `_nack_event` alias preserves every existing call site unchanged.
2. Replace the deferred import at line 79 with `from eventbus.delivery_repo import
   ack_event_for_consumer`, keeping the deferred placement and its `# noqa: PLC0415` marker:
   ```python
   from eventbus.delivery_repo import ack_event_for_consumer
   ```
3. Change nothing else: authorization calls, response codes, and idempotency-key
   handling stay exactly as they are (REQ-005).
### Method
REQ-002 / AC-002. Two facade imports exist:
- Line 14: `from eventbus.db import nack_event as _nack_event` (module level).
- Line 79: deferred `from eventbus.db import ack_event_for_consumer  # noqa: PLC0415`.
Both names live in `eventbus.delivery_repo`. The `nack_event` call site (line 173,
`_nack_event(...)`) already passes `consumer_id` positionally and the route validates
the (event_id, consumer_id) pair via `authorize_event_pair()` — the validation logic
is unchanged (REQ-005: keep 400/403/422/404 behavior and idempotency gating).
### Details
Import lines only; assertions and fixtures unchanged.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: nothing for the import migration itself; the consumer_id-required contract
  it relies on is already satisfied by the route's own validation and doc 03.
  - Blocks: sibling documents 02 (ack_route is one of the importers that must be migrated before the
  facade is deleted).

## Security considerations

- The 403 pair-authorization flow via `authorize_event_pair()` and the 400/422 validation stay byte-identical (REQ-005 / AC-004).

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: `grep -n "eventbus.db\b" scripts/eventbus/ack_route.py`
  Expected: no matches.
- Command: `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py tests/eventbus/test_eventbus_ack_nack.py -q`
  Expected: pass; the 422-missing-param test at line 573 of `tests/eventbus/test_eventbus_ack_nack.py` (anchor re-verified at HEAD `dc426f9ad`) and the 403 tests (lines 772-828) pass unchanged (AC-004).
  validation contract is byte-for-byte unchanged.

## Completion criteria

- the route imports both delivery names from `delivery_repo` and its (AC-002, REQ-002, REQ-005)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate facade imports in this file — Plan Phase 2 | Completed | 20261107-164122 | 20261107-164122 | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Completed | 20261107-164122 | 20261107-164122 |  |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Completed | 20261107-164122 | 20261107-164122 |  |

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
- **Requirement ID**: REQ-002 / AC-002
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `scripts/eventbus/ack_route.py`