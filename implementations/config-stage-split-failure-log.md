# config-stage-split — Failure Log (Phase 1 expected failures)

Release unit `config-stage-split` (Procedures 01/02/05/06). Phase 1 (Procedures 03/04)
records the new tests failing on pre-change code per REQ-005 before the release-unit
production procedures land.

## Procedure 03 — `TestCheckConfigStage` (tests/agent/test_startup_validation.py)
- Approach: add `_run_check_config` helper + `TestCheckConfigStage` (6 tests) + runtime regression test.
- Observed (pre-change): `check_config` does not exist → `AttributeError` on every `TestCheckConfigStage` test; runtime regression test sees `check_routing_drift` still called by `check_services`.
- Reason: production method `StartupValidationPipeline.check_config` not yet added (Phase 2). Expected REQ-005 failure.
- Command: `uv run pytest tests/agent/test_startup_validation.py -k TestCheckConfigStage -q`
- Result (recorded 20261104): 6 failed, 11 deselected. Every `TestCheckConfigStage` test raises
  `AttributeError: 'StartupValidationPipeline' object has no attribute 'check_config'`; the runtime
  regression test fails because `check_services` still calls `check_routing_drift`. Expected REQ-005
  failure; production method lands in Procedure 01 (Phase 2).

## Procedure 04 — `TestConfigStageOrdering` (tests/agent/test_startup_rollback.py)
- Approach: stub `_check_config` in autouse fixture + two `run()` tests (order, abort-before-spawn).
- Observed (pre-change): order test's call list lacks the config label; abort test never raises → both fail.
- Reason: `run()` does not yet call `_check_config` (Phase 3). Expected REQ-005 failure.
- Command: `uv run pytest tests/agent/test_startup_rollback.py -k TestConfigStageOrdering -q`
- Result (recorded 20261104): 2 failed. Order test yields `['start','verify','services','prompt']`
  (missing leading `config`) because `run()` does not yet call `_check_config`; abort test never
  raises. Expected REQ-005 failure; orchestrator wiring lands in Procedure 02 (Phase 3).
