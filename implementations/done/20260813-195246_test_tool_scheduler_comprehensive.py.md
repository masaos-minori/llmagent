## Goal

Update `tests/agent/test_tool_scheduler_comprehensive.py` (175 lines today) so its edge-
case tests for `build_execution_groups()` use call-id-keyed `tool_meta` dicts and
`ToolSpec.resource_scopes` (plural) instead of today's tool-name-keyed dict and singular
`resource_scope`, porting every existing scenario with equivalent intent, then add
comprehensive multi-scope edge cases (large batches with overlapping multi-scope calls,
a `move_file`-style dual scope inside a complex mixed batch) reflecting this file's
"edge case" focus.

## Scope

In scope: `tests/agent/test_tool_scheduler_comprehensive.py` only —
- the module-level `_tc()` and `_meta()` helpers (current lines 11-27), updated: `_tc()`
  is unchanged in shape (already returns a call-id-bearing dict); `_meta()` gains a
  `resource_scopes: tuple[str, ...] = ()` parameter replacing `resource_scope: str = ""`
  (note: this file's `_meta()`, unlike `test_tool_scheduler.py`'s, takes no `name`
  parameter at all — it always builds `ToolSpec(name="", ...)` — this doc preserves that
  detail since it is a pre-existing, deliberate simplification specific to this file's
  edge-case focus, not something this doc needs to "fix");
- the single test class `TestBuildExecutionGroupsEdgeCases` (current lines 30-175), every
  one of its 7 test methods (`test_mixed_tool_types_with_complex_dependencies`,
  `test_empty_resource_scopes_and_no_scopes`, `test_complex_resource_scopes`,
  `test_all_tools_same_resource_scope`, `test_tool_with_no_metadata`,
  `test_large_number_of_tools`, `test_single_tool_with_complex_metadata`), each of which
  today builds its `meta` dict keyed by tool *name* string literal (e.g. `"shell_run":
  _meta(requires_serial=True)`), updated to key by each call's `"id"` field instead;
- new tests reflecting this file's "comprehensive/edge case" character: a large batch
  (extending `test_large_number_of_tools`'s pattern) where several calls share
  overlapping multi-valued `resource_scopes`, and a dense mixed-batch case combining a
  `move_file`-style dual-scope call with unrelated serial/write-first/parallel calls in
  one batch (extending `test_mixed_tool_types_with_complex_dependencies`'s pattern).

Out of scope: `tests/agent/test_tool_scheduler.py`, `test_tool_scheduler_serialization.py`
(separate docs), and `scripts/agent/tool_scheduler.py` itself (covered by its own doc).

## Assumptions

- The production rework in the paired `scripts/agent/tool_scheduler.py` doc lands in the
  same commit; this file's tests target the new signature. Confirmed against the
  "Already-verified facts": today's `_meta()` here builds `ToolSpec(call_id="", name="",
  resource_scope=resource_scope, ...)` (singular field), consistent with
  `resource_scopes` not existing anywhere yet — this file is unmodified/valid against
  current source and must not be rewritten until the paired implementation lands.
- `MissingToolSpecError` is importable from `agent.tool_scheduler`, per the paired
  scheduler doc.
- This file's `_meta()` omitting a `name` parameter (always `name=""`) is intentional and
  orthogonal to the call-id-keying change — `ToolSpec.name` is not read by
  `build_execution_groups()`'s logic (confirmed by reading the production function: it
  reads `meta.requires_serial`, `meta.resource_scope`/`resource_scopes`, `meta.is_write`,
  never `meta.name`), so this doc does not add a `name` parameter to `_meta()` here
  merely for symmetry with the other two test files' helpers.

## Design decisions

- **Rename `_meta()`'s `resource_scope` parameter to `resource_scopes`, accepting a
  tuple.** Same mechanical rename as the sibling `test_tool_scheduler.py` doc, applied
  consistently: every call site's `resource_scope="file"` becomes
  `resource_scopes=("filesystem:file",)` (adding a kind prefix per the plan's Design
  section scope-string shape), preserving each test's original intent (e.g.
  `test_all_tools_same_resource_scope` still asserts "same scope → same serialized
  group," just expressed as `resource_scopes=("filesystem:file",)` on both sides).
- **Rekey every `meta` dict from `{name: _meta(...)}` to `{tc["id"]: _meta(...)}`.**
  Confirmed by reading `test_mixed_tool_types_with_complex_dependencies` in full: today's
  `meta = {"shell_run": _meta(...), "write_file": _meta(...), ...}` dict is built with
  string-literal tool names as keys, in the same order the corresponding `tc_*` variables
  are constructed via `_tc("shell_run")` etc. — this doc's port constructs each `tc_*`
  first (as today) and then builds `meta` using `tc_serial["id"]` etc. as keys (or, since
  `_tc(name)["id"] == f"call_{name}"` is deterministic, the literal string
  `"call_shell_run"` — this doc recommends using `tc_serial["id"]` rather than the
  literal string, to avoid the dict construction silently drifting out of sync with
  `_tc()`'s internal id format if that format ever changes).
- **`test_tool_with_no_metadata` becomes the natural home for a `MissingToolSpecError`
  case.** Today, `test_tool_with_no_metadata` (current line 136) tests what happens when
  a tool call has no entry in `meta` — under today's implementation this exercises the
  silent-default path (`meta = tool_meta.get(name)` returning `None`, then
  `scope=""`/`is_write=False` fallbacks). Under the new implementation, this exact
  scenario is precisely what raises `MissingToolSpecError` — so this doc changes this
  test's assertion from "the call ends up in the parallel/write-first bucket by default"
  to "calling `build_execution_groups()` raises `MissingToolSpecError`" — this is a
  behavior-changing port (the old and new *intended* behavior for this exact input are
  different), which is precisely the point: this scenario is the direct regression test
  for the plan's "raise, don't default" acceptance criterion, and belongs first in this
  file given its name already describes the exact condition.
- **`test_large_number_of_tools` extended with overlapping multi-scope entries, not
  replaced.** Per this file's "comprehensive/edge case" character (many tools, checking
  aggregate group-count/shape assertions rather than fine-grained per-tool checks), add
  a variant within the same test (or a sibling test) where a subset of the large batch
  shares overlapping `resource_scopes` (including at least one ancestor/descendant
  filesystem pair) to confirm the conflict-graph connected-component logic scales
  correctly and doesn't accidentally merge unrelated components at larger N.

## Alternatives considered

- Moving the `MissingToolSpecError` regression case to a brand-new test class instead of
  repurposing `test_tool_with_no_metadata`. Rejected: the existing test's name and intent
  ("what happens when a tool has no metadata") is already the exact scenario that now
  raises, and changing its assertion in place is more legible than adding a
  near-duplicate test with a different name — a reviewer diffing this file sees
  directly that the meaning of "no metadata" changed from "default" to "error," which is
  the whole point of this plan.
- Skipping new multi-scope edge cases in this specific file, on the reasoning that
  `test_tool_scheduler.py` already covers the "canonical" ancestor/descendant and
  `move_file` cases. Rejected: per the plan's Risk section, this rework is
  "CC=D(23)... genuine algorithmic redesign" and this file's stated purpose is edge-case/
  comprehensive coverage (large N, dense mixed batches) — the canonical single-pair cases
  belong in `test_tool_scheduler.py`, but this file's unique value is stress-testing the
  same logic at higher call counts and denser conflict graphs, which is exactly where a
  connected-component implementation bug (e.g. an off-by-one in graph traversal, or an
  accidental O(n²) exact-match assumption) would most likely surface.

## Implementation

### Target file: `tests/agent/test_tool_scheduler_comprehensive.py`

### Procedure

1. Update `_meta()` (current lines 16-27) to accept `resource_scopes: tuple[str, ...] =
   ()` instead of `resource_scope: str = ""`.
2. In `test_mixed_tool_types_with_complex_dependencies` (31), `test_empty_resource_scopes_and_no_scopes`
   (79), `test_complex_resource_scopes` (98), `test_all_tools_same_resource_scope` (118),
   `test_large_number_of_tools` (148), `test_single_tool_with_complex_metadata` (162):
   rekey each `meta` dict from tool-name-string keys to each `tc_*["id"]` value, and
   change every `resource_scope="..."` keyword to `resource_scopes=("filesystem:...",)`.
3. In `test_tool_with_no_metadata` (136): change the assertion from whatever
   default-bucket behavior it currently checks to asserting
   `pytest.raises(MissingToolSpecError)` around the `build_execution_groups()` call
   (adding a `import pytest` line if not already present, and importing
   `MissingToolSpecError` from `agent.tool_scheduler`).
4. Extend `test_large_number_of_tools` (or add a sibling test in the same class) with a
   subset of overlapping multi-scope calls, per Design.
5. Add a new test extending `test_mixed_tool_types_with_complex_dependencies`'s pattern
   with a `move_file`-style dual-scope call inside the same dense mixed batch.

### Method

Manual port, largely mechanical for the `_meta()` rename and dict-rekeying (applies
uniformly to 6 of 7 tests), with one behavior-changing edit
(`test_tool_with_no_metadata`) and two additive edge-case extensions guided by this
file's existing "comprehensive" test style (large N, dense mixed batches, aggregate
shape assertions).

### Details

- Confirmed via direct read (lines 1-175) and `rg -n "^def test_"
  tests/agent/test_tool_scheduler_comprehensive.py`: single class
  `TestBuildExecutionGroupsEdgeCases` (30) with 7 methods at lines 31, 79, 98, 118, 136,
  148, 162; file total 175 lines (matching the plan's citation).
- Confirmed `_meta()` (lines 16-27) has no `name` parameter — always constructs
  `ToolSpec(call_id="", name="", resource_scope=resource_scope, requires_serial=...,
  is_write=...)` — distinct from `test_tool_scheduler.py`'s `_meta()`, which does take a
  `name` parameter. This doc's Scope/Design sections explicitly preserve this
  file-specific detail rather than harmonizing the two helpers, since harmonizing test
  helpers across files is not part of this plan's stated changes.
- Confirmed via direct read of `test_mixed_tool_types_with_complex_dependencies` (lines
  31-77): `meta` dict keyed by string literals `"shell_run"`, `"write_file"`,
  `"edit_file"`, `"create_directory"`, `"read_text_file"`, `"list_directory"` — matching
  each `tc_*` variable's tool name exactly, confirming today's name-keying convention in
  this file (to be rekeyed by `tc["id"]` per this doc's Procedure).
- Coincidental prior-cycle filename match: `ls implementations/*test_tool_scheduler_comprehensive.py*
  implementations/done/*test_tool_scheduler_comprehensive.py* 2>/dev/null` returned 0
  hits — no prior-cycle doc exists for this exact filename at all (per the task's
  "Already-verified facts," this is consistent with the target symbols being absent from
  source today).

## Compatibility considerations

- This file's helpers (`_tc`, `_meta`) are local to this file, not shared with the other
  two scheduler test files (each defines its own copy) — changes here do not affect
  them, though all three must agree on the production signature.

## Security considerations

N/A — test-only file. The repurposed `test_tool_with_no_metadata` case is itself a
direct regression lock for the plan's fail-closed acceptance criterion.

## Rollback considerations

- Coupled to the paired `scripts/agent/tool_scheduler.py` implementation doc; revert
  together.
- No data/schema impact.

## Validation plan

- `uv run pytest tests/agent/test_tool_scheduler_comprehensive.py -v` (and jointly per
  the plan's Validation plan table with the other two scheduler test files) — call-id
  keying works; `test_tool_with_no_metadata` raises `MissingToolSpecError`; new
  multi-scope edge cases pass; every other pre-existing scenario still passes with
  equivalent intent.

## Out of scope

- `tests/agent/test_tool_scheduler.py`, `test_tool_scheduler_serialization.py` —
  covered by their own docs.
- `scripts/agent/tool_scheduler.py` itself — covered by its paired implementation doc.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-195246
- Related target files: tests/agent/test_tool_scheduler_comprehensive.py
