## Goal

Verify that `tests/agent/test_tool_approval_risk.py` requires no code change from this
plan, despite being listed among the "Update for run_approval_checks() signature
change" test files — confirm by inspection that it does not call `run_approval_checks()`
at all.

## Scope

In scope: verification only of `tests/agent/test_tool_approval_risk.py` (366 lines) —
confirm it exercises `classify_risk()` / `build_preview()` / operation-type
classification, none of which change in this plan.

Out of scope: any edit to this file.

## Assumptions

- `agent.tool_policy.classify_risk()` and `agent.tool_result_formatter.build_preview()`
  (this file's actual imports, per `from agent.tool_policy import classify_risk as
  _classify_risk` / `from agent.tool_result_formatter import build_preview as
  _build_preview`) are untouched by this plan — neither module is named anywhere in the
  plan's Scope, Affected areas, or Implementation steps as a change target.

## Design decisions

- **Confirmed via direct grep.** `grep -n "check_approval\|run_approval_checks"
  tests/agent/test_tool_approval_risk.py` returns no matches at all — this file never
  touches either function; its module docstring (line 5: "Covers _classify_risk(),
  _build_preview(), and _classify_operation_type().") independently corroborates this.

## Alternatives considered

N/A — verification-only doc.

## Implementation

### Target file

`tests/agent/test_tool_approval_risk.py`

### Procedure

1. Run `grep -n "check_approval\|run_approval_checks" tests/agent/
   test_tool_approval_risk.py` — confirm zero matches (already confirmed for this doc).
2. Run `grep -n "^from agent" tests/agent/test_tool_approval_risk.py` — confirm imports
   are limited to `agent.tool_policy.classify_risk` and
   `agent.tool_result_formatter.build_preview`, both outside this plan's Scope.
3. No edit required. Leave the file as-is.

### Method

Verification via `grep`.

### Details

- No further grounding needed beyond the two grep results above; this file's subject
  matter (risk classification and preview text formatting) has no dependency on tool
  call preparation, JSON parsing, or `RuntimeToolRegistry` lookups.

## Compatibility considerations

N/A — no change made.

## Security considerations

N/A — no change made.

## Rollback considerations

N/A — no change made, nothing to roll back.

## Validation plan

`uv run pytest tests/agent/test_tool_approval_risk.py -v` — all tests pass unchanged.

## Out of scope

- `classify_risk()`, `build_preview()`, `_classify_operation_type()` — none touched by
  this plan.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184037_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-235947
- Related target files: test_tool_approval_risk.py
