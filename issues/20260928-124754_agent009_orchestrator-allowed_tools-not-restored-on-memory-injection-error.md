# Orchestrator allowed_tools override not restored when memory injection raises

## Priority
Medium

## Summary
`tests/agent/test_orchestrator.py::TestAllowedToolsOverride::test_original_config_restored_even_on_error` fails: when `handle_memory_injection` raises during `handle_turn`, the expected `RuntimeError` does not propagate, so the test's `pytest.raises(RuntimeError)` block never executes and the subsequent restore-assertion is never reached.

## Background
Discovered during the post-docs-reorg full-suite validation re-check (`implementations/20260925-111411_04_tests___full_suite_.md`, Execution Status Step 3). A prior run of this same procedure (20260927) filed `agent001`-`agent008` for a cluster of orchestrator/workflow-engine test failures, all since resolved (`issues/done/`); a re-run today found 4 remaining failures, of which this is one.

## Problem
`tests/agent/test_orchestrator.py:1266-1281` constructs an `Orchestrator` with `allowed_tools=["search_web"]`, sets `ctx.cfg.tool.allowed_tools = []`, patches `orch._conversation_manager.handle_memory_injection` to raise `RuntimeError("unexpected error")`, and calls `await orch.handle_turn("test")` inside `pytest.raises(RuntimeError)`. The test fails with `Failed: DID NOT RAISE <class 'RuntimeError'>` — `handle_turn` is apparently swallowing (or not propagating) the exception raised from memory injection, so the test's "config restored even on error" assertion can't be exercised as written. Captured logs show the workflow engine retrying and eventually halting ("Task test-task-id: execute halted after 3 attempts: unexpected error"), suggesting the error is caught and converted into a halted-workflow outcome somewhere in `handle_turn`'s call chain rather than propagating.

## Reason for Change
Either the test's premise is stale (an earlier change intentionally made `handle_turn` catch and handle this class of error instead of propagating it, in which case the test needs updating to assert the new behavior) or `handle_turn` is incorrectly swallowing an error that should propagate, and the config-restore-on-error path this test exists to guard is currently unverified.

## Implementation Intent
Read `Orchestrator.handle_turn` and its `_conversation_manager.handle_memory_injection` call site (`scripts/agent/orchestrator.py:255-275`) to determine whether an exception from `handle_memory_injection` is caught anywhere in the call chain (directly, or via the workflow engine's retry/halt handling referenced in the captured log). Confirm whether the intended contract is "propagate" (fix the code, or the interception layer, to re-raise) or "catch and halt" (update the test to assert the halted-outcome behavior and separately verify config restoration on that path).

## Target Files or Areas
- `scripts/agent/orchestrator.py` (`handle_turn`, `_handle_memory_injection`, lines ~255-275)
- `scripts/agent/workflow/workflow_engine.py` (retry/halt handling referenced in the captured failure log)
- `tests/agent/test_orchestrator.py` (`TestAllowedToolsOverride.test_original_config_restored_even_on_error`, line ~1266)

## Required Changes
- Confirm where the `RuntimeError` from `handle_memory_injection` is caught (workflow engine retry logic, or an orchestrator-level try/except).
- Depending on the confirmed intended contract, either restore propagation for this call site or update the test to match the now-caught-and-halted behavior while still asserting `allowed_tools` is restored on that path.

## Constraints
Must not change the documented retry/halt behavior for other workflow-engine error paths — scope the fix to this specific call site's error-propagation contract only.

## Acceptance Criteria
- The listed test passes (either by propagation being restored, or the test being updated to accurately reflect the current, intended error-handling contract).
- `ctx.cfg.tool.allowed_tools` restoration is verified under whichever error path is confirmed correct.

## Testing Expectations
Run `uv run pytest tests/agent/test_orchestrator.py -v -k TestAllowedToolsOverride`; run full suite once after the fix.

## Documentation Impact
N/A: no `docs/*.md` task-scope mapping identified for this internal orchestrator error-handling behavior; revisit if the investigation finds a documented contract that needs correcting.

## Out of Scope
The other 3 failures found in the same full-suite re-check (docs-quality golden pairs, eventbus ack ownership, ingestion embedding-failure test) — tracked as separate issues.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: whether "propagate" or "catch and halt" is the actually-intended contract for an error raised during memory injection — the test currently asserts the former, but the observed behavior and workflow-engine retry/halt logging suggest the latter is what the code currently does.

## AI Implementation Instruction
Determine the intended error-handling contract from the workflow engine's retry/halt design (not just from making the test pass) before deciding whether to fix the code or the test.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260928-124754
- **Related target files**: scripts/agent/orchestrator.py, tests/agent/test_orchestrator.py
