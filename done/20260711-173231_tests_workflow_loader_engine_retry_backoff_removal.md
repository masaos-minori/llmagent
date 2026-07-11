# Implementation: `tests/test_workflow_loader.py` / `tests/test_workflow_engine.py` — Retry-Stage and Backoff Test Updates

## Goal

Update/add tests covering the removal of the `retry` stage from `default.json` and the narrowing of `_SUPPORTED_BACKOFF` to `{"fixed"}`, plus a regression guard ensuring `WorkflowEngine.run()` never invokes a `retry`-labeled stage.

## Scope

**In scope:**
- `tests/test_workflow_loader.py`: update `test_invalid_backoff_value_rejected` (or add a new test) to assert `"exponential"` is rejected; add/confirm a test loading the real `config/workflows/default.json` and asserting its `stages` set is exactly `{"plan", "execute", "verify"}`.
- `tests/test_workflow_engine.py`: add a regression test asserting `WorkflowEngine.run()` never calls `_run_stage`/`begin_stage_if_new` with `stage_id="retry"`; update/remove any existing test case that uses `backoff="exponential"` as a fixture input, replacing it with `backoff="fixed"` as the only tested value going forward.

**Out of scope:**
- `tests/test_workflow_models.py` — not named in this plan's Scope list; no test changes proposed here (the `models.py` comment-only fix has no behavior to test).
- Any production code change — this doc covers test-file changes only.
- Full-suite regression run details beyond what's listed in the plan's Validation plan table.

## Assumptions

- Confirmed by direct read (per plan Design §5): `tests/test_workflow_loader.py` currently has a `test_invalid_backoff_value_rejected`-style test exercising the loader's backoff validation branch; this test (or a sibling test) currently exercises or could exercise `"exponential"` as a case needing an update once it becomes invalid.
- Confirmed by direct read (per plan Design §5): `tests/test_workflow_engine.py` may have existing retry-delay tests; any that pass `backoff="exponential"` as a fixture must be updated since that value will now raise `WorkflowLoadError` at load time (if constructed via the loader) or is simply no longer a meaningful test case (if constructed directly as a `RetryPolicy` object bypassing the loader — confirm construction path at implementation time).
- `config/workflows/default.json` is loadable via the project's real path resolution (per `workflow_loader.py`'s `Path` resolution logic) from a test context, so a test can load the real file directly rather than a fixture copy.

## Implementation

### Target file

`tests/test_workflow_loader.py` and `tests/test_workflow_engine.py`

### Procedure

**`tests/test_workflow_loader.py`:**
1. Locate the existing backoff-validation test (e.g. `test_invalid_backoff_value_rejected`).
2. Update it (or add a new parametrized case) so that `"exponential"` is passed as the `backoff` value and the test asserts a `WorkflowLoadError` is raised with a message that lists only `"fixed"` as the accepted value (e.g. assert on the exception message content: `"must be one of: fixed"`).
3. Add a new test (e.g. `test_default_json_has_no_retry_stage`) that loads the real `config/workflows/default.json` via `WorkflowLoader` (not a fixture/temp file) and asserts `{s.id for s in loaded.stages} == {"plan", "execute", "verify"}`.

**`tests/test_workflow_engine.py`:**
4. Add a new regression test (e.g. `test_run_never_invokes_retry_stage`) that runs `WorkflowEngine.run()` against a representative task/config (mock or fixture, whichever pattern existing tests in this file use) and asserts, via a spy/mock on `_run_stage` (or `begin_stage_if_new`, whichever is the correct hook — confirm exact method name by reading `workflow_engine.py`), that it is never called with `stage_id="retry"` (or equivalent argument name).
5. Search the file for any existing test using `backoff="exponential"` as an input fixture; remove/replace that case so only `backoff="fixed"` is exercised going forward.

### Method

Standard `pytest` test edits: parametrize or duplicate existing test functions; use `unittest.mock.patch`/`MagicMock` or the file's existing mocking convention to spy on stage invocation. No production code changes.

### Details

- Follow existing test file conventions (fixture names, mock patterns, assertion style) already present in each file — do not introduce a new mocking library or pattern.
- Ensure the new `default.json`-loading test does not depend on test execution order or mutate the shared file.
- Keep test function names descriptive and snake_case, consistent with existing tests in each file.
- English-only comments/docstrings in test code per `rules/coding.md`.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to these test files:

| Check | Tool | Target |
|---|---|---|
| Tests | `uv run pytest tests/test_workflow_loader.py tests/test_workflow_engine.py tests/test_workflow_models.py -v` | All pass, including new/updated tests |
| Regression | `uv run pytest tests/ -k "workflow" -q` | No new failures |
| Type check | `uv run mypy scripts/agent/workflow/` | No new errors (tests dir covered by pre-commit mypy per `rules/coding.md`) |
