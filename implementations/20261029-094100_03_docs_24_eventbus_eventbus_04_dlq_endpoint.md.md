## Goal

State the per-response (request-local) consistency boundary in the DLQ endpoint doc
`docs/24_eventbus/eventbus_04_dlq_endpoint.md`, replacing the current envelope/bounds-only
description with an explicit sentence that `total` and `items` are consistent within one
`/dlq` response and not across requests.

## Scope

Docs-only edit to `docs/24_eventbus/eventbus_04_dlq_endpoint.md`. No production code, no
tests.

## Assumptions

- The current "List DLQ Entries > Behavior" bullets (existing lines 31-33) describe
  `limit`/`offset`, the envelope, and `seq`-ascending order but say nothing about the
  consistency boundary.
- The boundary matches the code: `dlq_list()` computes `total` (`count_dlq`) and the page
  (`fetch_dlq`) inside one `run_with_db_lock` acquisition (`scripts/eventbus/dlq_route.py`;
  cited as reference, not a modification target). Each request takes its own lock, so two
  requests may observe different states.
- This doc is distinct from `eventbus_03_dlq_operations.md` and `eventbus_11_replay_endpoint.md`
  (edited by sibling plans), so no cross-plan wording conflict.

## Design decisions

- Add one bullet to the existing "Behavior" list rather than a new subsection, keeping the
  change minimal and current-behavior-only.

## Alternatives considered

- Adding a dedicated "Consistency" subsection: rejected; the boundary fits naturally as a
  Behavior bullet and the doc already has a separate "Concurrency guarantee" subsection for
  the requeue path.

## Implementation

### Target file

`docs/24_eventbus/eventbus_04_dlq_endpoint.md`

### Procedure

1. Open `docs/24_eventbus/eventbus_04_dlq_endpoint.md`.
2. In the "### Behavior" list under "## List DLQ Entries", add one bullet after the
   existing ordering bullet (existing line 33) stating the per-response consistency
   boundary (text below).
3. Run `stale_detector.py` on this document (cite doc files by full leading-slash path).

### Method

Insert after existing line 33 (`- Items are ordered by event \`seq\` ascending ...`):

```markdown
- Consistency is request-local: within a single `/dlq` response the `total` count and the
  `items` array are read under one database lock and are internally consistent; two
  separate `/dlq` requests are not guaranteed to reflect the same state, because each
  request acquires its own lock.
```

### Details

- Cite doc files by full leading-slash path so the stale detector skips them in the symbol
  check. The words `total`, `items`, and `/dlq` are prose, not symbols.
- The wording states current behavior only; it does not claim a cross-page snapshot (that is
  the out-of-scope cross-page mechanism per UNK-01).

## Compatibility considerations

Purely documentary; no API or behavior change. It clarifies an existing contract without
altering the response shape or ordering.

## Security considerations

None.

## Rollback considerations

Revert the one inserted bullet.

## Validation plan

1. Read `docs/24_eventbus/eventbus_04_dlq_endpoint.md` and confirm the new Behavior bullet
   states per-response, request-local consistency.
2. Run `uv run python tools/check_docs_consistency.py --domain eventbus`.
3. Run `uv run python tools/check_docs_structure.py`.
4. Run `stale_detector.py` on this document (must report "not stale").

## Completion criteria

- The "List DLQ Entries > Behavior" list states the per-response consistency boundary.
- `check_docs_consistency.py --domain eventbus` and `check_docs_structure.py` pass.
- `stale_detector.py` clean.

## Out of Scope

- The replay endpoint doc wording (seq 04).
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
- **Related target files**: `docs/24_eventbus/eventbus_04_dlq_endpoint.md`
