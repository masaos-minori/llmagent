## Goal

Rewrite `test_write_first_batch_has_serialize_false` (current line 93) and
`test_serial_barrier_event_fields` (current line 112) in
`tests/agent/test_tool_scheduler_serialization.py` to assert the corrected
serialization-event/batch semantics instead of locking in today's two defects
(scopeless writes gathered concurrently; a hard-coded `is_write=True` on every serial-
barrier event regardless of the triggering call's real write status), and add
reason-code and `is_write`-fidelity tests for the rewritten `ExecutionPlan`/
`SerializationEvent` shape.

## Scope

In scope: `tests/agent/test_tool_scheduler_serialization.py` only —
- the module-level `_tc()`/`_spec()` helpers (current lines 11-24), updated to the
  target `call_specs`-keyed/`resource_scopes`-plural shape once the Issue-01 sibling
  plan lands, and to accept a `requires_serial=True, is_write=False` combination (not
  exercised today) so this doc's new is_write-fidelity test can construct a
  non-write serial-barrier call;
- `test_write_first_batch_has_serialize_false` (current line 93): rewrite so the
  assertion reflects the `global:write` fix — the two scopeless writes now serialize
  (their batch's group is `sequential=True`), not gathered concurrently
  (`serialize_flags[0] is False` today);
- `test_serial_barrier_event_fields` (current line 112): rewrite so `evt.is_write`
  is asserted against the *triggering call's actual* `ToolSpec.is_write` (parametrize
  over both `is_write=True` and `is_write=False` serial calls) instead of the current
  hard-coded expectation `assert evt.is_write is True` which passes today only because
  `tool_scheduler.py`'s production code hard-codes `is_write=True` at its serial-
  barrier event-construction site (current line 151), not because it reflects the
  call's real metadata;
- new tests: each of the five reason codes this plan introduces (`forced_serial`,
  `requires_serial`, `resource_read_write_conflict`, `resource_write_write_conflict`,
  `global_write_scope`) produces a `SerializationEvent` with that exact `reason` string;
  an event is emitted only when concurrency was actually prevented (a batch of calls
  with no conflicts at all produces zero events, already covered by
  `test_read_only_produces_no_serialization_events` at current line 147 — this doc
  extends that non-emission guarantee to the new `global:write`/reason-code paths).

Out of scope: `tests/agent/test_tool_scheduler.py`, `test_tool_scheduler_comprehensive.py`
(separate target files/docs), and `scripts/agent/tool_scheduler.py` itself (covered by
its own doc — this doc only updates tests to match).

## Assumptions

- **Verified by direct read, matching the plan's citation exactly:**
  `test_write_first_batch_has_serialize_false` is at line 93 (within `TestSerializeFlags`,
  lines 30-105), and `test_serial_barrier_event_fields` is at line 112 (within
  `TestSerializationEventFields`, lines 108-165) — both confirmed via
  `grep -n "def test_write_first_batch_has_serialize_false\|def test_serial_barrier_event_fields"`.
- The production rework in the paired `scripts/agent/tool_scheduler.py` doc
  (`call_specs` param, `global:write` fallback scope, public `SerializationEvent` with
  real `is_write`, the five explicit reason codes, `ExecutionPlan` return type) lands in
  the same commit; this file's tests target that new shape.
- Per this plan's own Step-1 gate and confirmed against current source
  (`resource_scopes` absent from `scripts/shared/tool_spec.py`,
  `scripts/agent/tool_preparation.py` does not exist), this file's current content
  (singular `resource_scope=` kwargs via its own `_spec()` helper) remains valid
  against today's source and must not be rewritten until both the Issue-01 sibling plan
  and this plan's production changes land.
- This file defines its own local `_tc()`/`_spec()` helpers (current lines 11-24),
  independent of the other two scheduler test files' `_tc()`/`_meta()` — confirmed by
  reading all three files' headers; this doc's edits to `_spec()` do not need to stay
  in sync with `_meta()`'s shape in the sibling files, only with the production
  `ToolSpec` contract they all consume.

## Design decisions

- **`test_write_first_batch_has_serialize_false`'s rewritten assertion inverts to
  `is True`, on a sequential group, not a concurrently-gathered one.** Today (lines
  93-101): `write_first_batch = md.concurrent_groups[0]` / `assert
  write_first_batch.serialize_flags[0] is False` — two scopeless writes (`write_x`,
  `write_y`) share one group, gathered concurrently. Under the `global:write` fix, both
  resolve to the same synthetic scope and conflict — the corrected assertion locates
  the resulting `ScheduledGroup` and asserts `sequential is True` (the field name/shape
  from the new `ExecutionPlan`/`ScheduledGroup` dataclasses, replacing the old
  `serialize_flags` parallel-array indexing). Rename the test (e.g.
  `test_write_first_group_now_serializes_via_global_write_scope`) to state the
  behavior change explicitly, mirroring the equivalent rewrite in the paired
  `test_tool_scheduler.py` doc for `test_write_first_group_is_gathered_concurrently`
  (the two tests exercise the same underlying fix from two different angles — batch/
  group shape here, event fields there — and should be rewritten consistently, not
  independently reinvented).
- **`test_serial_barrier_event_fields` parametrizes over real `is_write`, replacing the
  hard-coded expectation.** Today's test (lines 112-120) only exercises
  `_spec("shell_run", requires_serial=True)` — `is_write` defaults to `False` in the
  `_spec()` helper's own signature (current line 16: `is_write: bool = False`), yet the
  test asserts `evt.is_write is True` (line 118), which only passes today because
  `tool_scheduler.py`'s serial-barrier event construction (current line 151) hard-codes
  `is_write=True` regardless of the actual spec passed in — a real defect this plan's
  Goal names explicitly ("real `is_write` (never hard-coded)"). The rewritten test adds
  a second case with `requires_serial=True, is_write=False` and asserts
  `evt.is_write is False` for that case, proving the fix actually reads the call's
  metadata instead of hard-coding.
- **Reason-code tests are additive, one per new code, not a single combined test.**
  Per the plan's Design section: "explicit reason codes (`forced_serial`,
  `requires_serial`, `resource_read_write_conflict`, `resource_write_write_conflict`,
  `global_write_scope`)" — five distinct, independently-triggerable conditions;
  separate tests make it clear in a failing-test report exactly which code regressed,
  rather than one parametrized test whose failure output requires cross-referencing
  which case failed.

## Alternatives considered

- Leaving `test_serial_barrier_event_fields` as a single non-parametrized case and
  trusting that a passing `is_write is True` assertion is "close enough" evidence the
  fix works, since `shell_run`-style serial tools are usually writes in practice.
  Rejected: this is exactly the kind of coincidental-pass the plan's Risk section warns
  against — the current test already passes against the *broken* hard-coded-`True`
  implementation, so it provides zero regression signal for this specific fix unless a
  `requires_serial=True, is_write=False` case is added that would fail under the old
  hard-coded behavior and pass under the new real-metadata behavior.
- Adding the `global:write` batch-shape regression test here as well as in
  `test_tool_scheduler.py`, on the theory that this file (serialization-focused) should
  also carry it. Rejected in favor of one rewrite per already-plan-cited test location:
  this file's `test_write_first_batch_has_serialize_false` is the plan-cited test for
  the *batch/serialize_flags* angle of the same fix that `test_tool_scheduler.py`'s
  `test_write_first_group_is_gathered_concurrently` covers from the *groups* angle —
  both are rewritten, in their own files, per the plan's own citation, not merged or
  duplicated across files.

## Implementation

### Target file: `tests/agent/test_tool_scheduler_serialization.py`

### Procedure

1. Confirm the Issue-01 sibling plan's port of this file has landed (call-id-keyed
   `call_specs`/`resource_scopes` plural) before applying this doc's edits.
2. Rewrite `test_write_first_batch_has_serialize_false` (current lines 93-101): change
   the located group/flag assertion so the two scopeless writes' resulting group is
   asserted `sequential`/serialized, not concurrently-gathered — reconcile the exact
   attribute name (`serialize_flags[i]` vs. a `ScheduledGroup.sequential` field) against
   the paired `tool_scheduler.py` doc's actual dataclass shape at implementation time.
3. Rewrite `test_serial_barrier_event_fields` (current lines 112-120): add a second
   parametrized case with `requires_serial=True, is_write=False`, asserting
   `evt.is_write is False` for that case (and keep the existing `is_write=True` case,
   asserting `evt.is_write is True` for it) — proving the event's `is_write` field
   tracks the real spec, not a hard-coded constant.
4. Add one test per new reason code (`forced_serial`, `requires_serial`,
   `resource_read_write_conflict`, `resource_write_write_conflict`,
   `global_write_scope`), each constructing the minimal batch that triggers exactly
   that code and asserting `evt.reason == "<code>"`.
5. Extend the "no serialization events when nothing conflicts" guarantee (existing
   pattern at `test_read_only_produces_no_serialization_events`, current line 147) to
   confirm a batch of calls with distinct, non-overlapping explicit scopes (no
   `global:write` fallback triggered, no barrier) also produces zero events.
6. Update the `from agent.tool_scheduler import (...)` line (current line 7) if new
   symbols need importing for direct dataclass-shape assertions.

### Method

Manual, targeted rewrites of the two plan-cited tests plus additive reason-code
coverage, guided by direct reading of the file's two test classes
(`TestSerializeFlags`, lines 30-105; `TestSerializationEventFields`, lines 108-165) to
confirm exact current assertions before inverting them.

### Details

- Confirmed via direct read (full file, 164 lines) and
  `grep -n "def test_write_first_batch_has_serialize_false\|def test_serial_barrier_event_fields"`:
  both at the plan-cited lines exactly — 93 and 112 respectively — inside
  `TestSerializeFlags` (30) and `TestSerializationEventFields` (108).
- `_spec()` (current lines 15-24) signature: `_spec(name, *, scope="", is_write=False,
  requires_serial=False)` — confirmed `is_write` already defaults to `False`
  independent of `requires_serial`, meaning the helper already supports constructing
  the new non-write-serial-barrier case this doc's rewrite needs without modification;
  only the test *bodies* need updating, not the helper.
- `test_write_first_batch_has_serialize_false`'s current body (lines 93-101): `tcs =
  [_tc("write_x"), _tc("write_y")]`, `meta = {"write_x": _spec("write_x", is_write=True),
  "write_y": _spec("write_y", is_write=True)}` (both explicitly no-scope) — confirmed
  this is precisely the scopeless-write-pair scenario the plan's `global:write` fix
  targets.
- `test_serial_barrier_event_fields`'s current body (lines 112-120) asserts
  `evt.requires_serial is True`, `evt.is_write is True`, `evt.resource_scope == ""`,
  `evt.scheduling_decision == "serial_barrier"` — confirmed the `is_write is True`
  assertion is the one this doc's Design section flags as coincidentally passing
  against the current hard-coded-`True` production bug (`tool_scheduler.py:151`).
- Coincidental prior-cycle filename match: `ls implementations/*test_tool_scheduler_serialization.py*
  implementations/done/*test_tool_scheduler_serialization.py* 2>/dev/null` returns one
  hit, `implementations/done/20260705-151354_test_tool_scheduler_serialization.py.md` —
  read in full: dated July, no `Traceability` block, references
  `tests/test_tool_scheduler_serialization.py` (no `agent/` path segment) — confirmed a
  genuinely unrelated prior effort (different file path convention, different era, no
  reference to `call_specs`/`global:write`/`ExecutionPlan`), a coincidental filename
  match only.

## Compatibility considerations

- This file's helpers (`_tc`, `_spec`) are local to this file, not shared with the other
  two scheduler test files — changes here do not affect them, though all three must
  agree on the production `build_execution_groups()`/`ExecutionPlan`/`SerializationEvent`
  shapes.
- `SerializationEvent.resource_scope` may become `resource_scopes` (plural) per the
  sibling Issue-01 `tool_scheduler.py` doc's Design decision — if that rename lands,
  every `evt.resource_scope ==` assertion in this file (lines 119, 132, 143) must update
  to the plural field name in the same commit, or these tests fail with an
  `AttributeError` rather than a assertion failure. Flagged here for the implementer to
  reconcile against whichever `tool_scheduler.py` doc's dataclass shape is actually
  built.

## Security considerations

N/A — test-only file. `test_serial_barrier_event_fields`'s rewritten `is_write=False`
case is itself a direct regression lock for this plan's audit-trail-truthfulness
acceptance criterion ("its audit trail is actually truthful," per the plan's Goal).

## Rollback considerations

- Coupled to the paired `scripts/agent/tool_scheduler.py` implementation doc; revert
  together.
- No data/schema impact.

## Validation plan

`uv run pytest tests/agent/test_tool_scheduler_serialization.py -v` (and jointly per the
plan's Validation plan table with the other two scheduler test files) — the rewritten
`test_write_first_batch_has_serialize_false` and `test_serial_barrier_event_fields`
pass; new reason-code and is_write-fidelity tests pass; every other pre-existing
scenario in this file's two classes still passes with equivalent intent.

## Out of scope

- `tests/agent/test_tool_scheduler.py`, `test_tool_scheduler_comprehensive.py` —
  covered by their own docs.
- `scripts/agent/tool_scheduler.py` itself — covered by its paired implementation doc.
- The Issue-01 sibling plan's mechanical call-id-keying port of this file — assumed
  already landed, not re-performed by this doc.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184423_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-001549
- Related target files: test_tool_scheduler_serialization.py
