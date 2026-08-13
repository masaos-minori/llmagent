## Goal

Update `ToolConfig.serial_tool_calls`'s docstring in `scripts/agent/config_dataclasses.py`
(current line 161's comment, field at line 161-... — see Details) to describe the
single-engine, `force_serial` semantics this plan introduces: the field is no longer a
selector between two execution engines (`_execute_with_dag()` vs. the now-deleted
`_execute_standard()`); it is now one input into `build_execution_groups()`'s single
DAG planner.

## Scope

In scope: the one-line comment immediately preceding
`serial_tool_calls: bool = False` (current line 161 comment, field itself at line 161)
inside `ToolConfig`. Text-only change; no field name, type, or default-value change.

Out of scope: every other field in `ToolConfig` (e.g. `tool_definitions` at line
190-194, `tool_concurrency_limits` at line 173 — unrelated existing mechanisms not
touched by this plan); the field's runtime read site in
`scripts/agent/tool_runner.py::execute_all_tool_calls()` (current line 527, becoming the
`force_serial=ctx.cfg.tool.serial_tool_calls` argument — covered by the paired
`tool_runner.py` doc, not this one).

## Assumptions

- This docstring update lands in the same commit as the paired `tool_runner.py` and
  `tool_scheduler.py` changes — a reader should never see this comment describing
  "single-engine, force-serial semantics" while `_execute_standard()` still exists in
  source, or vice versa.
- `serial_tool_calls`'s field name, type (`bool`), and default (`False`) are unchanged
  by this plan — only its *meaning* changes (from "select an engine" to "force one
  phase per call" via `force_serial`), per the plan's Scope: "Update `ToolConfig.serial_tool_calls`
  docstring... to describe the single-engine, force-serial semantics" (no field/type/
  default change mentioned).

## Design decisions

- **Docstring only, no behavioral code change in this file.** The plan's Affected-areas
  table states explicitly: "Update `ToolConfig.serial_tool_calls` (line 161) docstring
  only — no field/type/default change." The field is read at exactly one site
  (`tool_runner.py:527` today), "now feeding `force_serial` instead of branch
  selection" — this doc's only job is to make the comment match that new read-site
  semantics.
- **State the new semantics precisely: "one sequential phase per call," not
  "runs everything one at a time" vaguely.** Per the plan's Design section, when
  `force_serial=True`, `build_execution_groups()` "short-circuits all of the above:
  emit one phase per call, in original order, each phase a single-call
  `ScheduledGroup(sequential=True, reason="forced_serial")`" — the comment should name
  this exact mechanism so a future reader understands the field now flows into the
  planner rather than picking between two functions.

## Alternatives considered

N/A — the plan's Affected-areas table specifies this exact change (docstring text only,
no field/type/default change); no alternative implementation shape was considered.

## Implementation

### Target file: `scripts/agent/config_dataclasses.py`

### Procedure

1. Locate the `serial_tool_calls` field inside `ToolConfig` (confirmed via direct read:
   `# When True, tool calls execute one by one instead of asyncio.gather()` immediately
   precedes `serial_tool_calls: bool = False` at line 161).
2. Replace the comment with wording describing the new semantics, e.g.:
   ```python
   # Forces build_execution_groups() to emit one sequential phase per call (in
   # original order, reason "forced_serial") instead of its normal phase-building/
   # conflict-graph logic. No longer selects between two execution engines — both
   # force_serial=True and False now run through the single DAG path
   # (agent/tool_runner.py::_execute_with_dag()).
   serial_tool_calls: bool = False
   ```
3. Leave the field declaration itself (`serial_tool_calls: bool = False`) unchanged.

### Method

Manual, single-comment-block edit — no code logic change, so no test impact beyond a
docstring-diff review (mirrors the sibling Issue-02 doc's approach for the same file's
`tool_definitions` field comment).

### Details

- Confirmed via direct read of `scripts/agent/config_dataclasses.py` (lines 150-194):
  `ToolConfig` is a `@dataclass` with docstring "Tool execution, caching, approval
  policy, and prompt settings."; `serial_tool_calls: bool = False` sits at line 161,
  immediately preceded by the one-line comment `# When True, tool calls execute one by
  one instead of asyncio.gather()`.
- Confirmed the field's current comment describes *what* the flag does today (serial
  vs. gather) but not *how* — it predates the two-engine split this plan removes, and
  will become actively misleading once `_execute_standard()` no longer exists, since a
  reader could infer the flag still picks a whole separate code path.
- Note: a second, unrelated Issue-02 doc (`plans/20260813-184037_plan.md`) already
  updates this same file's `tool_definitions` field comment (lines 190-194) for a
  different reason (removing an outdated "fallback" claim); that change and this one are
  independent, non-overlapping edits to the same file and may land in either order.

## Compatibility considerations

- Comment-only change; no behavioral or type impact on any consumer of
  `serial_tool_calls` — confirmed sole runtime read site is
  `scripts/agent/tool_runner.py::execute_all_tool_calls()` (current line 527), covered
  by the paired `tool_runner.py` doc's Procedure.
- Test fixtures across `tests/agent/` that set `serial_tool_calls` via `_cfg(**overrides)`-
  style helpers are unaffected — they pass a `bool` value, unchanged in shape.

## Security considerations

N/A — comment-only change, no behavior affected.

## Rollback considerations

- Trivial: revert the comment text. No functional dependency on this change from any
  other file in this plan — unlike the `tool_scheduler.py`/`tool_runner.py` pair (which
  must roll back together because their contracts are coupled), this comment can be
  reverted independently without breaking anything.

## Validation plan

Manual review only (no test asserts on docstring content); confirm via
`grep -n "force_serial\|one sequential phase" scripts/agent/config_dataclasses.py` that
the new wording is present. Include this file in the plan's full `uv run ruff check`
pass to confirm the comment doesn't break line-length or formatting lint rules.

## Out of scope

- Any change to `serial_tool_calls`'s field name, type, or default value.
- `tool_definitions`'s own docstring (lines 190-194) — a separate, independent edit
  tracked by the Issue-02 sibling plan, not this one.
- `tool_concurrency_limits` (line 173) — an unrelated existing mechanism, explicitly
  named out of scope by this plan's own Out-of-Scope section.
- Any `docs/*.md` update — out of scope for this document-only phase.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184423_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-001129
- Related target files: config_dataclasses.py
