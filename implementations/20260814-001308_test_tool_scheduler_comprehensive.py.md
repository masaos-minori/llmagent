## Goal

Add read/write conflict, write/write conflict (distinct from the `global:write`
fallback case), read/read-concurrency-at-scale, and missing-`call_id`-failure coverage
for the rewritten `build_execution_groups()` in this file's existing "comprehensive/
edge case" style (large batches, dense mixed scenarios), per the plan's Implementation
step "add the remaining tests enumerated in the requirement's Tests section
(...read/write and write/write conflict serialization, read/read concurrency,
ancestor/descendant conflict, missing-ToolSpec failure...)".

## Scope

In scope: `tests/agent/test_tool_scheduler_comprehensive.py` only —
- the module-level `_tc()`/`_meta()` helpers (current lines 11-27), updated to the
  target `call_specs`-keyed/`resource_scopes`-plural shape once the Issue-01 sibling
  plan lands (this doc does not re-perform that mechanical port — see Assumptions);
- new tests reflecting this file's "comprehensive/edge case" character: an explicit
  same-scope read/write conflict test; an explicit same-scope write/write conflict test
  (distinct from the `global:write`-fallback path, which is exercised in the paired
  `test_tool_scheduler.py` doc's rewrite of `test_write_first_group_is_gathered_concurrently`);
  a large-N all-read batch proving read/read pairs never conflict even at scale
  (extending `test_large_number_of_tools`'s existing pattern, current line 148); a
  missing-`call_id` failure case building on `test_tool_with_no_metadata`'s existing
  home (current line 136), confirming the fail-closed behavior holds under this plan's
  `call_specs`/`force_serial` signature.

Out of scope: `tests/agent/test_tool_scheduler.py` — the actual rewrite of
`test_write_first_group_is_gathered_concurrently` (the scopeless-writes-now-serialize
regression lock) lives there, at line 293, confirmed via direct read/grep of that file;
this doc does not duplicate it. Also out of scope: `test_tool_scheduler_serialization.py`
(separate doc), and `scripts/agent/tool_scheduler.py` itself (covered by its own doc).

## Assumptions

- The production rework in the paired `scripts/agent/tool_scheduler.py` doc
  (`call_specs` param, `global:write` fallback, `force_serial`, `ExecutionPlan` return)
  lands in the same commit; this file's tests target that new shape.
- Per this plan's own Step-1 gate and confirmed against current source
  (`resource_scopes` absent from `scripts/shared/tool_spec.py`,
  `scripts/agent/tool_preparation.py` does not exist), this file's current content
  (singular `resource_scope=` kwargs, no `name` parameter in `_meta()`) remains valid
  against today's source and must not be rewritten until both the Issue-01 sibling plan
  and this plan's production changes land.
- This file's `_meta()` omitting a `name` parameter (always `name=""`) is a pre-existing,
  deliberate simplification specific to this file — `build_execution_groups()`'s logic
  never reads `ToolSpec.name`, confirmed by reading the current production function —
  this doc does not add a `name` parameter merely for symmetry with
  `test_tool_scheduler.py`'s helper.
- `test_tool_with_no_metadata` (current line 136) is the natural extension point for
  this doc's missing-`call_id` case, per the same reasoning the sibling Issue-01 doc
  already applies to this exact test (its name already describes "what happens when a
  call has no metadata," which under both Issue 01's and this plan's fail-closed
  changes becomes "raises," not "falls back to a default bucket").

## Design decisions

- **New read/write and write/write conflict tests use explicit, non-empty
  `resource_scopes`** (once that field lands) to distinguish "same explicit scope, must
  serialize" from "no scope, falls back to `global:write`, must *also* serialize
  (against each other)" as two independently-verified paths through the same
  conflict-graph logic, per this plan's Design section step 5. The `global:write`
  path itself is exercised by the paired `test_tool_scheduler.py` doc's rewrite, not
  duplicated here.
- **Read/read concurrency test scales with this file's existing "large N" style.**
  Extend `test_large_number_of_tools`'s pattern (current line 148) with an
  all-read-no-write variant asserting every read stays in one concurrent
  `ScheduledGroup` regardless of batch size — proving the conflict graph never builds
  edges between two reads, consistent with this plan's Design section ("read/read
  pairs never conflict").
- **Missing-`call_id` test extends `test_tool_with_no_metadata`'s existing home.**
  If the Issue-01 sibling plan's own version of this test already asserts a raise here
  (for its own `MissingToolSpecError` reason), this doc's addition only needs to confirm
  the same failure mode holds under this plan's *additional* `call_specs`/`force_serial`
  signature — e.g. that the failure surfaces correctly even when `force_serial=True` is
  also passed — rather than introduce a second, competing assertion for the same base
  scenario.

## Alternatives considered

- Performing the full Issue-01 mechanical call-id-keying port of this file's seven
  existing tests within this doc. Rejected: that port is Issue 01's responsibility
  (already documented in its own implementation cycle, generated `20260813-195246`);
  this doc's scope is narrower — only the new conflict-scenario/scale coverage this
  plan's algorithm change specifically requires.
- Duplicating the `test_write_first_group_is_gathered_concurrently` rewrite in this file
  as well as in `test_tool_scheduler.py`, on the theory that both files should carry
  regression coverage for the `global:write` fix. Rejected: the plan's Implementation
  steps name this test once, by name, without a file qualifier, and direct
  `grep -n "def test_write_first_group_is_gathered_concurrently"` across both files
  confirms it is defined exactly once, in `test_tool_scheduler.py:293` — duplicating it
  here would test the same production code path twice with no new information; this
  file's distinct value is its edge-case/scale coverage (large N, dense mixed batches),
  which is what this doc adds instead.

## Implementation

### Target file: `tests/agent/test_tool_scheduler_comprehensive.py`

### Procedure

1. Confirm the Issue-01 sibling plan's port of this file has landed before applying
   this doc's edits — this doc's new tests assume `call_specs`/`resource_scopes`
   already exist, per Assumptions.
2. Add a same-scope read/write conflict test: one write call and one read call sharing
   an explicit `resource_scopes` entry, asserting they serialize together (same
   sequential `ScheduledGroup`).
3. Add a same-scope write/write conflict test (distinct from the `global:write` case):
   two writes with an explicit shared scope, asserting serialization — proving the
   explicit-scope path routes through the same conflict logic as the `global:write`
   fallback path (verified separately in the paired `test_tool_scheduler.py` doc).
4. Extend `test_large_number_of_tools` (current line 148) or add a sibling test with an
   all-read batch at the same N, asserting one concurrent `ScheduledGroup` with no
   sequential splits.
5. Confirm/extend `test_tool_with_no_metadata` (current line 136) to assert the
   fail-closed behavior holds under this plan's `call_specs`/`force_serial` signature —
   only add coverage for anything specific to this plan's changes (e.g. the failure
   surfacing correctly even when `force_serial=True`), not a duplicate of Issue 01's
   base-case assertion if it already exists.

### Method

Manual, targeted additions layered on top of the Issue-01 sibling plan's mechanical
port — additive edge-case extensions guided by this file's existing "comprehensive"
style (large N, dense mixed batches, aggregate shape assertions), with no rewrite of
any test that already belongs to a different target file.

### Details

- Confirmed via direct read (lines 1-175) and `grep -n "^def test_|^class Test"
  tests/agent/test_tool_scheduler_comprehensive.py`: single class
  `TestBuildExecutionGroupsEdgeCases` (line 30) with 7 methods including
  `test_all_tools_same_resource_scope` (118), `test_tool_with_no_metadata` (136),
  `test_large_number_of_tools` (148), `test_single_tool_with_complex_metadata` (162) —
  file total 175 lines.
- Re-verified via `grep -n "def test_write_first_group_is_gathered_concurrently"
  tests/agent/test_tool_scheduler.py tests/agent/test_tool_scheduler_comprehensive.py`:
  exactly one match, `tests/agent/test_tool_scheduler.py:293` — confirming that test
  does **not** live in this file, and this doc correctly does not attempt its rewrite.
- Coincidental prior-cycle filename match: `ls
  implementations/*test_tool_scheduler_comprehensive.py*
  implementations/done/*test_tool_scheduler_comprehensive.py* 2>/dev/null` returns one
  hit from the Issue-01 sibling plan (`plans/20260813-183049_plan.md`, generated
  `20260813-195246`) — that doc covers the call-id-keying port and its own
  `test_tool_with_no_metadata` repurposing for `MissingToolSpecError`; it does not
  cover this plan's `global:write`/`force_serial`/multi-barrier scenarios, confirmed
  absent from source today, so this doc is written rather than skipped.

## Compatibility considerations

- This file's helpers (`_tc`, `_meta`) are local, not shared with the other two
  scheduler test files — changes here do not affect them, though all three must agree
  on the production `build_execution_groups()` signature.

## Security considerations

N/A — test-only file. The read/write and write/write conflict tests are themselves
direct regression locks for this plan's correctness acceptance criteria.

## Rollback considerations

- Coupled to the paired `scripts/agent/tool_scheduler.py` implementation doc; revert
  together.
- No data/schema impact.

## Validation plan

`uv run pytest tests/agent/test_tool_scheduler_comprehensive.py -v` (and jointly per the
plan's Validation plan table with the other two scheduler test files) — new conflict/
scale/missing-id tests pass; every other pre-existing scenario still passes with
equivalent intent once the Issue-01 port has landed.

## Out of scope

- The `test_write_first_group_is_gathered_concurrently` rewrite — lives in
  `tests/agent/test_tool_scheduler.py`, covered by that file's own doc.
- `tests/agent/test_tool_scheduler_serialization.py` — covered by its own doc.
- `scripts/agent/tool_scheduler.py` itself — covered by its paired implementation doc.
- The Issue-01 sibling plan's mechanical call-id-keying port of this file — assumed
  already landed, not re-performed by this doc.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184423_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-001308
- Related target files: test_tool_scheduler_comprehensive.py
