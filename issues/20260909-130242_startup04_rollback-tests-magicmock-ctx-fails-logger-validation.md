# `TestStartupRollback`'s bare `MagicMock()` context fails `Logger`'s strict `log_file` validation

## Priority
Medium

## Summary
9 tests in `TestStartupRollback` (`tests/agent/test_startup.py`) fail with
`ValueError: log_file must be a non-empty str, got: <MagicMock
name='mock.cfg.obs.audit_log_file' ...>`. The tests construct `ctx = MagicMock()`
without setting `ctx.cfg.obs.audit_log_file` to a real string, and the code path under
test now reaches far enough (through `ComponentInitializer.initialize()` ->
`build_agent_context()`) to actually construct a `Logger`, whose validation rejects the
unconfigured `MagicMock` attribute.

## Background
`Explicit in code`: `scripts/shared/logger.py`'s `_require_str` raises `ValueError` when
given a non-`str` value, including an unconfigured `MagicMock` attribute (which
`hasattr`/attribute access on a bare `MagicMock()` always satisfies, auto-creating a
child `MagicMock` rather than raising `AttributeError`). The call chain
`StartupOrchestrator.run()` -> `ComponentInitializer.initialize()`
(`scripts/agent/startup_component_init.py`) -> `build_agent_context()`
(`scripts/agent/factory.py`, `_build_audit_logger`) -> `Logger.__init__` reaches this
validation using `ctx.cfg.obs.audit_log_file`, which is an unconfigured `MagicMock`
attribute in these tests' bare `MagicMock()` context fixture.

## Problem
All 9 `TestStartupRollback` tests (all except
`test_rollback_on_partial_multi_server_failure`, tracked separately in `startup03`)
share this same `ValueError`. `Needs confirmation`: whether `orch.run()` reaching this
deep into component initialization (as far as constructing a real `Logger`) is a
recently-introduced behavior (possibly via the `ComponentInitializer` extraction,
commit `ea986372e`, "refactor: extract ComponentInitializer and delegate
StartupOrchestrator concerns") that these rollback tests were never updated for, or
whether this code path was already reachable before that extraction and the tests
simply never exercised it deeply enough to hit this validation until some other change
shifted execution order. This distinction affects whether the fix is "add a real
`audit_log_file` value to the test's `MagicMock` config" (if the code path is
correctly reaching this point) or something deeper (if reaching `Logger` construction
during a rollback test is itself unexpected).

## Reason for Change
9 tests in `TestStartupRollback` currently fail before their actual rollback-behavior
assertions run, providing no coverage of the rollback logic they are meant to verify.

## Implementation Intent
First confirm (via `git log`/`git blame` on the relevant call chain, or a minimal
reproduction) whether `orch.run()` reaching `Logger` construction during these rollback
tests is expected given the current `ComponentInitializer`-based startup flow. If
expected: set `ctx.cfg.obs.audit_log_file` (and any other required `cfg.obs.*` string
fields `Logger.__init__` validates) to a real string value in `TestStartupRollback`'s
shared context fixture. If the depth of code reached is itself unexpected for a
rollback-focused test (e.g. rollback tests are meant to fail before reaching full
component initialization), investigate why execution now proceeds further than these
tests' own scope assumes, rather than only patching the symptom.

## Target Files or Areas
- `tests/agent/test_startup.py` (`TestStartupRollback`'s shared context/fixture setup)
- `scripts/agent/startup_component_init.py` (`ComponentInitializer.initialize()`) —
  reference; confirm exact call depth reached
- `scripts/agent/factory.py` (`build_agent_context()`, `_build_audit_logger`) —
  reference; confirms which `cfg.obs.*` fields `Logger` requires
- `scripts/shared/logger.py` (`Logger.__init__`, `_require_str`) — reference only, not a
  modification target; its strict validation is confirmed correct and intentional

## Required Changes
- Confirm whether `TestStartupRollback` reaching `Logger` construction is expected given
  the current startup flow.
- If expected: set a real string value for `ctx.cfg.obs.audit_log_file` (and any other
  `Logger`-required `cfg.obs.*` field found during implementation) in the affected
  tests' shared fixture.
- If unexpected: investigate why rollback-scenario tests now execute this deep before
  their own rollback trigger fires, and correct the test's mocking depth accordingly
  (do not simply silence the symptom if the root scope is wrong).

## Constraints
Do not modify `scripts/shared/logger.py`'s validation — it is confirmed intentional and
correct; this is a test-fixture-configuration issue, not a validation defect.

## Acceptance Criteria
- [ ] Whether reaching `Logger` construction in these tests is expected is explicitly
  confirmed (not assumed) before implementing a fix
- [ ] All 9 listed `TestStartupRollback` tests no longer fail with the `log_file`
  `ValueError`
- [ ] No change to `scripts/shared/logger.py`

## Testing Expectations
- `uv run pytest "tests/agent/test_startup.py::TestStartupRollback" -q` — none of its
  10 tests should fail with the `log_file` `ValueError` after this fix (1 of the 10,
  `test_rollback_on_partial_multi_server_failure`, is tracked separately in `startup03`
  and may still need that issue's own fix applied first/alongside)

## Documentation Impact
N/A: test-fixture-configuration fix; no documented behavior change expected unless
investigation reveals the deeper call-depth question needs a design clarification, in
which case note the finding in `docs/05_agent_*` per `docs/00_index.md`'s task-scope
mapping.

## Out of Scope
- `TestStartupRollback::test_rollback_on_partial_multi_server_failure` — tracked
  separately in `startup03` (missing `auth_token`, a different cause).
- `TestStartupWorkflowPreflight`'s 6 failures — tracked separately as `startup05`.
- `TestStartupMemoryFailures::test_memory_injection_categorized_logging`'s 3 failures —
  tracked separately as `startup06`.
- Any change to `scripts/shared/logger.py`.

## Dependencies
N/A: none. Related to (but does not duplicate) `startup02`
(`issues/20260909-105724_startup02_recover-pending-approvals-test-targets-removed-module-attribute.md`)
and `startup03`, which cover different failures in the same file.

## Unresolved Questions
Whether `orch.run()` reaching `Logger` construction during a `TestStartupRollback`
scenario is expected current behavior (in which case the fix is fixture configuration)
or an unexpected depth of execution for a rollback-focused test (in which case the test
itself may need rescoping) — resolve via `git log`/`git blame` on
`ComponentInitializer.initialize()`'s call chain and a minimal reproduction before
implementing.

## AI Implementation Instruction
Resolve the Unresolved Question above before implementing — do not assume the fix is
"add a real `audit_log_file` string" without first confirming the code path reaching
`Logger` construction is itself expected for these tests' scenarios. Do not modify
`scripts/shared/logger.py`.
