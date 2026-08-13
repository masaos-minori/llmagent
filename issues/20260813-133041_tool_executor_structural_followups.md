# Structural follow-ups for ToolExecutor / ToolTransportInvoker (gate-chain extraction, invoke merge, typed args)

## Priority
Low

## Summary
Three related, higher-risk structural improvements were identified for
`scripts/shared/tool_executor.py` and `scripts/shared/tool_transport_invoker.py` during their
refactor cycles but deliberately not implemented because each requires its own dedicated
behavior-lock/characterization-test cycle rather than folding into a single-file,
zero-behavior-change pass.

## Reason for Change
Found during behavior-preserving refactor cycles on `scripts/shared/tool_executor.py` and
`scripts/shared/tool_transport_invoker.py` (2026-08-13). Grouped into one issue because all
three concern the same tight file pair and share a common risk profile (ordering-sensitive gate
checks feeding MCP tool routing) — per issue-creator grouping rules, tasks affecting tightly
coupled files with a shared review/test strategy belong together.

## Implementation Intent
Each of the three sub-items below needs its own characterization test pinning current behavior
*before* any structural change, given the special-case sensitivity of this file pair
(MCP routing path, per `prompts/04_refactor.md` Special Cases).

1. **Gate-chain helper**: `ToolExecutor._raw_execute` calls `_check_startup_mode` /
   `_check_health` / `_ensure_lifecycle_ready` in a specific order that
   `test_transport_success_full_path` asserts exactly (`["resolve", "health", "lifecycle",
   "transport"]`). A shared "gate chain" helper could reduce duplication but risks silently
   reordering the checks.
2. **Invoke-with-gates merge**: `ToolTransportInvoker.invoke()` and `ToolExecutor._raw_execute()`
   share a near-duplicate try/except + `record_success`/`record_transport_error` pattern. Merging
   requires its own blast-radius mapping since `ToolTransportInvoker` may have other subclasses.
3. **Typed args DTO**: replacing `dict[str, Any]` for `args` parameters across `execute`,
   `_raw_execute`, `_execute_with_cache`, `_execute_with_stampede_protection` with a typed DTO
   touches every call site across `scripts/agent/` — a cross-cutting migration, not a
   single-file refactor.

## Target Files or Areas
- `scripts/shared/tool_executor.py`
- `scripts/shared/tool_transport_invoker.py`
- Callers across `scripts/agent/` (factory, tool_runner, repl) for item 3

## Required Changes
- Item 1: add a characterization test asserting exact gate-call order before any transformation,
  then extract the gate-chain helper preserving that order.
- Item 2: map `ToolTransportInvoker`'s subclasses and their test coverage before merging.
- Item 3: scope a dedicated migration plan (likely via `requires/` → `plans/` given its breadth)
  before touching any call site.

## Acceptance Criteria
- Each sub-item, if implemented, preserves the existing gate-call order and existing test
  pass/fail results with no new failures.
- Item 3 is not attempted without a full-repo blast-radius review and a dedicated plan.

## Testing Expectations
Full existing test suite for both files plus new characterization tests pinning gate order
(item 1) and the merged helper's contract (item 2) before implementation; full repo test suite
for item 3 given its breadth.

## Documentation Impact
None required unless item 3 changes a documented public contract.

## Out of Scope
- Do not implement any of these three items speculatively; each requires explicit approval and
  its own behavior-lock cycle per this project's refactor discipline.

## AI Implementation Instruction
Treat this issue as three independently schedulable follow-ups, not one task. For item 1 or 2,
run `skills/python-refactoring/workflow.md` Phase 1 (Dependency Mapping) and Phase 2 (Behavior
Lock) in full before any transformation. For item 3, do not start without first producing a
`requires/` document given its cross-cutting scope.
