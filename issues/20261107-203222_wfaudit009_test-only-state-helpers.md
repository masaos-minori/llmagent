# Remove or wire the test-only StateStore and attempt helpers

## Priority
Medium

## Summary
Several public helpers in the workflow persistence layer are used only by tests — attempt start/count helpers and two StateStore query methods — while production uses sibling private helpers for the same jobs. Collapse the duplicated API surface: wire the helpers to production, or delete them and move tests onto the production helpers.

## Background
Code review evidence (Verified; caller census by repository-wide grep):
- `attempt_ops.start_attempt`: callers are test files only; production creates attempts through the task-creation helper instead. A source comment even warns that the idempotency insert "is not attempt_ops.start_attempt" and must change together with it — two near-duplicate insert paths.
- `attempt_ops.count_attempts`: used only in test assertions; production uses the count-only helper.
- `StateStore.find_stale_running_attempts` and `StateStore.pending_tool_calls`: called only from tests; the engine calls the underlying ops functions directly.
- Precedent: `issues/done/20261103-134148_wfreview006_duplicate-attempt-crud-apis.md` (resolved) removed one duplicate CRUD pair and introduced the count-only helper; the remaining pairs listed here survived that pass.

## Problem
Two parallel ways to perform the same persistence operation exist, one production-real and one test-visible. They must be kept manually in sync (a code comment says so explicitly), and the test-only variants can drift or be mistaken for supported API.

## Reason for Change
Duplicate mutation paths in a persistence layer are a drift hazard that this project has already paid for once. Removing the test-only halves makes the production path the single tested path.

## Implementation Intent
For each helper decide: production-consume or delete. Default posture is delete-and-retarget-tests onto the production helper (the count-only helper, the task-creation attempt insert, and the ops-level query functions), so tests exercise the same code production runs.

## Target Files or Areas
- scripts/agent/workflow/attempt_ops.py
- scripts/agent/workflow/state_store.py
- scripts/agent/workflow/idempotency_ops.py (comment referencing the duplicate insert)
- tests/agent/workflow/test_workflow_state_store.py and other workflow tests using the helpers

## Required Changes
- Retarget tests from `start_attempt` / `count_attempts` / the two store query methods to the production helpers.
- Delete the test-only helpers; update the cross-reference comment in the idempotency insert accordingly.
- Confirm no doc or export references the removed names.

## Constraints
- Test coverage must not drop: each removed helper's assertions must survive on the production helper.
- Do not merge the idempotency insert and the attempt-creation insert unless a single-path design is explicitly proposed in the plan phase; this issue only removes the unused path.
- Keep the ops-level query functions (used by the engine) intact.

## Acceptance Criteria
- Repository-wide grep shows zero callers for each removed helper name.
- Workflow test packages pass with assertions preserved (same or stronger).
- The manual "change together" coupling comment is removed or reduced to one insert path.

## Testing Expectations
- Mutation-style check: after deletion, the tests that previously called the helpers must fail if the production helper's behavior breaks (i.e. they genuinely exercise it).
- Full workflow + orchestrator test packages green.

## Documentation Impact
None expected beyond removing references from module docstrings if any name the helpers. No operator-facing change.

## Out of Scope
- The adapter alias block and inert patches (separate issue).
- Facade bypass patterns (separate issue).
- Consolidating the two SQL insert paths (design decision, plan phase).

## Dependencies
- Builds on `issues/done/20261103-134148_wfreview006_duplicate-attempt-crud-apis.md` (resolved; re-verify current source).
- Independent of, but adjacent to, `issues/20261107-203221_wfaudit008_dead-alias-test-patches.md`; either order is safe.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
Verify the caller census against current source before deleting (the archived duplicate-removal issue already shifted some helpers). Prefer moving tests onto production helpers over keeping thin delegating wrappers.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203222
- **Related target files**: scripts/agent/workflow/attempt_ops.py, scripts/agent/workflow/state_store.py, scripts/agent/workflow/idempotency_ops.py, tests/agent/workflow/test_workflow_state_store.py
