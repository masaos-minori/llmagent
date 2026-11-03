## Goal

Move the two remaining synchronous diagnostic writes in `scripts/agent/tool_runner.py` off
the event loop: `_record_transport_failure` becomes a coroutine running
`save_transport_failure` through `asyncio.to_thread` and `execute_one_tool_call` awaits it
at the same point in its sequence; `_execute_with_dag` awaits the offloaded
serialization-event recorder before `_record_round_exec` (REQ-004, REQ-005; AC-4, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/tool_runner.py` row (seq 04) of
`plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md`. Its companion
tests live in the sibling test document
`implementations/20261103-113432_08_tests_agent_test_tool_runner.py.md` (that row fails the
companion conditions — two rows list it — so it has its own document) and must be written
red first. Executes together with
`implementations/20261103-113432_05_scripts_agent_tool_run_recorder.py.md` in one commit:
seq 05 turns `_record_round_serialization_events` into a coroutine this document awaits;
run the tests only after both files are edited.

## Assumptions
- Verified against current source (20261103): `_record_transport_failure` (tool_runner.py:230)
  is synchronous, early-returns on non-error / non-transport / `ctx.diagnostics is None`, and
  calls `ctx.diagnostics.save_transport_failure` with keyword arguments (240-246).
  `execute_one_tool_call` (255) calls `audit_tool_exec` (281), then
  `_record_transport_failure(ctx, name, result)` (292), then `guard.observe_availability`
  (293); `asyncio` is already imported (14). `_execute_with_dag` calls
  `_record_round_serialization_events(...)` at 453, immediately before `_record_round_exec`
  (454-461).
- `rg "_record_transport_failure" scripts tests` shows `execute_one_tool_call` as its only
  caller (Plan D5 re-confirmed 20261103); no test calls the two helpers directly — transport
  tests drive `execute_one_tool_call` (e.g. `TestTransportFailureDiagnostics`
  `test_transport_error_is_saved_to_diagnostics`, tests/agent/test_tool_runner.py:1901), so
  the coroutine change reaches tests only through awaited call paths.
- Size finding (Plan Risks, added 20261103): the file is 20444 B against the 20480 B
  `check_module_size.py` gate — 36 B headroom. This document's diff is estimated at
  `async def` (+6), the awaited call site (+6), the `to_thread` wrap (~+25) and the
  serialization `await` (+6) ≈ +43 B: the gate is expected to fail by a small margin
  unless the wrap lands byte-neutral. Measure exactly after the edits.
- UNK-01 (ConfigLoader thread safety, Plan): settled during seq 03 execution and recorded
  there; if serialization settles on a lock, the same lock discipline applies at these
  sites. UNK-02: no containment is added at these two sites (`to_thread` re-raises in the
  awaiting coroutine, matching today's propagation) — unchanged by this document.

## Design decisions
- Keep the serialization offload glue in `tool_run_recorder.py` (seq 05) and take only the
  `await` at 453 here: the Plan's Risks mitigation for the size gate, and REQ-005's wording
  ("awaited ... from `_execute_with_dag`") is satisfied transitively — the awaited
  coroutine performs the per-event `to_thread` writes in event order before
  `_record_round_exec` runs.
- `_record_transport_failure` becomes `async def` with the same early returns evaluated on
  the loop thread, and one `await asyncio.to_thread(ctx.diagnostics.save_transport_failure,
  ...)` with the identical keyword arguments (REQ-004; AC-4).

## Alternatives considered
- Doing the per-event `to_thread` loop in `_execute_with_dag` (closer to the seq 05 row's
  wording): rejected — it adds ~90 B to `tool_runner.py`, guaranteeing the size gate fails,
  with no behavioral difference.
- Wrapping the synchronous `_record_transport_failure` at its call site with
  `await asyncio.to_thread(...)`: rejected — REQ-004 (Frozen) names the recorder itself as
  the coroutine.

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
1. Confirm the red tests from the seq 08 document exist and fail against the current
   implementation.
2. Change `def _record_transport_failure(` (tool_runner.py:230) to `async def` and its body
   call to `await asyncio.to_thread(ctx.diagnostics.save_transport_failure, session_id=...,
   tool_name=..., server_key=..., error_msg=...)` with the identical keyword values
   (240-246); early returns unchanged.
3. Await the call site: `await _record_transport_failure(ctx, name, result)` at 292, keeping
   it between `audit_tool_exec` and `guard.observe_availability` (REQ-004 sequence).
4. Await the serialization recorder: `await _record_round_serialization_events(...)` at 453
   (requires the seq 05 change in the same commit).
5. Measure size: `uv run python tools/check_module_size.py`. If the gate fails, record a
   Blocker in this document and stop before committing: the owner decides between a
   `--update-baseline` approval and a separate `tool_runner.py` split Plan (Plan Risks
   mitigation). Do not compact unrelated code to squeeze under the gate.

### Method
Three call-site level edits plus one keyword change; no data-flow or signature changes
outside `_record_transport_failure`.

### Details
- `execute_one_tool_call` and `_execute_with_dag` are already `async def`; awaiting does not
  change their signatures (Plan D5).
- `_record_transport_failure` stays radon A-rank (await adds no branch); recheck
  `radon cc scripts/agent/tool_runner.py -s` (current: A(5)/A(5)/A(3) for the three touched
  functions).
- No containment added at either site (UNK-02); exception behavior is byte-identical
  (`asyncio.to_thread` re-raises in the awaiting coroutine).

### Companion test files
- tests/agent/test_tool_runner.py is NOT a companion of this row (two target rows list
  it); its procedure and red-first sequencing are owned by
  `implementations/20261103-113432_08_tests_agent_test_tool_runner.py.md`, which runs
  before this document.
- Validation: the seq 08 tests go green only after this document and seq 05 land; the
  existing `TestTransportFailureDiagnostics` assertions (1901, 1931) must keep passing
  unchanged (REQ-007) — `assert_called_once_with` still matches because the keyword
  arguments pass through `asyncio.to_thread` verbatim.

## Compatibility considerations
- No public API change: `_record_transport_failure` is module-private with a single internal
  caller (Plan D5 verified re-run 20261103).
- Cross-plan overlap (Plan Assumptions, Step 8b): `wfretry001`, `maskargs001` and
  `toolarg001` are completed under `plans/done/`, and `toolarg001`'s `test_tool_runner.py`
  helper rewrite is already on master (verified 20261103), so the Plan's
  "implement this Plan's `test_tool_runner.py` additions after toolarg001" sequencing
  condition is satisfied. `inflightcancel001` (active, same memo batch) also grows this
  file ~200 B — whichever Plan lands second re-runs the size gate and inherits the Blocker
  contingency above.
- No `docs/` change; `uv run python tools/generate_reference_table.py --check` confirms no
  drift (no public symbol changes).

## Security considerations
N/A: unchanged payloads and trust boundaries; only the executing thread moves.

## Rollback considerations
- Revert the commit (with seq 05, one commit); no config or schema change.

## Validation plan
1. `uv run pytest tests/agent/test_tool_runner.py tests/agent/commands/test_cmd_mcp.py -q`
   — seq 08 tests green after this change; existing transport/diagnostics tests unchanged
   (Plan Validation row 3).
2. Static: `uv run ruff check scripts/agent/tool_runner.py`, `uv run ruff format --check`,
   `uv run mypy scripts/agent/tool_runner.py`, bandit (no new finding).
3. Size and complexity gates: `uv run python tools/check_module_size.py` (Procedure 5 —
   the plan's critical gate) and `radon cc scripts/agent/tool_runner.py -s` (no rank
   increase).
4. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after all
   six documents are executed.

## Completion criteria
- AC-4: a transport-level tool error persists through `save_transport_failure` on a worker
  thread, completing before `guard.observe_availability`; other results touch no diagnostics.
- AC-5 (caller half): `_execute_with_dag` awaits the serialization writes in event order
  before `_record_round_exec`.
- AC-6: seq 08 responsiveness tests show loop callbacks firing while the writes are blocked.
- The `check_module_size` result (pass, or Blocker with the owner decision) is recorded in
  this document's Execution Status.

## Out of Scope
- The recorder-side per-event offload implementation (seq 05) and the red tests (seq 08).
- Guard deferral and the LLM-error sites (seq 01/02/03).
- Containment for these two write sites (UNK-02) and `tool_call_state` recorder writes
  (UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm seq 08 red tests exist and fail | Completed | 20261103-173417 | 20261103-173454 | Seq 08 red confirmed: test_transport_failure_write_off_loop and test_serialization_event_write_off_loop fail on the deterministic ordering gate; companion test green; 89 existing tests unchanged. |
| 2 | `async def` + `to_thread` wrap for `_record_transport_failure` (Procedure 2) | Completed | 20261103-174000 | 20261103-174339 | async def + await asyncio.to_thread wrap landed; early returns unchanged; docstring kept single-line for size (see Step 4). |
| 3 | Await both call sites (Procedure 3-4, with seq 05 in one commit) | Completed | 20261103-174000 | 20261103-174339 | await at both call sites: _record_transport_failure between audit_tool_exec and guard.observe_availability; await _record_round_serialization_events before _record_round_exec (seq 05 in working tree, one commit planned). |
| 4 | Size gate measurement and contingency handling (Procedure 5), then Validation plan 1-3 | Completed | 20261103-174339 | 20261103-181609 | All Validation 1-3 checks pass (91/91 test_tool_runner incl. seq 08 green; 173 regression; ruff/format/mypy/bandit clean; radon no rank increase; ref-table no drift) but size gate FAILS: tool_runner.py 20504 B > 20480 (HEAD 20444 + 60 B; black re-wrapped the serialization await +23 B). Docstring already compressed to single line. Stopping before commit per Procedure 5; owner decision recorded in Blocker Log. Owner approved baseline entry agent/tool_runner.py 21000 B (20261103). Gate now: OK - no new violations (advisory tighten only). Validation 1-3 re-confirmed green: 91/91, 173 regression, ruff/format/mypy/bandit clean, radon ranks unchanged (incl. _record_transport_failure A(5)), ref-table no drift. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `check_module_size` fails: tool_runner.py 20504 B > 20480 B gate (HEAD 20444 + 60 B; functional +49 B unavoidable, black re-wrapped the serialization await +23 B; own docstring already compressed). Owner decision required: `--update-baseline` approval vs separate `tool_runner.py` split Plan (note: inflightcancel001 procedure 121149_04 will add ~200 B to this file later). Commit of seq 04+05+08 held until decided. | Yes | 20261103 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (transport-failure write off the loop, awaited at the same
  sequence point), REQ-005 (serialization writes awaited from `_execute_with_dag`),
  REQ-007 (existing tool_runner tests unchanged)
- **Source issue**: issues/20261003-180333_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-113432
- **Related target files**: `scripts/agent/tool_runner.py` (its row's tests are covered by
  the seq 08 document; see Companion test files)
- **Size gate resolution**: `tools/check_module_size_baseline.txt` now grandfathers
  `agent/tool_runner.py` at 21000 B (owner approval 20261103; chosen over a split Plan to
  absorb the pending inflightcancel001 growth in the same file)