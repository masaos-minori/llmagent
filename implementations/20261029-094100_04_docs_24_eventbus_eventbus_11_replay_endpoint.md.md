## Goal

Replace the "consistent snapshot" wording in the replay endpoint doc
`docs/24_eventbus/eventbus_11_replay_endpoint.md` with per-response (request-local)
wording that keeps the accurate single-acquisition fact but drops the cross-request
implication.

## Scope

Docs-only edit to `docs/24_eventbus/eventbus_11_replay_endpoint.md`. No production code, no
tests.

## Assumptions

- The "## Ordering and Consistency" section (existing lines 66-68) currently reads:
  "The page and the total count are fetched under the global DB lock in a single
  acquisition, so the returned events and `total` form a consistent snapshot; concurrent
  writes do not affect the result set."
- The single-acquisition fact is true *within* one `/replay` response, but the phrase
  "form a consistent snapshot" / "concurrent writes do not affect the result set" implies a
  cross-request guarantee the API does not provide. The reword states per-response
  consistency only.
- This doc is distinct from the DLQ endpoint doc (seq 03) and `eventbus_03_dlq_operations.md`
  (sibling plans), so no cross-plan wording conflict.

## Design decisions

- Reword the existing second sentence in place; keep the first sentence (ordering by `seq`).

## Alternatives considered

- Deleting the whole "Ordering and Consistency" section: rejected; the single-acquisition
  per-response fact is accurate and worth documenting.

## Implementation

### Target file

`docs/24_eventbus/eventbus_11_replay_endpoint.md`

### Procedure

1. Open `docs/24_eventbus/eventbus_11_replay_endpoint.md`.
2. In the "## Ordering and Consistency" section (existing lines 66-68), replace the second
   sentence (existing line 68) with the per-response wording below.
3. Run `stale_detector.py` on this document (cite doc files by full leading-slash path).

### Method

Replace existing line 68:

```
Events are ordered by `seq` ascending (insertion order). The page and the total count are fetched under the global DB lock in a single acquisition, so the returned events and `total` form a consistent snapshot; concurrent writes do not affect the result set.
```

with:

```
Events are ordered by `seq` ascending (insertion order). Within a single `/replay` response the events and the `total` count are read under one database-lock acquisition and are internally consistent; consistency is request-local — successive `/replay` requests are not guaranteed to reflect the same state.
```

### Details

- Cite doc files by full leading-slash path so the stale detector skips them in the symbol
  check. The words `total`, `/replay`, and `seq` are prose, not symbols.
- The reword removes the word "snapshot" (REQ-005) and the cross-request implication while
  preserving the accurate single-acquisition per-response fact.

## Compatibility considerations

Purely documentary; no API or behavior change. It clarifies an existing contract.

## Security considerations

None.

## Rollback considerations

Revert the one reworded sentence.

## Validation plan

1. Read `docs/24_eventbus/eventbus_11_replay_endpoint.md` and confirm line 68 now states
   per-response, request-local consistency and no longer says "consistent snapshot".
2. Run `uv run python tools/check_docs_consistency.py --domain eventbus`.
3. Run `uv run python tools/check_docs_structure.py`.
4. Run `stale_detector.py` on this document (must report "not stale").

## Completion criteria

- "Ordering and Consistency" states per-response consistency; "snapshot" wording removed.
- `check_docs_consistency.py --domain eventbus` and `check_docs_structure.py` pass.
- `stale_detector.py` clean.

## Out of Scope

- The DLQ endpoint doc wording (seq 03).
- Any production query or response-shape change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Docs-only edit |
| 2 | Add or update tests per Validation plan | Pending | — | — | No tests for docs change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docs checks named above |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This is the docs deliverable |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261028-122307_ebpage003_pagination-contract-dlq-index.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-231631_ebpage003_pagination-contract-dlq-index.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-094100
- **Related target files**: `docs/24_eventbus/eventbus_11_replay_endpoint.md`
