# Orchestrator memory-injection error no longer propagates as RuntimeError under workflow-engine retry-halt

## Priority
Medium

## Summary
`tests/agent/test_orchestrator.py::TestAllowedToolsOverride::test_original_config_restored_even_on_error` fails: it expects `orch.handle_turn("test")` to re-raise a `RuntimeError` injected via `orch._conversation_manager.handle_memory_injection`'s `side_effect`, but no exception propagates (`Failed: DID NOT RAISE <class 'RuntimeError'>`). Evidence traced to the workflow engine's retry-then-halt mechanism now swallowing the error before it reaches the test's `pytest.raises` block, rather than a bug in the config-restore logic the test's assertion (never reached) actually targets.

## Background
Discovered as a pre-existing, unrelated full-suite failure while syncing an unrelated documentation change (NC-027 closure) via `git-commit-and-sync`. Confirmed to reproduce identically on `origin/master` alone (verified in an isolated worktree with no other changes applied), so this is not a regression introduced by that unrelated work — it already existed upstream.

`scripts/agent/orchestrator.py`'s `_process_turn()` (lines ~262-291) calls `await self._conversation_manager.handle_memory_injection(line)` directly inside a `with self._tool_override(self._allowed_tools):` block (lines ~269-291). `_tool_override()` (lines ~296-303) is a plain `@contextmanager` with a `finally` that restores `ctx.cfg.tool.allowed_tools` regardless of exceptions — this part of the mechanism the test targets looks structurally sound on inspection.

The captured log from the failing run shows the actual call path instead goes through `scripts/agent/workflow/workflow_engine.py::_run_stage_with_retry()`: it catches the injected `RuntimeError`, retries the stage up to `policy.max_attempts` (2 retries logged: "attempt 1 failed, retrying in 1s", "attempt 2 failed, retrying in 1s"), then raises `WorkflowHaltError(...) from exc` after exhausting attempts ("execute halted after 3 attempts"). `scripts/agent/workflow_engine_adapter.py::_handle_workflow_halt()` (lines ~358-368) then catches `WorkflowHaltError | WorkflowTimeoutError`, logs `"Turn halted by workflow engine: %s"`, resets workflow state, and invokes `self._on_error(exc)` if set — it does not re-raise. This means `handle_turn()` completes normally instead of propagating the original `RuntimeError` (or any exception) to the caller.

## Problem
The test was written assuming `handle_memory_injection`'s exception propagates directly out of `handle_turn()`. Under the current workflow-engine architecture, a stage failure is retried up to 3 times (each retry re-enters/re-exits `_tool_override()`, so the config-restore behavior itself appears unaffected by the retries) and then converted into a caught, logged `WorkflowHaltError` that is not re-raised — so `pytest.raises(RuntimeError)` never fires, and the test's actual intent (confirming config restoration on error) is never reached because the raise-expectation fails first.

## Reason for Change
Either the test is stale relative to an intentional architecture change (retry + swallow-and-halt is now the designed failure path for a workflow-engine-managed turn), or genuine turn-processing errors are now silently swallowed (logged only) where a caller previously received an exception — the latter would be a user/developer-visible regression (errors becoming invisible failures) worth confirming is intentional. Either way, a failing regression test on `master` masks real signal for future changes to this path until resolved one way or the other.

## Implementation Intent
Determine whether the retry-then-halt-and-swallow behavior in `workflow_engine.py`/`workflow_engine_adapter.py` is the intended, documented failure-handling contract for this call path (check for an ADR or design doc covering it — `docs/10_adr/ADR-004-environment-failure-handling-policy.md` did not obviously reference it on a quick search and may need updating either way). If intentional: update the test to assert the halt path instead (e.g. assert `ctx.workflow.active is False` / the logged halt / `_on_error` invocation, and separately verify `ctx.cfg.tool.allowed_tools` restoration without relying on `pytest.raises`). If not intentional — i.e. errors should still surface to the caller after halting — fix `_handle_workflow_halt()` (or its caller) to re-raise after performing its cleanup, and only then confirm the test's original expectation still holds.

## Target Files or Areas
- `tests/agent/test_orchestrator.py` (`TestAllowedToolsOverride::test_original_config_restored_even_on_error`)
- `scripts/agent/workflow/workflow_engine.py` (`_run_stage_with_retry`, retry policy, `WorkflowHaltError`)
- `scripts/agent/workflow_engine_adapter.py` (`_handle_workflow_halt`)
- `scripts/agent/orchestrator.py` (`_process_turn`, `_tool_override`) — for confirming config-restore is unaffected, not expected to need a code change
- `docs/10_adr/ADR-004-environment-failure-handling-policy.md` — check whether it already documents this retry/halt contract

## Required Changes
- Confirm (via existing ADRs, commit history, or the retry-policy config in `config/workflows/*.json`) whether retry-then-halt-and-swallow is the intended contract for a workflow-managed turn stage failure.
- If intentional: rewrite the failing test to assert against the halt path's observable effects instead of a raised `RuntimeError`, while still verifying `ctx.cfg.tool.allowed_tools` is restored.
- If unintentional: add re-raising (or an equivalent surfaced-error mechanism) to `_handle_workflow_halt()` or its caller, then re-verify the test passes unchanged.

## Constraints
- Do not remove or weaken the retry policy itself (`policy.max_attempts`, backoff) — this issue is about whether the final halt is silently swallowed or surfaced, not about retry behavior.
- Any change to `_handle_workflow_halt()`'s re-raise behavior must not break the two adjacent, currently-passing tests in the same class (`test_original_allowed_tools_restored_after_turn`, `test_allowed_tools_none_leaves_config_unchanged`) or other callers relying on `handle_turn()` not raising on a normal halt (e.g. an approval-required halt, per the adjacent `_handle_approval_required` handler in the same file).

## Acceptance Criteria
- `tests/agent/test_orchestrator.py::TestAllowedToolsOverride::test_original_config_restored_even_on_error` passes, asserting behavior consistent with whichever contract is confirmed correct (updated test, or a code fix plus the original assertion).
- The full `tests/agent/` suite passes with no new failures, including the workflow-engine and workflow-engine-adapter test files.
- If an ADR gap is found, either a doc citation is added confirming the existing design, or a Needs Confirmation / new ADR note is filed — do not leave the ambiguity unresolved silently.

## Testing Expectations
Run `uv run pytest tests/agent/test_orchestrator.py -v` and `uv run pytest tests/agent/workflow/ -v` targeted, then the repository-defined full suite (`uv run pytest`) per `rules/toolchain.md`, to confirm no regression in workflow-halt handling elsewhere.

## Documentation Impact
If the investigation confirms retry-then-halt-and-swallow is the intended contract and it is not yet documented, `docs/10_adr/ADR-004-environment-failure-handling-policy.md` (or the relevant agent/workflow doc per `docs/00_governance/00_index.md`'s task-scope mapping) should note it as a Known behavior. If undocumented and confirmed unintentional (a bug), file it as a code-behavior gap per `rules/coding.md` "Current behavior" classification rather than adding a doc note describing the bug as-is.

## Out of Scope
- The unrelated eventbus ACK-endpoint authorization issue filed separately (see Dependencies) — different subsystem.
- Broader redesign of the workflow engine's retry/backoff policy.

## Dependencies
N/A: none. (A separate, unrelated pre-existing failure — `tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_principal_ownership_validation` — was discovered at the same time and filed as its own issue; the two do not depend on each other.)

## Unresolved Questions
- Is silently swallowing a halted workflow's original exception (logging only, no re-raise) the intended, documented contract, or an oversight? This determines whether the fix is a test update or a code change (see Implementation Intent) — needs an owner/maintainer decision or a documented precedent to resolve with confidence.

## AI Implementation Instruction
Do not assume either the test or the implementation is "correct" without first checking for an existing ADR or design decision covering workflow-halt error propagation — search `docs/10_adr/` and `docs/23_agent/` before choosing a fix direction. Keep the diff scoped to whichever single side (test or `_handle_workflow_halt`) the investigation identifies as wrong; do not change both defensively. If no documented precedent exists either way, stop and report the ambiguity (per this issue's Unresolved Questions) rather than picking a direction unilaterally.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260929-111152
- **Related target files**: tests/agent/test_orchestrator.py, scripts/agent/workflow/workflow_engine.py, scripts/agent/workflow_engine_adapter.py, scripts/agent/orchestrator.py
