## Goal

Make one tool round answer every `tool_call` id it declared, whether the round
completed normally or failed by raising (`REQ-001`, `REQ-003`). Today
`execute_all_tool_calls()` (`scripts/agent/tool_runner.py:347-391`) collects rows
only from the results it managed to gather, so an exception escaping the round
leaves the persisted assistant `tool_calls` block with zero answers. This row
gives the round its own owned map of "answered" ids, records each real result at
the point it exists, synthesizes one row per still-unanswered declared id at the
end of the round (normal or exceptional), and threads a mid-round guard stop
through the engines so a trip ends the remaining work (`REQ-002`, `REQ-006`).

## Scope

Internal restructure of `scripts/agent/tool_runner.py` only. Public contract
unchanged: `execute_all_tool_calls(ctx, tool_calls, turn, out_failed_keys)` keeps
its `-> None` return and raises exactly what it raises today (`REQ-008`). The
changes are confined to `execute_all_tool_calls` and the three private engines it
calls (`_execute_with_dag`, `_run_plan_batches`, `_run_group_calls`), plus a new
per-call recording wrapper. Reference reads: `scripts/agent/tool_result_pairing.py`
(the synthesis, this row does not create), `scripts/agent/tool_loop_guard.py`
(the scan this row consults, this row does not extract), `scripts/agent/tool_preparation.py`
(already-answered path), `scripts/agent/session_message_repo.py` (`save_many`).
Dependent tests: `tests/agent/test_tool_runner.py`, `tests/agent/test_tool_result_pairing.py`.

## Assumptions

- `collected: dict[str, tuple]` keyed by `tool_call_id` is a complete definition
  of "answered": the only paths that produce a row for a declared id are the group
  engines (`tool_runner.py:69-74`), the preparation-failure merge (`:384`), and
  `_build_denied_messages()` (`:412-428`) (`ASSUM-03`, `REQ-010`).
- Recording a result in a per-call wrapper inside `_run_group_calls()` preserves
  completed results across a `gather` failure without changing `gather`
  semantics (`ASSUM-02`); the residual `gather`-cancellation window is bounded by
  `UNK-02` and removed by `tool003`.
- The declared id set read before execution cannot move even if preparation,
  approval, planning, or execution fails (`REQ-003`), because it is taken from the
  `tool_calls` argument at the top of the function.
- Phase 2's mid-round stop consumes the guard instance `LLMTurnRunner` already
  owns, reached through the explicit parameter the tool001 plan
  (`plans/20261022-092413_plan.md`) adds to `execute_all_tool_calls` and
  `execute_one_tool_call`; that plan deletes the `getattr(ctx, "guard", None)`
  read at `:201` this row would otherwise have to keep.

## Design decisions

- **DR-001 — the round owns `collected`.** `execute_all_tool_calls` is the only
  function that holds the declared set for a round (`:349`), and `tool_call_id` is
  already the key every write path uses (`:221`, `:427`, `session_message_repo.py:91-104`).
  The pairing is `declared − answered`; a failure and a skipped call become the
  same observable fact — a declared id not in the map — and one code path answers
  both. A later `tool001` mid-round decision or a `tool003` change adds a call
  site or a payload, not a new owner.
- **DR-005 — synthesized rows bypass stats, `out_failed_keys`, and
  `record_tool_result`, and join the existing single `save_many()` batch in
  declared order.** They flow outside `_collect_tool_result_msgs` (which would
  inflate `stat_tool_errors` and add hash keys to `failed_calls`) and outside
  `record_tool_result` (which feeds the empty-result guard). Only storage gains
  the missing rows; guard and stats behavior is identical to HEAD.

## Alternatives considered

- Inline synthesis in `tool_runner.py` (15526 B, no baseline, needs a session
  fixture to test) or in `tool_loop_guard.py` (wrong owner: the guard decides
  whether to stop, not what a result says) — rejected by `DR-003`; the synthesis
  lives in `scripts/agent/tool_result_pairing.py`.
- Returning the missing ids to the turn loop instead of synthesizing here — the
  runner does not know which ids the planner executed, and the tool001 plan
  already rejected an `out_partial_results`-style parameter (`DR-001`).

## Implementation

### Target file

`scripts/agent/tool_runner.py`

### Procedure

Apply in this order. Every edit is internal; no signature above
`execute_all_tool_calls` changes except adding the private `collected`/`guard`
parameters to the three engines.

1. **Read the declared ids once, before anything else (`REQ-003`).** At the top
   of `execute_all_tool_calls()`, immediately after the `if not tool_calls:`
   early return (`:364-366`), compute `declared_ids` as the ordered list of
   `tc["id"]` over `tool_calls`. Do this before `prepare_tool_calls()` (`:369`),
   `_run_approval_gate()` (`:372`), and `_execute_with_dag()` (`:375`) so a
   preparation or approval failure cannot move the set.
2. **Create the round-owned map (`DR-001`).** Declare `collected: dict[str,
   tuple] = {}` in `execute_all_tool_calls()` and thread it into
   `_execute_with_dag(ctx, approved_calls, force_serial=..., collected=collected)`.
   Add a `collected` parameter to `_execute_with_dag` (`:301`), `_run_plan_batches`
   (`:274`), and `_run_group_calls` (`:63`), passing it straight through.
3. **Record each real result at the point it exists (`REQ-002`).** Add a module
   helper `_recorded_call(ctx, pc, collected)` that awaits
   `execute_one_tool_call(ctx, pc)`, stores the returned 6-tuple in
   `collected[pc.call_id]` before returning it, and returns the tuple unchanged.
   Use it in both group shapes in `_run_group_calls()`: the sequential loop
   (`:71-73`) and the gathered call site (`:74`). `execute_one_tool_call` itself
   is not modified — it keeps returning the same 6-tuple (`:184`), so the
   tool001 call-site migration is not re-opened.
4. **Consult the mid-round scan on a trip (`REQ-006`, Phase 2).** In the
   sequential path of `_run_group_calls()`, after each recorded result, run the
   non-recording scan and `break` on a trip so no further call of that group runs.
   In `_run_plan_batches()`, after each batch's `gather` completes, run the scan
   and `break` so no further batch is dispatched. The scan is passed in through a
   `guard` parameter threaded from `execute_all_tool_calls` (the tool001 plan's
   parameter); see Method. The scan writes nothing (`REQ-007`).
5. **Preserve original-order merge and ordering (`REQ-009`, `REQ-010`).** Keep
   `call_order = {tc["id"]: i for i, tc in enumerate(tool_calls)}` (`:383`) and
   `results = list(results) + list(prep_failures); results.sort(...)` (`:384-385`)
   unchanged. `_collect_tool_result_msgs` (`:187-222`) keeps building rows for
   real results only — never for synthesized rows.
6. **Run the completion/pairing step (`REQ-001`, `REQ-012`).** After the
   execution step, before or at the existing `save_many()` site (`:391`), call
   `pair_round_results(declared_ids, answered_ids, collected, reason)` where
   `answered_ids = {ids in collected} ∪ {prep ids} ∪ {denied_ids}` and `reason`
   is the round's stop reason. Merge its returned `(LLMMessage, tool_msg)` pairs
   into the existing `extend_messages()` + `save_many()` path exactly as
   `_build_denied_messages` output is merged (`:388-391`): extend history with the
   `LLMMessage` half, extend `tool_msgs` with the tuple half, then one
   `ctx.session.save_many(tool_msgs)`. Synthesized rows are appended in declared
   order alongside the denied rows.
7. **Re-raise when the round raised (`REQ-008`).** Wrap the round body so that on
   an escaping exception the pairing step still runs (to answer the ids that did
   complete) and then the original exception propagates unchanged. Do not add any
   new `except` clause that swallows; use `try/finally` around the execution and
   pairing so the write happens and the raise is preserved. `llm_turn_runner.py`
   is not edited.
8. **Keep the `KeyError` at `:383` (`REQ-011`).** An id-less declared call still
   raises `KeyError` from `tc["id"]`; this row does not duplicate, move, or mask
   it.

### Method

- Edit-based, surgical. Thread `collected` as a new keyword parameter through the
  three private engines; thread `guard` (the tool001 parameter) the same way for
  Phase 2. Add `_recorded_call` as a module-level `async` helper next to
  `_execute_prepared_call`. Import `pair_round_results` from
  `agent.tool_result_pairing` and `ToolCallStopReason` from `agent.tool_enums`
  at the top of `tool_runner.py`.
- The completion step must run on both normal completion and exceptional
  completion identically; a `try/finally` around the execution+pairing block is
  the position that guarantees this without swallowing.

### Details

- `collected` holds the real 6-tuples `execute_one_tool_call` returns, keyed by
  `pc.call_id` (`tool_runner.py:184`).
- `pair_round_results` returns pairs shaped like `_build_denied_messages`
  (`:419-427`): `LLMMessage(role="tool", tool_call_id=id, content=payload)` and
  `("tool", payload, None, id)`. It does NOT pass through
  `_update_stats_for_result()` (`:225-237`) or `record_tool_result()`.
- One `save_many()` per round (`:391`), unchanged (`REQ-012`).
- If `tool_runner.py` crosses the 16384 B gate while `collected` is threaded
  (UNK-05), move the completion step into `scripts/agent/tool_result_pairing.py`;
  do not add a baseline and do not widen this Plan.

## Compatibility considerations

- No public signature change above `execute_all_tool_calls`; its parameter list
  and `-> None` are unchanged (`REQ-008`, AC-4). The three private engines gain
  parameters but are called only internally.
- The exception a failing round raises today still propagates unchanged; the two
  turn-level check sites (`llm_turn_runner.py:98-105`, `:122-130`) and
  `_finalize_after_guard` are untouched.
- Existing answered paths (preparation failures, approval denials) are never
  synthesized twice (`REQ-010`); their rows are byte-identical.

## Security considerations

- N/A: no auth, secret, permission, or policy change. A synthesized row states
  "not executed"; it does not bypass the approval gate or execute anything.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/tool_runner.py` restores
  HEAD. Reversible; touches no config, DB schema, or service port.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_result_pairing.py -q --timeout=120`
  after Phase 1 and again after Phase 2 — all pass.
- AC-1/AC-2: a round forced to fail by each exception class in the Problem table
  leaves, for every declared `tool_call_id`, exactly one `role='tool'` row
  readable through `ctx.session.fetch_messages()` and exactly one matching entry
  in `ctx.conv.history`, and the original exception still propagates.
- AC-3: `TestExecutorUnavailableGuard` (`tests/agent/test_tool_runner.py:1155-1166`)
  and `TestGatewayBypassPreflightDenial` (`:1169-1175`) keep asserting the raise;
  the order test at `:1034` passes unchanged.
- AC-4: `grep -n "except" scripts/agent/llm_turn_runner.py` shows only the
  pre-existing handler at `:86` and the one inside `_finalize_after_guard`;
  `grep -n "def execute_all_tool_calls" -A6 scripts/agent/tool_runner.py` shows the
  same parameter list and `-> None`.
- `uv run ruff check scripts/`, `uv run ruff format --check scripts/`,
  `uv run mypy scripts/ --config-file scripts/mypy.ini` (no new error, no new
  `# type: ignore`), `uv run python tools/check_module_size.py --top 5` (no new
  violation, no new baseline).

## Completion criteria

`execute_all_tool_calls` reads the declared ids before execution, owns `collected`,
records each real result at the production point in both group shapes, runs the
pairing step on normal and exceptional completion alike, merges synthesized rows
into the single `save_many()` batch in declared order, and re-raises the original
exception; every declared id has exactly one persisted `role='tool'` row; the
raise assertions and the order contract are unchanged; no new lint, type, size,
or import finding.

## Out of Scope

- Extracting the scan (`tool_loop_guard.py`) — row 4.
- The new pure synthesis module and enum — rows 2/3.
- The guard parameter plumbing — the tool001 plan's row
  (`plans/20261022-092413_plan.md:180`).
- `asyncio.gather` without `return_exceptions=True` (`tool_runner.py:74`, `:291-296`)
  — `tool003`. The `KeyError` from `tc["id"]` at `:383` — `tool004`.
- `scripts/agent/llm_turn_runner.py`, `scripts/agent/llm_turn_executor.py`,
  `scripts/agent/session_message_repo.py` — not edited.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read declared ids, own `collected`, thread through engines, record at production point (REQ-002, REQ-003) | Pending | — | — | Phase 1 |
| 2 | Run pairing step on normal and exceptional completion; merge into single save_many in declared order (REQ-001, REQ-009, REQ-012) | Pending | — | — | Phase 1 |
| 3 | Re-raise original exception; preserve KeyError at :383; keep answered paths unsynthesized (REQ-008, REQ-010, REQ-011) | Pending | — | — | Phase 1 |
| 4 | Consult mid-round scan after each recorded result / batch; break on trip (REQ-006) | Pending | — | — | Phase 2, needs tool001 guard parameter |
| 5 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | No guard instance reachable from `execute_all_tool_calls` until the tool001 plan's parameter exists | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-005, REQ-006, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012
- **Source issue**: `issues/20261021-093421_tool002-tool-call-persisted-without-tool-results.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-105432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-113556
- **Related target files**: `scripts/agent/tool_runner.py`
