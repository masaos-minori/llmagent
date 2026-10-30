# Implementation Procedure: test_tool_loop_guard.py unavailable-repeat tests

## Goal

Cover the unavailable-repeat bound, hint emission, recovery clearing, and the
static-visibility authority invariant in `tests/agent/test_tool_loop_guard.py`
(REQ-003, REQ-004, REQ-007).

## Scope

**In scope:**
- `tests/agent/test_tool_loop_guard.py`: new test class(es) for row 04 behavior.

**Out of scope:**
- `tests/agent/test_tool_loop_guard_wiring.py` (characterization: untouched, green).

## Assumptions
- Verified at HEAD `124e340b4`: file exists with 39 tests exercising
  `ToolLoopGuard` through a mocked `AgentContext`; `test_tool_loop_guard_wiring.py`
  covers the runner wiring. Test-first: new tests fail until row 04 lands.

## Design decisions
- New class `TestUnavailableRepeat` (new):
  - counting: `observe_availability` (new) with hinted results (`server_key="srv"`, reasons
    `server_unavailable`) increments; at `count >= tool_empty_result_max_repeats`
    (config patched to e.g. 2), `check_unavailable_repeat()` returns the summary string
    exactly once and calls `ctx.diagnostics.save` once with
    `guard_type="unavailable_repeat"` (assert via the mocked diagnostics).
  - reset: an unhinted (`availability_hint=None`) result for `"srv"` clears the counter;
    a subsequent hinted result starts from 1 (models HALF_OPEN trial success = recovery,
    AC-3).
  - disabled: `tool_empty_result_max_repeats = 0` → `check_unavailable_repeat()` returns
    `None` regardless of counts.
  - key scoping: hints for two different `server_key`s count independently.
- New class `TestStaticFieldImmutability` (new) (REQ-007/AC-1): construct real
  `RuntimeTool` instances (`scripts/shared/runtime_tool.py:31`) + `RuntimeToolRegistry`
  (`scripts/shared/runtime_tool_registry.py:37`; test-layer import is contract-legal),
  snapshot static fields (dataclass equality), drive a real `McpServerHealthRegistry`
  through HEALTHY→DEGRADED→UNAVAILABLE→HALF_OPEN→HEALTHY transitions interleaved with
  `observe_availability` (new) calls, assert field-level equality of every `RuntimeTool` and
  that no LLM tool-definition mapping changed.

## Alternatives considered
- End-to-end REPL-level test: rejected — row 11 owns the turn-level integration; this
  file stays unit-scoped on the guard.

## Implementation
### Target file
`tests/agent/test_tool_loop_guard.py`

### Procedure
1. Keep all 39 existing tests byte-identical.
2. Append `TestUnavailableRepeat` (new) and `TestStaticFieldImmutability` (new).

### Method
- Reuse the file's existing mock-context helpers; construct genuine
  `ToolCallResult(..., availability_hint=DynamicAvailabilityHint(...))` fixtures rather
  than magic mocks for hint data.

### Details
- `server_key` on fixtures must be non-empty (`""` would collide with error-path
  results).

## Compatibility considerations
- The `guard_hint` diagnostics payload gains a new `guard_type` value; no existing
  diagnostics assertions are edited.

## Security considerations
- Assert the emitted hint equals the fixed module constant (guards against future
  server-text leakage into the hint channel).

## Rollback considerations
- Delete the two appended classes to revert.

## Validation plan
- `uv run pytest tests/agent/test_tool_loop_guard.py
  tests/agent/test_tool_loop_guard_wiring.py` — new classes fail before row 04, green
  after; 39 existing tests green throughout.

## Completion criteria
- Bound-at-limit firing, once-per-turn hint emission, recovery reset, disabled default,
  per-server keying, and static-field equality across health transitions all pass after
  rows 04/01.

## Out of Scope
- Row 04 implementation, runner integration test (row 11), diagnostics display test
  (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `TestUnavailableRepeat` (new) (fails before row 04 lands) | Completed | — | 20261030-205244 | TestUnavailableRepeat appended: bound-at-bound single save with guard_type=unavailable_repeat, recovery reset, limit-0 inert, per-server keying, half-open hint counting |
| 2 | Append `TestStaticFieldImmutability` (new) (REQ-007 field-equality) | Completed | — | 20261030-205244 | TestStaticFieldImmutability appended: real RuntimeTool/RuntimeToolRegistry snapshot equality (dataclass fields + llm_tool_definitions) across HEALTHY-DEGRADED-UNAVAILABLE-HALF_OPEN-HEALTHY interleaved with observe_availability |
| 3 | Confirm 39 existing tests and wiring suite green | Completed | — | 20261030-205244 | 51 passed (39 existing + 6 wiring + 6 new); existing test bodies byte-identical; ruff clean |

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
- **Requirement ID**: `REQ-003`, `REQ-004`, `REQ-007`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `tests/agent/test_tool_loop_guard.py`