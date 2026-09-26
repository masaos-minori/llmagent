# tool_executor_routing KeyError srv in set_session_id

## Priority
Medium

## Summary
Both tests in `tests/shared/test_tool_executor_routing.py::TestSetSessionId` fail with `KeyError: 'srv'`, indicating the session-id-injection code path looks up a `'srv'` key in a dict/config that does not contain it in the test's setup.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
- `test_session_id_injected_into_http_transport_header`: `KeyError: 'srv'`
- `test_set_session_id_empty_string_does_not_inject_header`: `KeyError: 'srv'`

Both tests in the same class fail identically, suggesting either a shared fixture/setup no longer provides a `'srv'` key that `set_session_id` (or a function it calls) expects, or the lookup key itself changed (e.g. renamed from `'srv'` to something else) without the fixture/tests being updated.

## Reason for Change
This blocks test coverage for HTTP-transport session-id header injection (including the empty-string no-op case), a routing/tool-executor behavior.

## Implementation Intent
Read `set_session_id`'s current implementation to find the exact dict/object it indexes with `'srv'`, and read the test class's fixture/setup to see what keys it actually provides. Determine whether the key was renamed in production (fix: update the fixture) or the test fixture is simply missing a required key it always needed (fix: add it).

## Target Files or Areas
- Shared tool-executor routing module (confirm exact path, likely `scripts/shared/tool_executor_routing.py` or similar) defining `set_session_id`
- `tests/shared/test_tool_executor_routing.py`

## Required Changes
- Confirm the exact source of the `'srv'` key lookup and the test fixture's current dict contents.
- Align whichever side is stale (fixture or lookup key).

## Constraints
N/A: none

## Acceptance Criteria
- Both listed tests pass.

## Testing Expectations
Run `tests/shared/test_tool_executor_routing.py`; run full suite once after the fix.

## Documentation Impact
N/A: internal routing key, no expected documentation impact.

## Out of Scope
Other unrelated failing tests from the same full-suite run.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: whether `'srv'` was renamed in production code or the test fixture always required it and recently lost it (e.g. via an unrelated fixture refactor).

## AI Implementation Instruction
Read `set_session_id`'s current source and the test class's `setUp`/fixture before editing either side. Confirm which side is authoritative before changing anything.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/shared/test_tool_executor_routing.py
