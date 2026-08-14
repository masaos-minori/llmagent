## Goal

Rewrite `test_serial_tool_precedes_parallel_tools` (current line 61, in
`TestRequiresSerialBarrier`) and `test_write_first_group_is_gathered_concurrently`
(current line 293, in `TestConcurrentGroups`) in `tests/agent/test_tool_scheduler.py` to
assert the corrected phase-based behavior instead of locking in today's two defects
(leading-bucket barrier hoisting; scopeless writes gathered concurrently instead of
serialized), and add new phase-boundary/order-preservation/`force_serial`/missing-
`call_id` tests for the rewritten `build_execution_groups()`.

## Scope

In scope: `tests/agent/test_tool_scheduler.py` only —
- the module-level `_tc()` and `_meta()` helpers (current lines 11-28), updated so
  `_meta()` builds a `ToolSpec` compatible with whatever field shape lands from the
  Issue-01 sibling plan (`resource_scopes` plural, once that lands) and test call sites
  switch from `{name: _meta(...)}` to `{tc["id"]: _meta(...)}` dicts (the parameter this
  plan renames from `tool_meta` to `call_specs`);
- `test_serial_tool_precedes_parallel_tools` (current line 61): rewrite to assert the
  serial call occupies its own *phase* in original position (not necessarily first if
  it appears after a parallel call in the input), per this plan's "in-place barrier, not
  a leading bucket" fix;
- `test_write_first_group_is_gathered_concurrently` (current line 293): rewrite to
  assert the two scopeless writes now *serialize* (both resolve to the synthetic
  `("global:write",)` scope and conflict), instead of today's assertion that they share
  one group gathered concurrently (`serialize_flags == [False]`) — a direct behavior
  inversion, the regression lock for this plan's "no scope-less writes racing each
  other" acceptance criterion;
- new tests: multiple `requires_serial` barriers splitting a batch into multiple phases
  in original order; a `force_serial=True` batch producing one single-call sequential
  phase per call regardless of scope/write metadata, reason `forced_serial`; a call
  whose `call_id` is absent from `call_specs` raising (exact exception type reconciled
  against the paired `tool_scheduler.py` doc at implementation time).

Out of scope: `tests/agent/test_tool_scheduler_comprehensive.py`,
`test_tool_scheduler_serialization.py` (separate target files/docs in this set — the
paired `test_tool_scheduler_comprehensive.py` doc covers its own new
conflict/scale/missing-id coverage, not this rewrite), and any change to
`scripts/agent/tool_scheduler.py` itself (covered by its own doc — this doc only
updates tests to match).

## Assumptions

- The production rework described in the paired `scripts/agent/tool_scheduler.py` doc
  (new `call_specs` parameter name, `global:write` fallback scope, `force_serial`
  input, `ExecutionPlan` return type) lands in the same commit as this test update —
  these tests are written against the *target* signature and would fail against
  unmodified source.
- Per this plan's own Step-1 gate, `ToolSpec.resource_scopes` (plural) is assumed
  delivered by the sibling Issue-01 plan before this plan's tests are finalized;
  confirmed absent from `scripts/shared/tool_spec.py` as of this writing (only singular
  `resource_scope: str` exists) — this file's current content (singular
  `resource_scope=` kwargs at `_meta()` call sites) is therefore still valid against
  today's source and must not be rewritten until both the Issue-01 and this plan's
  production changes land.
- The existing `_tc(name)` helper's `"id": f"call_{name}"` shape (current lines 11-12)
  is sufficient as a call-id source for every test in this file, mirroring the same
  convenient property the sibling Issue-01 doc notes for this exact file.

## Design decisions

- **`test_serial_tool_precedes_parallel_tools`'s rewritten assertion drops the "always
  first" framing.** Today's test (lines 61-72) asserts `groups[0] == [serial]` — the
  serial call's group is always first regardless of input order (it happens to be first
  in this test's input, `[serial, parallel]`). Under the corrected in-place-barrier
  semantics, a serial call's phase occupies its *original relative position*. Add a new
  variant with input `[parallel, serial]` asserting the parallel call's phase comes
  first and the serial call's own single-call phase follows — the inverse ordering,
  which today's leading-bucket logic would get wrong (it would still hoist the barrier
  to the front). Keep the original `[serial, parallel]` variant too, since it remains a
  valid (if less discriminating) case.
- **`test_write_first_group_is_gathered_concurrently`'s assertion inverts.** Today
  (lines 293-305): `write_first_batch.groups == [[tc_write_a, tc_write_b]]` and
  `serialize_flags == [False]` — both scopeless writes share one group, gathered
  concurrently. Under the `global:write` fix, both calls resolve to
  `resource_scopes == ("global:write",)`, which conflict (same scope, both writes) —
  the corrected assertion is that they land in one **sequential** `ScheduledGroup`
  (`sequential=True`), not a concurrently-gathered one. Rename the test (e.g.
  `test_scopeless_writes_now_serialize_via_global_write_scope`) or keep its name and
  invert its body, with a comment stating this is an intentional behavior change per
  this plan, not a preserved one.
- **New multi-barrier test proves phases split around each barrier, not just the first
  one.** Per the plan's Design section: "close current_phase, emit the serial call as
  its own single-call phase, start a fresh current_phase" on *every* `requires_serial`
  call encountered while walking in order — a batch like
  `[read_a, serial_1, read_b, serial_2, read_c]` must produce five phases in that exact
  order (not two barrier phases hoisted to the front followed by one merged read phase,
  which is what today's leading-bucket logic would do).
- **`force_serial=True` test asserts one phase per call, in original order, regardless
  of any scope/write metadata.** Per the plan's Design section point 6, this is a
  short-circuit that bypasses the conflict-graph logic entirely — the test should use
  calls that *would* otherwise share a scope and be grouped concurrently under
  `force_serial=False`, to prove the short-circuit actually overrides normal grouping
  rather than coincidentally agreeing with it.
- **Missing-`call_id` test omits the id from `call_specs` entirely**, matching the
  paired implementation doc's described lookup-and-raise-on-miss behavior, rather than
  mapping it to `None` — this exercises the actual "absence" branch, not a null-check
  branch.

## Alternatives considered

- Rewriting every existing test in this file's six classes wholesale in this doc,
  duplicating effort already covered by the sibling Issue-01 doc's port of the same
  file (name-keyed → call-id-keyed dict rekeying, `_meta()` parameter rename). Rejected:
  this plan explicitly builds on top of Issue 01 landing first (per its own Assumptions
  and UNK-01) — the call-id-keying mechanical port is Issue 01's responsibility; this
  doc's job is narrower: only the two named defect-locking tests plus the new phase/
  force_serial/missing-id cases specific to *this* plan's algorithm change.
- Leaving `test_write_first_group_is_gathered_concurrently`'s name and assertion
  unchanged and adding a separate, differently-named test for the `global:write`
  behavior. Rejected: the existing test's name and current assertion are the exact
  scenario whose *meaning* changes under this plan — rewriting in place makes the
  behavior change visible in the diff, matching how the plan's Implementation steps
  explicitly list this test by name for rewriting, not for duplication alongside.

## Implementation

### Target file: `tests/agent/test_tool_scheduler.py`

### Procedure

1. Confirm the Issue-01 sibling plan's port of this file has landed (call-id-keyed
   `call_specs`/`resource_scopes` plural) before applying this doc's edits — this doc's
   new/rewritten tests assume that shape already exists, per Assumptions.
2. Rewrite `test_serial_tool_precedes_parallel_tools` (current lines 61-72): keep the
   `[serial, parallel]` variant and add a new `[parallel, serial]` variant asserting the
   parallel call's phase precedes the serial call's own single-call phase — proving
   position is input-order-derived, not hard-coded to "barrier first."
3. Rewrite `test_write_first_group_is_gathered_concurrently` (current lines 293-305):
   change the assertion so the two scopeless writes (`tc_write_a`, `tc_write_b`, both
   `is_write=True`, no explicit scope) land in one **sequential** `ScheduledGroup` via
   the resolved `("global:write",)` scope, not a concurrently-gathered one. Update the
   test's docstring/comment to state this is an intentional behavior change.
4. Add `TestPhaseBoundaries` (or extend `TestRequiresSerialBarrier`) with a
   multi-barrier test: `[read_a, serial_1, read_b, serial_2, read_c]` asserting five
   phases in exactly that order.
5. Add `TestForceSerial` with a test passing `force_serial=True` on a batch of calls
   that share a resource scope (would otherwise concurrently-group), asserting one
   single-call sequential phase per call, in original order, each with reason
   `forced_serial`.
6. Add a missing-`call_id` test: `build_execution_groups([tc], {})` (empty
   `call_specs`) raises the exception type the production rework introduces (reconcile
   the exact type against the implemented `tool_scheduler.py` at commit time — this
   plan does not itself mandate a new exception name, unlike the sibling Issue-01
   plan's `MissingToolSpecError`; reuse that one if the production code does).
7. Update the `from agent.tool_scheduler import (...)` line (current line 7) to import
   whatever new symbols this test file needs (`ExecutionPlan` if tests inspect its shape
   directly, the exception class from step 6).

### Method

Manual, targeted additions layered on top of the Issue-01 sibling plan's mechanical
call-id-keying port (not re-done here) — this doc's own edits are two behavior-correcting
rewrites plus three new test classes, guided by direct reading of the current six test
classes (lines 34-390) to confirm exact line numbers and existing helper shapes before
writing new assertions.

### Details

- Confirmed via direct read (lines 1-100, 237-390) and `grep -n "^def test_|^class Test"
  tests/agent/test_tool_scheduler.py`: six test classes —
  `TestBuildExecutionGroupsEmpty` (34), `TestRequiresSerialBarrier` (53),
  `TestResourceScopeGrouping` (87), `TestMixedScenarios` (178), `TestConcurrentGroups`
  (237), `TestToolRunnerDefaultSpec` (331) — file total 390 lines, matching the plan's
  file-level citation.
- `test_serial_tool_precedes_parallel_tools` (lines 61-72) today: input `[serial,
  parallel]`, asserts `groups[0] == [serial]` and `parallel in groups[-1]` — confirmed
  this passes trivially today regardless of whether the barrier is "hoisted" or
  "in-place," since serial is already first in the input; the new `[parallel, serial]`
  variant added by this doc's Procedure step 2 is what actually distinguishes the two
  implementations.
- `test_write_first_group_is_gathered_concurrently` confirmed via
  `grep -n "def test_write_first_group_is_gathered_concurrently" tests/agent/test_tool_scheduler.py`
  at line 293, inside `TestConcurrentGroups` (lines 237-329) — reading its full body
  (293-305) confirms today's exact assertions: `write_first_batch.groups ==
  [[tc_write_a, tc_write_b]]` and `write_first_batch.serialize_flags == [False]`,
  matching the plan's citation exactly (both the line number and the file).
- `_tc(name)` (lines 11-12) already returns `{"function": {"name": name}, "id":
  f"call_{name}"}` — confirmed deterministic and distinct per name, sufficient for this
  doc's new multi-barrier/force_serial tests without needing a second id-generation
  scheme.
- Coincidental prior-cycle filename match: `ls implementations/*test_tool_scheduler.py*
  implementations/done/*test_tool_scheduler.py* 2>/dev/null` returns hits from the
  Issue-01 sibling plan (`plans/20260813-183049_plan.md`, generated
  `20260813-195153`) and from unrelated older cycles (`20260619-095600`,
  `20260705-151352`, `20260715-150757` in `implementations/done/`) — none targets this
  plan's specific symbols (`force_serial`, the `global:write` inversion, multi-barrier
  phase-splitting, the `[parallel, serial]` ordering test); confirmed genuinely absent
  from this file today (only singular `resource_scope=` kwargs exist, per Assumptions),
  so this doc is written rather than skipped.

## Compatibility considerations

- This file's helpers (`_tc`, `_meta`) are local to this file, not shared with the other
  two scheduler test files — new/rewritten tests here do not affect
  `test_tool_scheduler_comprehensive.py` or `test_tool_scheduler_serialization.py`,
  though all three must agree on the production `build_execution_groups()` signature
  they test against (`call_specs` param name, `force_serial` kwarg, `ExecutionPlan`
  return type, `global:write` fallback).

## Security considerations

N/A — test-only file. `test_write_first_group_is_gathered_concurrently`'s inverted
assertion is itself a direct regression lock for this plan's "no scope-less writes
racing each other" security-relevant correctness fix.

## Rollback considerations

- Coupled to the paired `scripts/agent/tool_scheduler.py` implementation doc; revert
  together.
- No data/schema impact.

## Validation plan

`uv run pytest tests/agent/test_tool_scheduler.py -v` (and jointly with the other two
scheduler test files per the plan's Validation plan table:
`uv run pytest tests/agent/test_tool_scheduler.py tests/agent/test_tool_scheduler_comprehensive.py tests/agent/test_tool_scheduler_serialization.py -v`)
— the rewritten `test_serial_tool_precedes_parallel_tools` and
`test_write_first_group_is_gathered_concurrently` variants pass; new phase-boundary,
`force_serial`, and missing-`call_id` tests pass; every other pre-existing scenario in
this file's six classes still passes with equivalent intent.

## Out of scope

- `tests/agent/test_tool_scheduler_comprehensive.py`, `test_tool_scheduler_serialization.py`
  — covered by their own docs.
- `scripts/agent/tool_scheduler.py` itself — covered by its paired implementation doc.
- The Issue-01 sibling plan's mechanical call-id-keying port of this file's six existing
  classes — assumed already landed, not re-performed by this doc.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184423_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-001203
- Related target files: test_tool_scheduler.py
