# `PromptSetup.setup_prompt()`'s logger is a method-local variable, making it unpatchable by existing tests

## Priority
Medium

## Summary
`TestStartupMemoryFailures::test_memory_injection_categorized_logging` (3 parameterized
cases) in `tests/agent/test_startup.py` fails with `AssertionError: Expected
'error'/'warning'/'info' to have been called once. Called 0 times.`, even though the
captured stderr shows the expected log message was actually emitted. Confirmed cause:
`PromptSetup.setup_prompt()` (`scripts/agent/startup_prompt_setup.py`) constructs its
`Logger` as a method-local variable rather than a module-level or instance attribute, so
`patch("agent.startup.logger")` (the tests' patch target) has no effect on it —
structurally similar to `diagstore01`'s wrong-mock-target defect, but here there is no
correct module-level target to patch at all.

## Background
Commit `02a7ecce6` ("refactor: extract PromptSetup and delegate _setup_prompt +
_classify_memory_failure") moved `_setup_prompt()`'s logic into
`PromptSetup.setup_prompt()` (`scripts/agent/startup_prompt_setup.py`). That method
constructs `Logger(__name__, "/opt/llm/logs/agent.log")` (or equivalent) as a local
variable inside its own body, rather than obtaining it from a module-level
`logger = logging.getLogger(__name__)`-style binding (the pattern used elsewhere in this
codebase, e.g. `rules/coding.md` Logging convention) or receiving it via constructor
injection.

## Problem
`tests/agent/test_startup.py`'s `test_memory_injection_categorized_logging` patches
`agent.startup.logger`, expecting to intercept the logger used during memory-injection
failure classification. Since `PromptSetup.setup_prompt()` creates its own logger
locally rather than referencing any patchable module- or instance-level binding, this
patch target has never had any effect since the `02a7ecce6` extraction — there is
currently no way for a test to inject a mock logger into this code path via
`unittest.mock.patch`.

## Reason for Change
3 test cases verifying that memory-injection failures are logged at the correct
severity (error/warning/info depending on exception type) currently provide no real
coverage — the assertions pass or fail based on a patch target that was never wired to
anything, not on the actual logging behavior.

## Implementation Intent
Two viable approaches — choose after confirming which better matches this codebase's
existing conventions for similarly-extracted components (survey 2-3 sibling extracted
classes, e.g. `ComponentInitializer`, `ApprovalRecovery`, for their own logger-handling
pattern before deciding):
1. **Switch the test to `caplog`-based verification** instead of mock-patching a
   logger — assert on `caplog.records`' level and message content, which works
   regardless of how the logger is constructed internally. Requires no production code
   change.
2. **Make `PromptSetup`'s logger a module-level or constructor-injected attribute**
   instead of a method-local variable, matching this codebase's stated logging
   convention (`rules/coding.md` Logging convention), then patch that binding. Requires
   a production code change to `startup_prompt_setup.py`.
Do not implement both approaches — pick one based on which sibling extracted
components already do, to keep the fix consistent with existing patterns rather than
introducing a third convention.

## Target Files or Areas
- `tests/agent/test_startup.py`
  (`TestStartupMemoryFailures::test_memory_injection_categorized_logging`)
- `scripts/agent/startup_prompt_setup.py` (`PromptSetup.setup_prompt()`) — target only
  if Implementation Intent's option 2 is chosen
- `scripts/agent/startup_component_init.py`, or another already-extracted startup
  component module (reference only — survey for the existing logger-handling
  convention before choosing an approach)

## Required Changes
- Decide between `caplog`-based test verification (test-only) or promoting
  `PromptSetup`'s logger to a patchable module-level/instance binding (test + small
  production change), based on surveying sibling extracted components' existing
  convention.
- Update `test_memory_injection_categorized_logging`'s 3 parameterized cases to match
  the chosen approach.

## Constraints
Do not introduce a new, third logging-access convention if either `caplog` verification
or a module-level logger already matches an existing sibling component's pattern —
prefer consistency with what already exists over a novel solution.

## Acceptance Criteria
- [ ] The chosen approach (`caplog` or patchable logger) is picked based on confirmed
  precedent from at least one sibling extracted startup component, not invented
  independently
- [ ] `uv run pytest "tests/agent/test_startup.py::TestStartupMemoryFailures::test_memory_injection_categorized_logging" -q`
  passes for all 3 parameterized cases, verifying actual log severity/content
- [ ] If option 2 (production change) is chosen, `scripts/agent/startup_prompt_setup.py`'s
  externally observable behavior (log file path, format) is unchanged — only the
  logger's construction/binding location changes

## Testing Expectations
- `uv run pytest "tests/agent/test_startup.py::TestStartupMemoryFailures::test_memory_injection_categorized_logging" -q`
  — all 3 cases pass with genuine (not coincidental) coverage of log severity per
  exception type
- If option 2 is chosen: `uv run pytest tests/agent/test_startup.py -q` — confirm no
  regression in other `PromptSetup`-related tests in this file

## Documentation Impact
N/A: internal test/logging-wiring fix; no documented external behavior change.

## Out of Scope
- `TestStartupRollback`'s failures — tracked separately as `startup03`/`startup04`.
- `TestStartupWorkflowPreflight`'s 6 failures — tracked separately as `startup05`.
- Any change to the memory-injection failure-classification logic itself
  (`_classify_memory_failure`, also extracted by `02a7ecce6`) — only the logger-access
  mechanism is in scope.

## Dependencies
N/A: none. Related to (but does not duplicate) `startup02`/`startup03`/`startup04`/`startup05`,
which cover different failures in the same file.

## Unresolved Questions
Which of the two Implementation Intent approaches (`caplog` vs. promoting the logger to
a patchable binding) matches this codebase's existing convention for extracted startup
components — resolve by surveying sibling components (e.g. `ComponentInitializer`,
`ApprovalRecovery`) before implementing, not by picking arbitrarily.

## AI Implementation Instruction
Survey at least one sibling extracted startup component's logger-handling pattern
before choosing an approach — do not default to whichever seems simplest without that
check, since introducing a third, inconsistent convention would itself be new test
debt. Do not change `_classify_memory_failure`'s own classification logic.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260909-130343
- **Related target files**: see Target Files or Areas above
