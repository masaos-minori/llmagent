## Goal

Confirm `tests/agent/test_history_compression_consistency.py` already satisfies its
frozen row (await-contract updates, REQ-004 transition) and that its real-boundary
compression test stays green against the offloaded `TurnPersistence.replace_messages`.
Verification-only unless a failure proves otherwise.

## Scope

- Only `tests/agent/test_history_compression_consistency.py`, current shipped state
  verified:
  - `_TurnBoundaryStub` (L290-302) implements `async def replace_messages` delegating
    to the real session facade — a stub shape, unaffected by the offload.
  - At least one test builds the real boundary (`boundary = await
    session.turn_boundary(conv)`, L394) — this is the test that exercises the offloaded
    path against the patched DB.
- No expected edits.

## Assumptions

- Partially-implemented classification: await-contract updates already covered by
  `implementations/done/20261027-094147_13_tests_agent_test_history_compression_consistency.py.md`
  (turn001, different source plan); this document covers only the post-offload
  verification remainder.
- The real-boundary test relies on `replace_messages` returning the new undo-boundary
  id (`int | None`); `..._02_...` preserves that return through
  `await asyncio.to_thread(...)`.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file.

## Design decisions

- Keep `_TurnBoundaryStub` delegating to the sync facade: it intentionally models the
  non-turn path; forcing it through `TurnPersistence` would change what the
  consistency tests isolate (DB/memory parity, not threading).

## Alternatives considered

- Adding a thread-identity assertion to the real-boundary compression test: rejected —
  REQ-001 proof has its dedicated row (`..._09_...`); this row's frozen scope is
  await-contract only.

## Implementation

### Target file

`tests/agent/test_history_compression_consistency.py`

### Procedure

Run the file after the offload lands; fix only genuine await-contract breaks.

### Method

1. After `..._02_...` is implemented: `uv run pytest tests/agent/test_history_compression_consistency.py`.
2. If the real-boundary test fails on the await/return contract, align only the mock
   or stub shape (keep `async def replace_messages -> int | None`); no assertion
   semantics change.
3. Otherwise no edit.

### Details

- The patched-DB fixture must keep producing a DB the offloaded worker thread can
  open: the repository opens its own connection per call inside the worker, so any
  tmp-path DB file works (no thread-local connection state to smuggle).

## Compatibility considerations

- Execute after `..._02_...` (Plan phase P3 → P5).

## Security considerations

- No changes; test-only file.

## Rollback considerations

- Expected no-diff row; any fix is a single-commit revert.

## Validation plan

- `uv run pytest tests/agent/test_history_compression_consistency.py` green
  post-offload.
- Full validation sequence (`rules/toolchain.md`).

## Completion criteria

- File green against the offloaded boundary with zero edits (or one documented fix).

## Out of Scope

- Compression algorithm semantics.
- Production code in `scripts/agent/conversation_state_manager.py` (`..._04_...`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-085136 | 20261028-085136 | minimal sanctioned test-side fix only: session_and_conn fixture fake conn made thread-agnostic (check_same_thread=False, 1 line); repo-direct fixture left as-is (same-thread calls); production code untouched |
| 2 | Add or update tests per Validation plan | Completed | 20261028-085136 | 20261028-085136 | uv run pytest tests/agent/test_history_compression_consistency.py -q green (15 passed) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-085136 | 20261028-085136 | full suite 10261 passed 8 skipped; diff-cover 100% (shared with ..._02_) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-085136 | 20261028-085136 | out of scope |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| 20261028-003125-13 | 3 | verification | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `tests/agent/test_history_compression_consistency.py`
