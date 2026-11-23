## Goal

- Create the dispatcher-level concurrency and lease-protection test module that pins exactly-one-execution under 100 concurrent callers and the lease heartbeat behavior (REQ-002 exactly one execution per logical call, REQ-003 lease alive during execution; AC-1, AC-2, AC-4).

## Scope
**Release unit**: dispatcher-decision-change

- Create `tests/mcp_servers/test_mcp_dispatch_concurrency.py` with the T-1 concurrency case and the T-2 heartbeat cases; no other file is modified by this document.

## Assumptions

- Verified this cycle: `tests/mcp_servers/test_mcp_dispatch.py` has no `dispatch_tool`-level concurrency case, and `tests/shared/test_mcp_dedup_concurrency.py` covers only store-level races (`test_100_concurrent_callers_exactly_one_acquired`, `test_multi_process_claim_race_exactly_one_winner`) — the gap the Plan's row 4 records.
- The fixture pattern follows `tests/mcp_servers/test_mcp_dispatch.py::TestDurableDedup` (a class-local `durable` fixture opening a `tmp_path` dedup store via the shared facade and monkeypatching `dispatch._dedup_store`, `_dedup_config`, `_dedup_disabled`, `_dedup_start_state`, clearing `dispatch._duplicate_cache` on teardown); the same `TOOL = "write_file"` (side-effecting, non-retryable by default) and retry-policy injection via `dispatch._tool_retry_policies` apply here.
- T-1 passes against the unmodified dispatcher (today's acquisition already refuses `in_progress`); the Plan's validation table records the lease cases (T-2) as red on the pre-change dispatcher and green after Phases 4-6.
- `_LeaseHeartbeat` is created by the earlier-seq sibling `20261123-205822_02`; the refused-renewal finalization tag `dedup_state="lease_conflict"` is already the dispatcher's shape, pinned by `test_finalize_lease_conflict_surfaces_without_redispatch` (verified this cycle: result not error, handler ran once, row stays `pending`).

## Design decisions

- One process, one event loop, 100 `asyncio.gather` callers (Plan T-1): all contention goes through the store's lease, so the test measures the dispatcher's decision path, not OS scheduling.
- Renewal is observed through a counting wrapper around `store.renew_lease` (monkeypatched on the fixture's store instance) rather than clock-only inference: the heartbeat's existence is proven by a real renewal call during the handler (REQ-003).
- Lease-loss case blocks renewal by making `store.renew_lease` raise `DedupLeaseConflict`, mirroring the existing finalization-conflict test's mechanism, so the assertion is about the dispatcher carrying `renewal_lost` to `lease_conflict` and never re-dispatching (AC-4).

## Alternatives considered

- Extending `tests/mcp_servers/test_mcp_dispatch.py` instead: rejected by the Plan (row 4 creates a separate module) — the concurrency cases need their own short-lease fixtures and would grow a file already near the size gate.
- Multi-process callers at the dispatcher level: rejected — `dispatch_tool` is in-process async; multi-process races are already store-level (`tests/shared/test_mcp_dedup_concurrency.py`).

## Implementation
### Target file
`tests/mcp_servers/test_mcp_dispatch_concurrency.py` (new)

### Procedure
1. Phase 1: create the module (docstring naming the plan file; imports mirroring `tests/mcp_servers/test_mcp_dispatch.py`: `asyncio`, `time`, `pytest`, `typing.Any`, `mcp_servers.dispatch`, the shared dedup facade) with the `durable` fixture and `TestConcurrentDispatch.test_100_concurrent_callers_execute_handler_exactly_once` (T-1): 100 `dispatch_tool({TOOL: handler}, TOOL, {"p": "a"}, idempotency_key="k1")` calls under `asyncio.gather`; assert `len(calls) == 1` and every non-executing result reports `dedup_state in {"in_progress", "duplicate_hit"}` with the `in_progress` ones carrying `error_type="dedup_in_progress"`. Run it against the unmodified dispatcher as the Plan's baseline.
2. Phase 4: add `TestLeaseHeartbeat` (new) with a fixture variant using a short store lease (order of 1-2 seconds):
   - T-2a: the handler sleeps past half the lease; assert `renew_lease` was called at least once during execution (counting wrapper), the final result is a success with `dedup_state == ""`, and the row ends `completed`.
   - T-2b: renewal blocked (wrapper raises `DedupLeaseConflict`), handler sleeps past the whole lease; assert the handler ran exactly once, the result reports `dedup_state == "lease_conflict"` without re-dispatch, and the row is left for reconciliation (mirrors `test_finalize_lease_conflict_surfaces_without_redispatch`).
3. Keep every case deterministic: explicit `idempotency_key`, no reliance on wall-clock sleeps beyond the lease margins the fixture configures, and a per-test `durable` store instance.

### Method
- Handler factories count invocations in a shared list (the `TestDurableDedup._handler(calls)` pattern); assertions read `DispatchResult.is_error` / `error_type` / `dedup_state` only — never ledger internals.
- The fixture injects retry policy the same way the sibling file does (`dispatch._tool_retry_policies = {}` for non-retryable defaults; declared policies for retryable cases), so the concurrency class also proves the non-retryable refusal path under contention.

### Details
- For T-1 the 99 non-executing callers can split between `in_progress` refusals and `duplicate_hit` replays depending on interleaving; the invariant the test pins is exactly one handler execution and refusal/replay for everything else (AC-1).
- For T-2b, block renewal from the first heartbeat tick onward; the dispatcher must still finalize through the normal owner-conditional path so the row stays `pending` for a later reconciliation.

## Compatibility considerations

- New test module only; it imports nothing private from the gate module (everything is exercised through `dispatch_tool`), so the gate's re-export design in sibling `20261123-205822_02` is not a dependency of these tests beyond the dispatcher seam.

## Security considerations

- Tests run against `tmp_path` SQLite stores only; no production store or config is touched, and the suite stays under the `tests/mcp_servers/` conventions enforced by `tests/mcp_servers/conftest.py`.

## Rollback considerations

- Deleting this single new file removes the coverage; no other file references it.

## Validation plan

- Phase 1 baseline: `uv run pytest tests/mcp_servers/test_mcp_dispatch_concurrency.py -q` with only T-1 present (green on the unmodified dispatcher).
- After Phases 4-6 land: the same command green including T-2; recorded red on the pre-change dispatcher for the lease cases (Plan validation table). Delete `.testmondata` first.

## Completion criteria

- The module exists and pins AC-1 (one execution among 100 concurrent callers) and AC-2/AC-4 (renewal observed during the handler; blocked renewal surfaces `lease_conflict` with no re-dispatch).

## Out of Scope

- All source changes (siblings `20261123-205822_01` through `20261123-205822_03`) and the assertion updates in `tests/mcp_servers/test_mcp_dispatch.py` (sibling `20261123-205822_05`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: create the module with T-1 and record the pre-change baseline | Pending | — | — | green pre-change per Plan validation table |
| 2 | Phase 4: add the T-2 heartbeat cases (red until the heartbeat lands) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md` + this document's Validation plan) | Pending | — | — | green after Phases 4-6 |

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
- **Requirement ID**: REQ-002 (exactly one execution per logical call), REQ-003 (lease renewed while the handler runs)
- **Source issue**: issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-205822
- **Related target files**: `tests/mcp_servers/test_mcp_dispatch_concurrency.py`
