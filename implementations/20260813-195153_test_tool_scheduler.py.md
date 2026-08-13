## Goal

Update `tests/agent/test_tool_scheduler.py` (390 lines today) so every existing test of
`build_execution_groups()` uses call-id-keyed `tool_meta` dicts and `ToolSpec.resource_scopes`
(plural) instead of today's name-keyed dict and singular `resource_scope`, porting every
existing scenario with equivalent intent, then add the new ancestor/descendant and
dual-scope (`move_file`) cases and a `MissingToolSpecError`-raised-on-missing-spec case
from the plan's requirement.

## Scope

In scope: `tests/agent/test_tool_scheduler.py` only —
- the module-level `_tc()` and `_meta()` test helpers (current lines 10-29), updated so
  `_tc()` continues to produce `{"function": {"name": name}, "id": f"call_{name}"}`
  (already call-id-bearing, convenient for the rework) and `_meta()` is renamed/retyped
  to build a `ToolSpec` with `resource_scopes: tuple[str, ...]` instead of
  `resource_scope: str`;
- every test class (`TestBuildExecutionGroupsEmpty`, `TestRequiresSerialBarrier`,
  `TestResourceScopeGrouping`, `TestMixedScenarios`, `TestConcurrentGroups`,
  `TestToolRunnerDefaultSpec`), updated to build `tool_meta` dicts keyed by each `_tc()`
  call's `"id"` field rather than its `"name"` field;
- new tests: filesystem ancestor/descendant overlap causing serialization despite
  unequal scope strings; a `move_file`-style call with two independent
  `resource_scopes` entries each independently conflicting with a different other call;
  a call whose `call_id` is absent from `tool_meta` raising `MissingToolSpecError`.

Out of scope: `tests/agent/test_tool_scheduler_comprehensive.py`,
`test_tool_scheduler_serialization.py` (separate target files/docs), and any change to
`scripts/agent/tool_scheduler.py` itself (covered by its own doc — this doc only updates
tests to match).

## Assumptions

- The production rework described in the paired `scripts/agent/tool_scheduler.py` doc
  lands in the same commit as this test update; these tests are written against the
  *target* call-id-keyed signature, not today's name-keyed one, and would fail against
  unmodified source. Confirmed against the "Already-verified facts" for this task:
  today's `_meta()` helper builds `ToolSpec(call_id="", name=name, resource_scope=...,
  ...)` (singular field, name defaulting to `""` in this file's variant — see Details),
  and `resource_scopes`/`MissingToolSpecError` do not exist anywhere yet, so this file's
  current content is unmodified/valid against today's source and must not be rewritten
  until the paired implementation lands.
- `MissingToolSpecError` is importable from `agent.tool_scheduler` (per the paired
  `tool_scheduler.py` doc's Design decision to define it in that module) — this test
  file imports it alongside `build_execution_groups` in its `from agent.tool_scheduler
  import (...)` line.
- The existing `_tc(name)` helper's `"id": f"call_{name}"` shape (already present today,
  confirmed by reading the file) is sufficient as a call-id source for every ported
  test — no test needs a *second* call with the same tool name and therefore no
  call-id collision risk exists in the ported scenarios; new dual-scope/multi-call tests
  introduced by this doc use distinct names (and therefore distinct ids) per call to
  avoid ambiguity.

## Design decisions

- **Rename `_meta()` to build multi-scope `ToolSpec`s, keep its call signature
  additive.** Today's signature is `_meta(name="", *, resource_scope="", requires_serial=False,
  is_write=False)`. The updated helper becomes `_meta(name="", *, resource_scopes=(),
  requires_serial=False, is_write=False)` — a straight field rename in the helper's
  keyword, with callers passing a tuple (e.g. `resource_scopes=("filesystem:/a",)`)
  instead of a bare string. Existing call sites that passed `resource_scope="/a"`
  become `resource_scopes=("filesystem:/a",)` (adding the kind prefix per the plan's
  Design section scope-string shape) — this is the single most repetitive mechanical
  edit across the file, applied consistently at every `_meta(...)` call site.
- **`tool_meta` dict construction switches from `{name: _meta(...)}` to `{tc["id"]:
  _meta(...)}`.** Since `_tc(name)` already produces a deterministic `f"call_{name}"`
  id, most ported tests can build their `tool_meta` dict as `{f"call_{name}":
  _meta(...)}` directly, or more robustly as `{tc["id"]: _meta(...)}` after constructing
  `tc = _tc(name)` first — the latter is preferred for clarity and to avoid the two
  literal id-construction expressions (`_tc()`'s internal one and a test's copy)
  silently drifting apart.
- **New ancestor/descendant test uses `"filesystem:"`-prefixed strings on both sides.**
  Per the plan's Design section scope-string shape (`f"{kind}:{value}"`) and the
  requirement's "Tests" section (referenced by the plan but not itself a target file for
  this doc), add a test with one call scoped `("filesystem:/data",)` (a directory-level
  operation) and another scoped `("filesystem:/data/sub/file.txt",)` (a descendant path,
  `is_write=True` on at least one side) asserting both end up in the same serialized
  group despite the scope strings not being equal.
- **New `move_file` dual-scope test uses two independent scope entries.** Per the plan's
  Design section ("`move_file`'s two scopes must each independently conflict with
  unrelated calls") and Affected-areas table (`resource_scope_keys=["source",
  "destination"]`), construct a `ToolSpec` with `resource_scopes=("filesystem:/a",
  "filesystem:/b")` and two other single-scope calls, one overlapping `/a` and one
  overlapping `/b` but not each other — assert all three end up in one connected
  component (the `move_file` call bridges what would otherwise be two separate
  components).
- **`MissingToolSpecError` test omits the call's id from `tool_meta` entirely** (rather
  than mapping it to `None` or a sentinel), matching the paired implementation doc's
  described lookup-and-raise-on-miss behavior (`tool_meta.get(tc["id"])` returning
  `None` today would fall through to the old silent default; the new code path checks
  for absence and raises before reaching any default logic).

## Alternatives considered

- Leaving `_meta()`'s parameter named `resource_scope` (singular) but changing its type
  to accept either a string or tuple, auto-wrapping a bare string into a one-tuple for
  backward compatibility with un-migrated call sites. Rejected: this would let some call
  sites silently continue using the old singular convention without a kind prefix,
  defeating the purpose of porting every scenario to the new shape explicitly and risking
  masking a real mismatch between test expectations and the new `ToolSpec.resource_scopes`
  field's actual declared type (`tuple[str, ...]`, no `str` union per the sibling
  `tool_spec.py` doc).
- Testing `MissingToolSpecError` only in one of the three scheduler test files (to avoid
  duplication). Rejected: the plan's Validation plan table lists all three
  `test_tool_scheduler*.py` files together as needing to demonstrate "raises on missing
  `ToolSpec`" — this doc places at least one such case in `test_tool_scheduler.py`
  specifically because it is the primary/foundational scheduler test file (holds
  `TestRequiresSerialBarrier`/`TestResourceScopeGrouping`, the two rule categories most
  directly affected by the missing-spec change); the other two files' docs may add
  additional missing-spec cases relevant to their own specific scenarios (edge cases,
  serialization-event fields) without this being pure duplication.

## Implementation

### Target file: `tests/agent/test_tool_scheduler.py`

### Procedure

1. Update `_meta()` (current lines 16-29) to accept `resource_scopes: tuple[str, ...] =
   ()` instead of `resource_scope: str = ""`, passing it through to `ToolSpec(...)`
   unchanged in shape otherwise.
2. Across `TestBuildExecutionGroupsEmpty` (34), `TestRequiresSerialBarrier` (53),
   `TestResourceScopeGrouping` (87), `TestMixedScenarios` (178), `TestConcurrentGroups`
   (237), `TestToolRunnerDefaultSpec` (331): change every `tool_meta` dict literal from
   `{name: _meta(...)}` to `{tc["id"]: _meta(...)}` (constructing `tc = _tc(name)` first
   where not already done), and every `_meta(resource_scope="...")` call to
   `_meta(resource_scopes=("filesystem:...",))` (or the appropriate kind prefix for any
   non-filesystem scenario already present in the file — confirmed by reading
   `TestResourceScopeGrouping` that today's scopes are simple path-like strings without
   kind prefixes, consistent with the current single-string implementation).
3. Add a new test class `TestMultiScopeConflicts` (or extend `TestResourceScopeGrouping`)
   with: an ancestor/descendant filesystem case, and a `move_file`-style dual-scope case
   bridging two otherwise-separate components, per Design.
4. Add a new test (e.g. in a `TestMissingToolSpec` class) asserting
   `build_execution_groups([tc], {})` (empty `tool_meta`, or a `tool_meta` missing the
   call's id) raises `MissingToolSpecError`.
5. Update the `from agent.tool_scheduler import (...)` line (current line 7) to also
   import `MissingToolSpecError`.

### Method

Manual, mechanical-where-possible port: the `_meta()` signature change and the
`{name: ...}` → `{tc["id"]: ...}` dict-key change apply uniformly across all six
existing test classes, so this is largely a consistent find/replace guided by reading
each class's current bodies, followed by hand-written new tests for the genuinely new
scenarios (ancestor/descendant, dual-scope, missing-spec) that have no current
counterpart to port from.

### Details

- Confirmed via direct read of the file's header (lines 1-40) and
  `rg -n "^def test_|^class Test" tests/agent/test_tool_scheduler.py`: six test classes
  — `TestBuildExecutionGroupsEmpty` (34), `TestRequiresSerialBarrier` (53),
  `TestResourceScopeGrouping` (87), `TestMixedScenarios` (178), `TestConcurrentGroups`
  (237), `TestToolRunnerDefaultSpec` (331) — spanning lines 34-390 (file total 390
  lines, matching the plan's citation).
- Today's `_tc(name)` helper (lines 10-11) already returns
  `{"function": {"name": name}, "id": f"call_{name}"}` — i.e. every test call already
  carries a deterministic, distinct `"id"` field, which is what makes the call-id
  rekeying mechanically straightforward in this particular file (not every test file in
  this plan necessarily has this property already — confirmed separately for the other
  two scheduler test files in their own docs).
- Today's `_meta()` helper (lines 16-29) builds `ToolSpec(call_id="", name=name,
  resource_scope=resource_scope, requires_serial=requires_serial, is_write=is_write)` —
  confirming the singular `resource_scope` field is in active use in this file today
  (not yet migrated), consistent with the "Already-verified facts" that
  `resource_scopes` (plural) does not exist anywhere yet.
- Coincidental prior-cycle filename match: `ls implementations/*test_tool_scheduler.py*
  implementations/done/*test_tool_scheduler.py* 2>/dev/null` returned 1 hit from an
  unrelated prior cycle (this plan's specific symbols are confirmed absent from this
  file today, per above).

## Compatibility considerations

- Every ported test changes its own literal `tool_meta` dict construction; no test in
  this file is consumed by or shares fixtures with `test_tool_scheduler_comprehensive.py`
  or `test_tool_scheduler_serialization.py` (each defines its own local `_tc()`/`_meta()`-
  equivalent helpers, confirmed by reading each file's header) — so this file's changes
  do not risk breaking the other two test files' internals, though all three must agree
  on the production `build_execution_groups()` signature they're testing against.

## Security considerations

N/A — test-only file.

## Rollback considerations

- Coupled to the paired `scripts/agent/tool_scheduler.py` implementation doc; revert
  together.
- No data/schema impact.

## Validation plan

- `uv run pytest tests/agent/test_tool_scheduler.py -v` (and, per the plan's Validation
  plan table, jointly with the other two scheduler test files:
  `uv run pytest tests/agent/test_tool_scheduler.py tests/agent/test_tool_scheduler_comprehensive.py tests/agent/test_tool_scheduler_serialization.py -v`)
  — call-id keying works; raises on missing `ToolSpec`; multi-scope/ancestor-descendant/
  `move_file` cases pass; every pre-existing scenario in this file's six classes still
  passes with equivalent intent.

## Out of scope

- `tests/agent/test_tool_scheduler_comprehensive.py`, `test_tool_scheduler_serialization.py`
  — covered by their own docs.
- `scripts/agent/tool_scheduler.py` itself — covered by its paired implementation doc.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-195153
- Related target files: tests/agent/test_tool_scheduler.py
