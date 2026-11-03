## Goal
- Make every diagnostic SQLite write issued from the async turn-execution path (`DiagnosticStore.save` and its siblings `save_partial_completion`, `save_transport_failure`, `save_serialization_event`) run on a worker thread via `asyncio.to_thread`, while the turn still waits for each write to finish before it proceeds and `DiagnosticStore`'s own synchronous code and SQL stay unchanged.

## Priority
Medium

## Scope
- **In-Scope**:
  - `LLMTurnRunner._handle_llm_error`: offload its three diagnostic writes (`save` for `llm_transport_error`, `save_partial_completion`, `save` for `mid_turn_error`) with `asyncio.to_thread`, awaited in the current order, keeping the existing per-write exception containment.
  - `tool_runner._record_transport_failure`: make the `save_transport_failure` write run off the loop, awaited by `execute_one_tool_call`.
  - The round-level `save_serialization_event` write issued by `tool_run_recorder._record_round_serialization_events` from `tool_runner._execute_with_dag` (a call site the Issue's prose names through the sibling method but its Target Files omit; see Problem).
  - `ToolLoopGuard._save_guard_hint`, reached from the synchronous `check_*` methods: an opt-in deferral mode in which the guard records the hint at the moment of the event and a new awaitable flush persists it on a worker thread, with `LLMTurnExecutor` enabling the mode for the production guard and `LLMTurnRunner` awaiting the flush after each guard check, before the turn proceeds.
  - Tests: an event-loop responsiveness test per offloaded call site using a slow stub, plus ordering and unchanged-default tests.
- **Out-of-Scope**:
  - `DiagnosticStore`'s synchronous implementation, SQL, schema, purge, redaction and encryption (`scripts/agent/diagnostic_store.py` is read-only here); the sensitive-pattern guard itself (diagmask001).
  - Session and tool-message persistence (`scripts/agent/turn_persistence.py` already offloads with `asyncio.to_thread`).
  - `tool_call_state` recorder writes in `_record_pending_state` / `_finalize_state` (workflow.sqlite writes from the same async path, not diagnostic writes; reported in Unknowns UNK-03, not planned here).
  - `llm_transport_errors.py` and `error_injection_service.py`: both call `DiagnosticStore.save` synchronously, but no production caller exists under `scripts/` (only tests call them), so they are not on the turn-execution path.
  - Making the `check_*` methods async, a thread-safe or bounded diagnostic write queue, and any `docs/` change.
- **Dependencies**: The Issue names `issues/20261101-111720_diagstore001_diagnostic-save-crashes-turn.md`, which no longer exists at that path: it is archived at `issues/done/20261101-111720_diagstore001_diagnostic-save-crashes-turn.md`, and its Plan is `plans/done/20261101-120804_diagstore001_diagnostic-save-crashes-turn.md` with procedures under `implementations/done/20261101-122726_*`. diagstore001 is already implemented on master (commit `9a6f41e13`): this Plan builds on its containment and must be implemented against the current source, preserving the per-call `except Exception` containment diagstore001 added in `_handle_llm_error` and `_save_guard_hint`. It did not cover `_record_transport_failure` or the serialization-event write, so those two stay unguarded against `RuntimeError` today; this Plan moves them off the loop without adding containment (see UNK-02). Ordering against active Plans: `plans/20261101-140448_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md` changes only `DiagnosticStore.save`'s guard (no shared target file) and can land in either order, but after it the refusal can fire more often, which this Plan's containment-preserving offload tolerates. Sequencing dependency on `tests/agent/test_tool_runner.py`: `plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md` rewrites shared registry helpers in that file, so implement this Plan's `test_tool_runner.py` additions after it (or rebase onto it); the overlaps with `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` and `plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md` are compatible (Assumptions, Step 8b).

## Background
Found during an adversarial code review of the REPL turn-execution loop against the project rule that `async def` code never introduces blocking I/O. Later re-verification found that assistant and tool-message persistence already moved to `scripts/agent/turn_persistence.py` (writes wrapped in `asyncio.to_thread`) and that `LLMTurnRunner.run()` persists the assistant message through `ctx.turn.persistence_boundary`, so only the diagnostic writes remain. diagstore001 then wrapped the `save()` call sites in `LLMTurnRunner._handle_llm_error` and `ToolLoopGuard._save_guard_hint` against runtime errors; it deliberately left threading to this Issue.

## Problem
`DiagnosticStore.save()` loads config, purges expired rows (a `DELETE` plus commit) and then inserts and commits through `SQLiteHelper("session").open(write_mode=True)`, all synchronously; the SQLite connection helper applies a default `busy_timeout` of 30000 ms, so a locked WAL can stall the calling thread for up to 30 seconds. Verified call sites on the live path, all inside coroutines or called by them:
- `LLMTurnRunner._handle_llm_error` (async): up to two synchronous writes (`save`, `save_partial_completion`) on a partial completion, or one `save` for a mid-turn error.
- `execute_one_tool_call` (async) calls the synchronous `_record_transport_failure`, which calls `save_transport_failure` on a transport-level tool error.
- `_execute_with_dag` (async) calls the synchronous `_record_round_serialization_events`, which calls `save_serialization_event` once per serialization event of the round (not named in the Issue's Target Files; found in Step 2).
- `ToolLoopGuard._save_guard_hint` (static, synchronous) is called from the synchronous `check_cycle`, `_check_progress_stagnation`, `check_dedup`, `check_retry`, `check_empty_result_repeat` and `check_unavailable_repeat`, which `LLMTurnRunner.run()` (async) calls directly through `check_all`, `check_empty_result_repeat` and `check_unavailable_repeat`.
(All checked in Step 2.)

## Reason for Change
Under disk or WAL lock contention these writes stall the whole event loop, delaying the signal-handler callback and the spinner or progress UI. They run on error and guard-trip paths, so the stall is intermittent, which is why the cost is easy to miss and hard to reproduce.

## Implementation Intent
Offload at the async call sites, never inside `DiagnosticStore`: `await asyncio.to_thread(store.save, ...)` keeps the turn waiting for each write (the ordering guarantee) while freeing the loop. For `_handle_llm_error`, `_record_transport_failure` and the serialization-event write this is a direct wrap. For the guard, whose `check_*` methods are synchronous and called from many tests, add a guard-owned deferral: when the guard is built with the deferral mode on, `_save_guard_hint` captures the payload (with its event-time timestamp) into a pending list instead of writing, and an awaitable flush persists the pending hints one at a time on a worker thread, reusing the existing contained persist step. `LLMTurnExecutor` enables the mode for the production guard and `LLMTurnRunner` awaits the flush after each guard check before returning or proceeding, so a hint is still durable before the turn moves on. With the mode off (the default) behavior is exactly as today.

## Requirements
- `REQ-001`: `ToolLoopGuard` gains an opt-in deferral mode (constructor keyword, default off). Off: `check_*` and `_save_guard_hint` behave exactly as today (synchronous write, existing containment and log message). On: a guard event records its payload, timestamp captured at event time, into a pending list and does not write; a new `async` flush method writes the pending hints in recorded order, each through `asyncio.to_thread` and the same contained persist step, and is a no-op without a thread hop when nothing is pending.
- `REQ-002`: `LLMTurnExecutor` builds the production `ToolLoopGuard` with deferral on, and `LLMTurnRunner.run()` awaits the guard's flush after every guard check it makes (`check_all`, `check_empty_result_repeat`, `check_unavailable_repeat`) before it finalizes, returns a `TurnResult`, or continues, so each guard hint is written before the turn proceeds past the check.
- `REQ-003`: `LLMTurnRunner._handle_llm_error` performs each of its diagnostic writes through `asyncio.to_thread`, awaited sequentially in the current order, with the per-write `except Exception` containment and warning log messages unchanged; the returned `TurnResult` and the `stat_partial_completions` update are unchanged.
- `REQ-004`: `tool_runner._record_transport_failure` performs `save_transport_failure` off the loop and `execute_one_tool_call` awaits it at the same point in the sequence (after `audit_tool_exec`, before `guard.observe_availability`); its early-return conditions (non-error, non-transport, no diagnostics) and arguments are unchanged.
- `REQ-005`: The `save_serialization_event` write in `tool_run_recorder._record_round_serialization_events` runs off the loop: the `ctx.stats` bookkeeping stays on the loop thread and the diagnostic write is awaited through `asyncio.to_thread` from `_execute_with_dag`, once per serialization event and in event order, before `_record_round_exec`.
- `REQ-006`: Tests: (a) for each of REQ-001 (flush), REQ-003, REQ-004 and REQ-005, a slow stub for the diagnostic write (blocking the worker thread with a `threading.Event`, never `time.sleep` on the loop) shows a callback scheduled on the loop fires while the write is in flight and that the awaiting coroutine does not complete until the write is released; (b) deferral-off behavior of the guard is unchanged (existing synchronous assertions keep passing); (c) deferral-on records nothing until the flush, preserves order, keeps the event-time timestamp, and contains a `save` failure with the existing warning; (d) `LLMTurnRunner.run()` calls the flush before returning on a guard trip; (e) `LLMTurnExecutor` passes the deferral keyword.
- `REQ-007`: No change to `scripts/agent/diagnostic_store.py` or its tests; existing tests for `llm_turn_runner`, `tool_loop_guard`, `tool_runner`, `llm_turn_executor` and `diagnostic_store` pass unchanged except where a new assertion is added.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/tool_loop_guard.py | Add the opt-in deferral keyword, pending-hint list, event-time payload capture, and the async flush; keep `_save_guard_hint`'s synchronous containment as the persist step | `_save_guard_hint` calls `ctx.diagnostics.save` synchronously from the synchronous `check_*` methods, which an async caller cannot offload without a deferral or async variant | REQ-001, REQ-007 / AC-1, AC-2, AC-7 | `ToolLoopGuard._save_guard_hint` (static, direct `ctx.diagnostics.save` inside `try/except Exception`); six `check_*` methods call it (checked in Step 2) | `tests/agent/test_tool_loop_guard.py` | Verified |
| scripts/agent/llm_turn_executor.py | Pass the deferral keyword where `handle_llm_turn` builds `ToolLoopGuard(self._ctx)` | It is the only production construction site of `ToolLoopGuard`; without it the mode never turns on | REQ-002 / AC-2 | `LlmTurnExecutor.handle_llm_turn` builds the guard and the runner; `rg "ToolLoopGuard\(" scripts` finds only this site (checked in Step 3) | `tests/agent/test_llm_turn_executor.py` | Verified |
| scripts/agent/llm_turn_runner.py | Await the guard flush after each guard check in `run()`; wrap the three diagnostic writes of `_handle_llm_error` in `asyncio.to_thread` | `run()` calls the guard checks synchronously and `_handle_llm_error` calls `save` and `save_partial_completion` directly | REQ-002, REQ-003 / AC-2, AC-3 | `LLMTurnRunner.run` (`check_all`, `check_empty_result_repeat`, `check_unavailable_repeat`), `LLMTurnRunner._handle_llm_error` (three contained synchronous writes); module has no `asyncio` import yet (checked in Step 2) | `tests/agent/test_llm_turn_runner.py` | Verified |
| scripts/agent/tool_runner.py | Make `_record_transport_failure` async and offload its write; await it in `execute_one_tool_call`; await the offloaded serialization-event write in `_execute_with_dag` | Both writes run synchronously inside coroutines; `asyncio` is already imported in this module | REQ-004, REQ-005 / AC-4, AC-5 | `_record_transport_failure` calls `ctx.diagnostics.save_transport_failure`; `execute_one_tool_call` and `_execute_with_dag` are `async def` and call the sync helpers (checked in Step 2) | `tests/agent/test_tool_runner.py` | Verified |
| scripts/agent/tool_run_recorder.py | Split `_record_round_serialization_events` so the `ctx.stats` bookkeeping stays synchronous and the per-event `save_serialization_event` write is a separate synchronous step the async caller can offload | The function mixes loop-thread stats mutation with the blocking diagnostic write | REQ-005 / AC-5 | `_record_round_serialization_events` appends to `ctx.stats.stat_serialization_events` and calls `ctx.diagnostics.save_serialization_event` in one loop (checked in Step 2) | covered by the seq 08 test row | Verified |
| `tests/agent/test_tool_loop_guard.py` | Add deferral-off regression, deferral-on record/flush/order/timestamp/containment tests and the flush responsiveness test | Existing tests assert synchronous `ctx.diagnostics.save` after `check_*`; no test covers deferral or loop responsiveness | REQ-006, REQ-001, REQ-007 / AC-1, AC-6, AC-7 | `TestSaveGuardHintContainment` and the `ctx.diagnostics.save.assert_called_once()` assertions exist (checked in Step 2) | itself | Verified |
| `tests/agent/test_llm_turn_runner.py` | Add responsiveness and ordering tests for `_handle_llm_error` (partial and mid-turn paths) and a test that `run()` awaits the flush before returning on a guard trip | `_handle_llm_error` tests only assert the save calls and containment, with `MagicMock` diagnostics | REQ-006, REQ-002, REQ-003 / AC-2, AC-3, AC-6 | `test_handle_llm_error_*` tests and `_make_ctx` exist (checked in Step 2) | itself | Verified |
| `tests/agent/test_tool_runner.py` | Add responsiveness tests for the transport-failure write and the serialization-event write | The existing serialization-event test asserts the call with a `MagicMock` store only; nothing tests loop responsiveness or `_record_transport_failure` | REQ-006, REQ-004, REQ-005 / AC-4, AC-5, AC-6 | `test_side_effect_calls_diagnostic_save` (asserts `save_serialization_event` called) exists (checked in Step 2) | itself | Verified |
| `tests/agent/test_llm_turn_executor.py` | Add an assertion that `handle_llm_turn` constructs the guard with deferral on | `_run_turn` patches `ToolLoopGuard` without checking constructor arguments | REQ-006, REQ-002 / AC-2 | `_run_turn` patches `agent.llm_turn_executor.ToolLoopGuard` (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/diagnostic_store.py | Synchronous `save` (config load, purge, filter, encrypt, insert) and the three sibling methods; must stay unchanged (Issue constraint), so it is evidence, not a target | REQ-001, REQ-003, REQ-004, REQ-005, REQ-007 |
| scripts/agent/turn_persistence.py | Existing precedent for offloading repository writes with `asyncio.to_thread` using one short-lived connection per call | REQ-001, REQ-003 |
| scripts/db/helper.py | `SQLiteHelper` per-call connection, `check_same_thread=True` default and the 30000 ms default busy timeout, which justify the offload and its thread-safety | REQ-003, REQ-004 |
| scripts/agent/context.py | `AgentContext.diagnostics` is `DiagnosticStore | None`; read-only (also a target of other Plans) | REQ-001 |
| scripts/agent/error_injection_service.py | Sync `save` caller with no production caller; confirms it is not on the turn path | Scope Out-of-Scope |
| scripts/agent/llm_transport_errors.py | Sync `save` / `save_partial_completion` callers with no production caller; confirms it is not on the turn path | Scope Out-of-Scope |
| scripts/agent/workflow/tool_call_state_ops.py | `record_tool_call` / `finalize_tool_call` are synchronous SQLite writes reached from the same async path; evidence for UNK-03 | UNK-03 |
| tests/agent/test_diagnostic_store.py | Existing `DiagnosticStore` tests that must keep passing unchanged | REQ-007 |

## Acceptance Criteria
- AC-1 (REQ-001): With deferral on, a guard trip records no `ctx.diagnostics.save` call until the flush is awaited; the flush performs one `save(session_id, "guard_hint", payload)` per recorded hint, in order, off the loop thread, with the event-time `timestamp`; with deferral off (default) every existing `check_*` assertion on `ctx.diagnostics.save` passes unchanged.
- AC-2 (REQ-001, REQ-002): `handle_llm_turn` builds the guard with deferral on, and on every guard trip in `LLMTurnRunner.run()` the hint's `save` has completed before `run()` returns the `TurnResult` or calls `_finalize_after_guard`.
- AC-3 (REQ-003): In `_handle_llm_error` no diagnostic write executes on the event-loop thread; each write completes before the next and before the `TurnResult` is returned; a `RuntimeError` or `sqlite3.Error` from a write still degrades to the existing warning and the same `TurnResult`.
- AC-4 (REQ-004): A transport-level tool error persists through `save_transport_failure` off the loop thread, completing before `guard.observe_availability` runs; other results do not touch diagnostics.
- AC-5 (REQ-005): `save_serialization_event` runs off the loop thread, once per serialization event in order, and `ctx.stats.stat_serialization_events` is still appended on the loop thread with the same entries.
- AC-6 (REQ-006): For each of AC-1, AC-3, AC-4, AC-5, a callback scheduled with `loop.call_soon`/`call_later` fires while the slow stubbed write is still blocked, and the awaiting coroutine finishes only after the write is released.
- AC-7 (REQ-007): `git diff` shows no change to `scripts/agent/diagnostic_store.py`; the existing tests of the five test modules named in Tests pass.

## Tests
- REQ-006(a) responsiveness: in `tests/agent/test_tool_loop_guard.py`, `tests/agent/test_llm_turn_runner.py` and `tests/agent/test_tool_runner.py`, stub the diagnostic method with a function that blocks on a `threading.Event`; start the awaiting coroutine as a task, schedule a loop callback and assert it ran before the event is set, then set it and assert the task completes. The stub MUST block the worker thread only; a stub that blocks the loop thread would make the assertion vacuous.
- REQ-006(b)(c) guard modes in `tests/agent/test_tool_loop_guard.py`: default off keeps the existing synchronous tests; deferral on records nothing before the flush, preserves order across several hints, keeps the captured timestamp, contains a `save` exception with the `kind=guard_hint` warning, and a flush with nothing pending returns without calling `asyncio.to_thread`.
- REQ-006(d) in `tests/agent/test_llm_turn_runner.py`: a guard trip through `run()` with a deferral-on guard asserts the flush ran before the `TurnResult`; `_handle_llm_error` ordering for the partial path (`save`, then `save_partial_completion`, both before return).
- REQ-006(e) in `tests/agent/test_llm_turn_executor.py`: the patched `ToolLoopGuard` is called with the deferral keyword on.
- REQ-004/REQ-005 in `tests/agent/test_tool_runner.py`: transport-error result off-loop write and observe-after-write ordering; serialization-event write off-loop with stats appended on the loop thread.
- Regression (REQ-007): `uv run pytest tests/agent/test_llm_turn_runner.py tests/agent/test_tool_loop_guard.py tests/agent/test_tool_loop_guard_wiring.py tests/agent/test_tool_runner.py tests/agent/test_llm_turn_executor.py tests/agent/test_diagnostic_store.py tests/agent/test_diagnostic_store_security.py tests/agent/test_orchestrator.py tests/agent/test_turn_persistence.py` where present.

## Documentation Impact
N/A: no `docs/*.md` page describes the concurrency of these writes. `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md` (section "Hints on Guard Triggering") says only that a hint is saved to `session_diagnostics` with `kind='guard_hint'`, which stays true; the generated reference lists `ToolLoopGuard` at class level only. After the code change run `uv run python tools/generate_reference_table.py --check` per `routing.md` Tools to confirm no drift (REQ-001, REQ-002).

## Assumptions
- Offloading with `asyncio.to_thread` is safe for `DiagnosticStore`: each write opens its own short-lived `SQLiteHelper` connection inside the worker thread and closes it there (`check_same_thread=True` default is respected), the same pattern `turn_persistence.py` already uses; ConfigLoader use inside `save` from a worker thread is not separately verified (UNK-01, non-blocking).
- The opt-in deferral keyword (default off) is the smaller option than making the `check_*` methods async: about 64 synchronous `check_*` call sites across `tests/agent/test_tool_loop_guard.py`, `tests/agent/test_orchestrator.py`, `tests/integration/test_robustness_chaos.py`, `tests/integration/test_orchestrator_integration.py` and `tests/integration/test_rag_llm_integration.py` would otherwise change (checked in Step 2). Rejected alternatives are recorded in Design.
- Step 8b: `tools/check_plan_target_overlaps.py` names this Plan for two files, both judged compatible. `scripts/agent/tool_runner.py` is also targeted by `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md`, which sets a side-effect flag before a non-READ call in the dispatch path; this Plan edits `_record_transport_failure`, `execute_one_tool_call` and `_execute_with_dag` for diagnostic writes, a different concern in disjoint functions. `tests/agent/test_tool_runner.py` is also targeted by wfretry001 (flag tests), `plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md` (a logging test) and `plans/20261101-142029_toolarg001_tool-validation-fails-open-empty-schema.md` (fixture schema in three shared registry helpers); this Plan only adds new test functions. Because the new tests may reuse those helpers, implement after toolarg001 when both are pending, or rebase onto it; no fix order is otherwise required.
- Own check of archived and procedure documents: files in `plans/done/` and `implementations/done/` that mention the target paths are completed work, including the diagstore001 Plan and its four procedures (`implementations/done/20261101-122726_01..04_*`); `implementations/` holds no active procedure, so no active procedure overlaps this Plan.
- The guard's `check_all` hint writes are rare (guard trips) and sequentially flushed hints are acceptable; no batching is needed.
- diagstore001 is treated as merged: `git log` shows its fix commit `9a6f41e13` on master and the current call sites carry its containment.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `ConfigLoader().load("agent.toml")` (called inside `DiagnosticStore.save` via `_load_diagnostics_config`) is safe to run from a worker thread concurrently with loop-thread reads | `ConfigLoader` has class-level restrict/reset hooks; thread-safety of its load path was not read in full (Needs confirmation) | During implementation read `scripts/shared/config_loader.py`'s load path; if unsafe, serialize via a lock at the offload site, still without touching `diagnostic_store.py` | False |
| UNK-02 | Whether the owner wants `save_transport_failure` and the serialization-event write contained against `RuntimeError` like the guard and LLM-error sites (diagstore001 left them out, so a sensitive-pattern refusal there still propagates from the async path) | Owner decision; diagstore001's Plan scoped containment to two call sites | Out of this Plan's scope: record as a follow-up Issue if wanted; the offload here neither adds nor removes the propagation | False |
| UNK-03 | Whether the `tool_call_state` recorder writes (`_record_pending_state`, `_finalize_state` calling `record_tool_call` / `finalize_tool_call`) block the loop the same way | Not verified at runtime; the helpers are synchronous SQLite `execute` + `commit` and the callers are in the async dispatch path, but the production recorder's threading was not traced (Needs confirmation) | Owner decides whether to file a separate Issue; not part of this Plan (different database and data, not diagnostic) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/tool_loop_guard.py | Modify | Medium (one production construction site, about 64 test call sites of `check_*` that must stay green) | 5 commits | N/A | not applicable (rsynced) |
| scripts/agent/llm_turn_executor.py | Modify | Low | 2 commits | N/A | not applicable (rsynced) |
| scripts/agent/llm_turn_runner.py | Modify | High (every LLM turn passes through `run`; `run` is already complexity C(15)) | 7 commits | N/A | not applicable (rsynced) |
| scripts/agent/tool_runner.py | Modify | High (every tool call passes through it) | 11 commits | N/A | not applicable (rsynced) |
| scripts/agent/tool_run_recorder.py | Modify | Low (one caller, `_execute_with_dag`) | 1 commit | N/A | not applicable (rsynced) |
| tests/agent/test_tool_loop_guard.py | Modify | Low | 6 commits | N/A | None: tests are not deployed |
| tests/agent/test_llm_turn_runner.py | Modify | Low | 9 commits | N/A | None: tests are not deployed |
| tests/agent/test_tool_runner.py | Modify | Medium (shared by three other Frozen Plans) | 12 commits | N/A | None: tests are not deployed |
| tests/agent/test_llm_turn_executor.py | Modify | Low | 1 commit | N/A | None: tests are not deployed |

## Design
Path B. Classification record: nine target files (more than three), so Path B; architecture checks: `lint-imports` (uv run) reports 6 contracts kept, 0 broken, and the change adds no import across a contract boundary (`asyncio` only; `agent.tool_loop_guard` gains no new module import). Dependency graph: `ToolLoopGuard` is constructed only in `scripts/agent/llm_turn_executor.py`; its `check_*` callers in `scripts/` are only `LLMTurnRunner.run()`; the writers' callers in the turn path are the four sites listed in Problem. Historical analysis: 30-day churn above; every source target has one effective owner.

Design decisions (python-design applied narrowly):
- D1 Where the offload lives. Alternatives: (a) async methods on `DiagnosticStore`, rejected because the Issue forbids changing it and diagmask001 is editing it; (b) wrap at the async call sites with `asyncio.to_thread(store.method, ...)`, chosen for the three direct sites; (c) a fire-and-forget thread, rejected because it breaks the Issue's ordering guarantee.
- D2 The guard. Alternatives: (a) async `check_*`, rejected for the test-churn above and because `check_*` also run the cheap pure scans; (b) always-on pending queue, rejected because every existing assertion of a synchronous `save` after `check_*` would need an added flush; (c) opt-in deferral keyword with an awaited flush, chosen: smallest change that keeps all current tests valid and gives the production path the offload. Cost: a second mode; mitigated by the executor test (REQ-006(e)) and the Risk below. The deferral stores the payload, not a closure, with the timestamp from the event so persisted `timestamp` fields do not shift by the flush delay.
- D3 Flush placement. `check_all` runs before `await ctx.conv.append_message(message)`; the flush is awaited immediately after each check and before `_finalize_after_guard` or the returned `TurnResult`, so the Issue's constraint (a save completes before the turn proceeds) holds. To keep `run()` from growing past its current complexity grade, the implementation should add one small private async helper in `llm_turn_runner.py` that flushes and returns the message, rather than three inline branches.
- D4 Serialization events. The stats bookkeeping must stay on the loop thread (it mutates `ctx.stats`); only the per-event `save_serialization_event` call goes to the worker, awaited in event order so the persisted order is unchanged.
- D5 Compatibility. No public API, schema or config change; `ToolLoopGuard`'s new keyword defaults to off; `_record_transport_failure` becomes a coroutine, and `rg "_record_transport_failure" scripts tests` shows only `execute_one_tool_call` calls it (checked in Step 3).

## Implementation steps
1. **Phase 1: Tests first (red)**
   - [ ] Add the guard deferral and flush tests, including the off-loop responsiveness test (REQ-001, REQ-006; tests/agent/test_tool_loop_guard.py).
   - [ ] Add the `_handle_llm_error` responsiveness/ordering tests and the `run()` flush-ordering test (REQ-002, REQ-003, REQ-006; tests/agent/test_llm_turn_runner.py).
   - [ ] Add the transport-failure and serialization-event responsiveness tests (REQ-004, REQ-005, REQ-006; tests/agent/test_tool_runner.py).
   - [ ] Add the executor keyword assertion (REQ-002, REQ-006; tests/agent/test_llm_turn_executor.py).
2. **Phase 2: Guard deferral**
   - [ ] Add the deferral keyword, pending list, event-time payload capture and async flush, keeping the synchronous persist as the contained step (REQ-001, REQ-007; scripts/agent/tool_loop_guard.py).
   - [ ] Enable deferral for the production guard (REQ-002; scripts/agent/llm_turn_executor.py).
3. **Phase 3: Call-site offload**
   - [ ] Offload the `_handle_llm_error` writes and await the guard flush after each guard check in `run()` (REQ-002, REQ-003; scripts/agent/llm_turn_runner.py).
   - [ ] Make `_record_transport_failure` async and await it in `execute_one_tool_call` (REQ-004; scripts/agent/tool_runner.py).
   - [ ] Split the serialization-event recorder and await the offloaded write in `_execute_with_dag` (REQ-005; scripts/agent/tool_run_recorder.py, scripts/agent/tool_runner.py).
4. **Phase 4: Deployment & Verification**
   - [ ] Run the Validation plan sequence and the regression set (REQ-007; all targets); confirm `scripts/agent/diagnostic_store.py` is unchanged.
   - [ ] Deploy hand-off: the change must be committed and pushed first; deploying is the user's decision under `skills/deploy/SKILL.md` (approval gate), which rsyncs `scripts/` per `deploy.sh`.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/tool_loop_guard.py, tests/agent/test_tool_loop_guard.py | Unit: deferral modes, flush, responsiveness | `uv run pytest tests/agent/test_tool_loop_guard.py tests/agent/test_tool_loop_guard_wiring.py` | New and existing tests pass |
| scripts/agent/llm_turn_runner.py, scripts/agent/llm_turn_executor.py | Unit: off-loop writes, flush-before-return, executor keyword | `uv run pytest tests/agent/test_llm_turn_runner.py tests/agent/test_llm_turn_executor.py` | Pass |
| scripts/agent/tool_runner.py, scripts/agent/tool_run_recorder.py | Unit/Integration: transport-failure and serialization-event offload | `uv run pytest tests/agent/test_tool_runner.py tests/agent/commands/test_cmd_mcp.py` | Pass |
| DiagnosticStore and guard consumers | Regression | `uv run pytest tests/agent/test_diagnostic_store.py tests/agent/test_diagnostic_store_security.py tests/agent/test_orchestrator.py tests/integration/test_robustness_chaos.py` | Pass, no edits to those files |
| Project gates | Format/lint/type/arch/security/coverage | `rules/toolchain.md` sequence; `uv run radon cc scripts/agent/llm_turn_runner.py -s -n C` (no new grade C/worse than the current `run` C(15)); `uv run python tools/generate_reference_table.py --check`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | All pass; baseline at planning time: diff-cover not run (no diff yet; the 90% changed-line threshold applies after implementation), radon grades recorded above, vulture reports only pre-existing unused-variable findings elsewhere, bandit on `scripts/agent` reports 29 Low and no Medium/High findings (pre-existing) |

## Risks
- **Risk**: The deferral mode leaves two behaviors in `ToolLoopGuard`; a future construction site that omits the keyword would silently keep the blocking write (likelihood: low, one construction site today). → **Mitigation**: the executor test (REQ-006(e)) pins the production wiring, and the keyword's docstring names the blocking trade-off.
- **Risk**: A hint recorded but never flushed (an exception between the check and the flush) would be lost. → **Mitigation**: flush immediately after each check with no awaited work in between; the loss is limited to a best-effort diagnostic, the same class of loss diagstore001 already accepts.
- **Risk**: `LLMTurnRunner.run` is already complexity grade C(15); three inline flush branches would worsen it. → **Mitigation**: one private async helper (Design D3) and the `radon cc ... -n C` check in the Validation plan.
- **Risk**: A worker-thread write can outlive a cancelled turn (`asyncio.CancelledError` during `await asyncio.to_thread`), leaving a diagnostic row written after the turn aborted. → **Mitigation**: acceptable for best-effort diagnostics; the write is a single complete insert, never a partial row.
- **Risk**: Concurrent loop-thread and worker-thread SQLite access to the session database could add `SQLITE_BUSY` waits. → **Mitigation**: WAL mode and the 30000 ms busy timeout apply to every connection, `turn_persistence.py` already runs repository writes the same way, and the waits now block only the worker.
- **Risk**: Edits to `tests/agent/test_tool_runner.py` collide with other Plans that touch the same file. → **Mitigation**: add-only test additions (new test functions), no edits to shared helpers.
- **Risk** (added 20261103, procedure-cycle verification): `scripts/agent/tool_runner.py` measures 20444 B against the 20480 B `check_module_size.py` gate — only 36 B of headroom. The `async def`/`await`/`asyncio.to_thread` changes are estimated at +40–70 B and can push the file over the gate; `plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md` adds a further ~200 B to the same file. → **Mitigation**: keep the `tool_runner.py` diff minimal (the per-event `asyncio.to_thread` glue lives in `tool_run_recorder.py`; only the `await` at the `_execute_with_dag` call site lands in `tool_runner.py`); measure `uv run python tools/check_module_size.py` after the edits; if the gate fails, record a Blocker in the procedure document and the owner decides between a `--update-baseline` approval and a separate `tool_runner.py` split Plan before either Plan merges.
- **Risk**: `_record_transport_failure` and `_record_round_serialization_events` remain unguarded against `RuntimeError` (diagstore001 did not cover them). → **Mitigation**: unchanged by this Plan and routed to UNK-02; the offload preserves the exception because `await asyncio.to_thread` re-raises it in the awaiting coroutine.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: guard deferral, `_handle_llm_error`, tool-runner offload and executor wiring tests (tests/agent/test_tool_loop_guard.py, tests/agent/test_llm_turn_runner.py, tests/agent/test_tool_runner.py, tests/agent/test_llm_turn_executor.py) | Completed | — | 20261103-182304 | Red-first test procedures covered by the seq 01/02/03 companion sections and the seq 08 document |
| 2 | Guard deferral and executor enablement (scripts/agent/tool_loop_guard.py, scripts/agent/llm_turn_executor.py) | Completed | — | 20261103-182304 | Procedures 20261103-113432_01/_02 generated |
| 3 | Call-site offload: `_handle_llm_error` and guard flush, `_record_transport_failure`, serialization-event write (scripts/agent/llm_turn_runner.py, scripts/agent/tool_runner.py, scripts/agent/tool_run_recorder.py) | In Progress | — | — | Procedures 20261103-113432_03/_04/_05 generated; size-gate contingency recorded in the plan Risks |
| 4 | Deployment and verification: validation sequence, regression set, deploy hand-off (all targets) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261103-113432_01_scripts_agent_tool_loop_guard.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261103-113432_02_scripts_agent_llm_turn_executor.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261103-113432_08_tests_agent_test_tool_runner.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261103-113432_05_scripts_agent_tool_run_recorder.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261103-113432_04_scripts_agent_tool_runner.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261103-113432_03_scripts_agent_llm_turn_runner.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180333_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-143807
- **Related target files**: scripts/agent/tool_loop_guard.py, scripts/agent/llm_turn_executor.py, scripts/agent/llm_turn_runner.py, scripts/agent/tool_runner.py, scripts/agent/tool_run_recorder.py, tests/agent/test_tool_loop_guard.py, tests/agent/test_llm_turn_runner.py, tests/agent/test_tool_runner.py, tests/agent/test_llm_turn_executor.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 2 (async path for `_save_guard_hint`); `_save_guard_hint` sync write | scripts/agent/tool_loop_guard.py | Step 2 | AC-1, AC-7 | tests/agent/test_tool_loop_guard.py | Confirmed by repository evidence |
| REQ-001 | Same | tests/agent/test_tool_loop_guard.py | Step 1 | AC-1, AC-6 | `uv run pytest tests/agent/test_tool_loop_guard.py` | Confirmed by repository evidence |
| REQ-002 | Issue Implementation Intent (async path at the call sites); sole construction site in `llm_turn_executor.py` | scripts/agent/llm_turn_executor.py | Step 2 | AC-2 | tests/agent/test_llm_turn_executor.py | Derived from confirmed evidence |
| REQ-002 | Issue Constraints (save completes before the turn proceeds) | scripts/agent/llm_turn_runner.py | Step 3 | AC-2 | tests/agent/test_llm_turn_runner.py | Explicit in issue |
| REQ-002 | Same | tests/agent/test_llm_turn_executor.py | Step 1 | AC-2 | `uv run pytest tests/agent/test_llm_turn_executor.py` | Derived from confirmed evidence |
| REQ-003 | Issue Required Changes 1; `_handle_llm_error` direct writes | scripts/agent/llm_turn_runner.py | Step 3 | AC-3 | tests/agent/test_llm_turn_runner.py | Confirmed by repository evidence |
| REQ-003 | Same | tests/agent/test_llm_turn_runner.py | Step 1 | AC-3, AC-6 | `uv run pytest tests/agent/test_llm_turn_runner.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes 1; `_record_transport_failure` direct write | scripts/agent/tool_runner.py | Step 3 | AC-4 | tests/agent/test_tool_runner.py | Confirmed by repository evidence |
| REQ-004 | Same | tests/agent/test_tool_runner.py | Step 1 | AC-4, AC-6 | `uv run pytest tests/agent/test_tool_runner.py` | Confirmed by repository evidence |
| REQ-005 | Issue Summary names `save_serialization_event`; call site found in `tool_run_recorder.py` | scripts/agent/tool_run_recorder.py | Step 3 | AC-5 | tests/agent/test_tool_runner.py | Derived from confirmed evidence |
| REQ-005 | Same | scripts/agent/tool_runner.py | Step 3 | AC-5 | tests/agent/test_tool_runner.py | Derived from confirmed evidence |
| REQ-005 | Same | tests/agent/test_tool_runner.py | Step 1 | AC-5, AC-6 | `uv run pytest tests/agent/test_tool_runner.py` | Derived from confirmed evidence |
| REQ-006 | Issue Required Changes 3, Acceptance Criteria 2, Testing Expectations | tests/agent/test_tool_loop_guard.py | Step 1 | AC-6 | `uv run pytest tests/agent/test_tool_loop_guard.py` | Explicit in issue |
| REQ-006 | Same | tests/agent/test_llm_turn_runner.py | Step 1 | AC-6 | `uv run pytest tests/agent/test_llm_turn_runner.py` | Explicit in issue |
| REQ-006 | Same | tests/agent/test_tool_runner.py | Step 1 | AC-6 | `uv run pytest tests/agent/test_tool_runner.py` | Explicit in issue |
| REQ-006 | Same | tests/agent/test_llm_turn_executor.py | Step 1 | AC-2 | `uv run pytest tests/agent/test_llm_turn_executor.py` | Derived from confirmed evidence |
| REQ-007 | Issue Constraints (do not change `DiagnosticStore`), Out of Scope | scripts/agent/tool_loop_guard.py | Step 4 | AC-7 | regression set in Validation plan | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261103-113432 -->