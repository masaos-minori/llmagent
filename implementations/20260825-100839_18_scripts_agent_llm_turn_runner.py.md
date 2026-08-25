## Goal
- Remove `_filter_disabled_tool_definitions()`'s no-op self-referential filtering,
  since `RuntimeToolRegistry.llm_tool_definitions()` already performs the real
  Stage-1 filtering this function was a redundant second pass over (REQ-008).

## Scope
- In scope: `LLMTurnRunner._filter_disabled_tool_definitions()` and its call site in
  `_stream_llm()`.
- **Important finding**: this method has two distinct responsibilities: (1) a live
  fallback to `ctx.cfg.tool.tool_definitions` when `registry is None`, and (2) a
  confirmed no-op loop when `registry` is not `None` (its own inline comment
  acknowledges this: "`visible_names` is redundant here — every entry from
  `llm_tool_definitions()` already has its name in `visible_names`"). REQ-008 removes
  only (2); (1) must be preserved.

## Assumptions
- `ctx.services_required.runtime_tools` is typed `RuntimeToolRegistry | None`
  (confirmed in `context.py`); `None` is a real, reachable state (e.g. uninitialized
  or failed discovery). The Plan does not ask to remove this fallback branch.

## Design decisions
- Remove the no-op portion only, inlining the equivalent of the live fallback
  directly at the call site in `_stream_llm()`:
  ```python
  registry = ctx.services_required.runtime_tools
  tool_defs = (
      registry.llm_tool_definitions()
      if registry is not None
      else ctx.cfg.tool.tool_definitions
  )
  ```
- This satisfies the Plan's instruction to remove the function and its call site
  while preserving the one behavior that was actually live.

## Alternatives considered
- Keeping the method but shrinking its body to just the fallback logic (dropping the
  no-op loop) — preserves the 4 existing direct-call tests unmodified, but does not
  literally match the Plan's "remove the function and its call site" wording. Viable
  fallback if test-compatibility is prioritized over literal removal at
  implementation time.
- Removing the method and call site entirely, treating the `None` fallback case as no
  longer needed — rejected; would require also changing the actual initialization
  guarantees around `runtime_tools`, which is outside REQ-008's scope.

## Implementation
### Target file
`scripts/agent/llm_turn_runner.py`

### Procedure
1. Replace the `self._filter_disabled_tool_definitions()` call in `_stream_llm()`
   with the inline equivalent shown in Design decisions.
2. Delete the `_filter_disabled_tool_definitions()` method definition entirely.
3. Confirm no now-unused imports remain (unlikely, since `dict[str, Any]`-shaped
   types are used elsewhere in the file too).

### Method
- Rewrite the call site first, then delete the method, to avoid an intermediate
  non-functional state.

### Details
- The 4 existing direct-call test cases in `tests/agent/test_llm_turn_runner.py`
  call `runner._filter_disabled_tool_definitions()` directly and will raise
  `AttributeError` once the method is deleted — they must be rewritten to assert on
  `_stream_llm()`'s resulting `tool_defs` value instead (see Validation plan). Flag
  this discrepancy to the Plan owner: the Plan's Test expectation ("existing cases
  continue to pass unmodified") cannot be met literally if the method itself is
  deleted; only the *behavior* (fallback + real filtering) is preserved.

## Compatibility considerations
- `docs/04_mcp_03_01_dispatch-and-routing.md` already accurately describes this
  no-op stage as it exists today; after removal, that description becomes stale and
  needs a follow-up correction (not performed here — documentation edits are outside
  this workflow's scope).
- `docs/adr/ADR-013-mcp-tool-availability-model.md` also references this as a known
  issue ("two-stage filtering design turned out to have a no-op second stage");
  removal resolves what that ADR describes, and the ADR text should be updated to
  match (separate follow-up, not performed here).

## Security considerations
- N/A: the no-op portion never filtered anything (self-referential), so removing it
  does not change what is exposed to the LLM. The real filter
  (`RuntimeToolRegistry.llm_tool_definitions()`, gated on `tool.enabled_for_llm`)
  already governs exposure and is unchanged.

## Rollback considerations
- Restoring the method definition and the original call site from the commit fully
  reverts this change. No persisted state or schema is affected.

## Validation plan
- Rewrite the 4 existing direct-call cases in `tests/agent/test_llm_turn_runner.py`
  to instead assert on the `tool_defs` value `_stream_llm()` produces: one case for
  `registry is not None` (asserts it equals `registry.llm_tool_definitions()`), one
  for `registry is None` (asserts it equals `ctx.cfg.tool.tool_definitions`,
  preserving the existing "regression" case's intent).
- `uv run pytest tests/agent/test_llm_turn_runner.py -v` after the rewrite.
- `uv run python tools/check_docs_consistency.py --domain mcp` — records whether the
  now-stale doc mentions above need a follow-up (the doc edits themselves are out of
  scope here).

## Out of scope
- Editing `docs/04_mcp_03_01_dispatch-and-routing.md` or
  `docs/adr/ADR-013-mcp-tool-availability-model.md` (flagged as follow-ups only).
- Revisiting whether `ctx.services_required.runtime_tools` can ever legitimately be
  `None` — out of scope for REQ-008.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Existing 4 direct-call tests require rewriting, not a no-op pass-through — see Implementation > Details |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: doc corrections tracked as follow-ups, not in this document's scope |

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
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/agent/llm_turn_runner.py
