# Workflow loader coerces config values with bare int() and leaves timeout_sec unvalidated

## Priority
Medium

## Summary
`WorkflowLoader` reads `timeout_sec`, `max_attempts`, and `backoff_sec` from workflow JSON through bare `int()` coercions. `bool`, float, and numeric-string values are silently accepted (and floats truncated), `timeout_sec` has no range check at all, and a non-numeric value raises a bare `ValueError` instead of `WorkflowLoadError`. Replace the coercions with explicit type and range validation.

## Background
Adversarial code review of `scripts/agent/workflow/` (2026-11-03). Evidence:

- Confirmed: `scripts/agent/workflow/workflow_loader.py:114` `max_attempts = int(policy["max_attempts"])`, `:117` `backoff_sec = int(policy["backoff_sec"])`, `:151` `timeout_sec=int(s["timeout_sec"])`, `:158-159` a second `int()` coercion pair when constructing `RetryPolicy`.
- Confirmed: `rules/coding.md` "Type-coercion policy" (line 114 ff.) prohibits bare `int()`/`float()`/`list()` coercions in config loading because they silently accept wrong types; the documented pattern is `get_typed`-style validation. The policy text names `*_models.py` config loaders explicitly; `workflow_loader.py` is a config loader outside that naming — see Unresolved Questions.
- Confirmed: guards exist for `max_attempts >= 1` (`workflow_loader.py:115-116`) and `backoff_sec >= 0` (`:118-119`), but there is no type or range guard for `timeout_sec`: `_validate` only checks required stage keys (`:105-108`). `int(True)` yields `1`, `int("30")` yields `30`, `int(3.9)` yields `3`, and `timeout_sec: 0` or a negative value passes validation.
- Confirmed: `timeout_sec` feeds `asyncio.timeout(timeout)` at `scripts/agent/workflow/workflow_engine.py:305,323`; a `0` or negative timeout makes every stage attempt fail immediately with a stage timeout, and `begin_stage_if_new` leases `timeout + 30` (`workflow_engine.py:314`).
- Confirmed: `int("abc")` raises `ValueError`, which is not converted to `WorkflowLoadError`. `Orchestrator.__init__` catches only `(WorkflowLoadError, FileNotFoundError)` (`scripts/agent/orchestrator.py:128-134`), so a malformed numeric value escapes as an unwrapped `ValueError`, unlike every other validation failure. The preflight path is inconsistent again in the other direction: `scripts/agent/services/workflow_schema.py:38-41` catches `(WorkflowLoadError, ValueError, TypeError, AttributeError)` and wraps it as `RuntimeError`.
- Confirmed test gap: `tests/agent/workflow/test_workflow_loader.py` covers missing keys, duplicate stage ids, missing required stages, and unknown `retry_on` kinds, but has no case for a non-integer, boolean, fractional, zero, or negative `timeout_sec`/policy number.

## Problem
Invalid workflow configuration is either silently coerced into a different runtime behavior (float truncation, `True` as `1`, string as int) or accepted as-is (`timeout_sec: 0` → every stage instantly times out), and the failure mode differs per call site depending on which exception leaks. Config validation is supposed to be the boundary that rejects bad config before any process starts.

## Reason for Change
The loader is the single validation gate for `config/workflows/*.json` (startup preflight, orchestrator init, and `validate.py` CLI all route through `WorkflowLoader.load()`). Leaving coercions there contradicts the repository's stated type-coercion policy and produces inconsistent error contracts across the three call sites.

## Implementation Intent
Validate each numeric field explicitly at the JSON boundary: require an actual `int` (reject `bool`, `float`, `str`), apply range checks (`timeout_sec >= 1`, existing `max_attempts >= 1`, `backoff_sec >= 0`), and raise `WorkflowLoadError` with the offending field and value for every rejection. Remove the duplicated second coercion in the `RetryPolicy`/`StageDefinition` construction once validation is authoritative.

## Target Files or Areas
- `scripts/agent/workflow/workflow_loader.py`
- `tests/agent/workflow/test_workflow_loader.py`

## Required Changes
- Add a shared typed-int validation helper (or reuse the repository `get_typed`-style pattern from `rules/coding.md`) for `timeout_sec`, `max_attempts`, `backoff_sec`.
- Reject `bool`, `float`, and `str` values for these fields with a `WorkflowLoadError` naming the field and bad value.
- Add a `timeout_sec >= 1` range check.
- Drop the redundant `int()` coercions at `workflow_loader.py:151,158-159` once validated values are guaranteed to be `int`.
- Add loader tests for: boolean `timeout_sec`, string numeric `timeout_sec`, fractional value, zero/negative value, and the same classes on `max_attempts`/`backoff_sec`; assert `WorkflowLoadError` (not `ValueError`) in every case.

## Constraints
- Error type contract: every config rejection must surface as `WorkflowLoadError` so all three call sites (`orchestrator.py:128-134`, `services/workflow_schema.py`, `workflow/validate.py`) keep a single exception contract; the current `ValueError` widening in `workflow_schema.py:38-41` may then be narrowable — narrow it only if tests confirm nothing else produces `ValueError` there.
- `config/workflows/default.json` and any deployed workflow files must keep loading unchanged (current values are valid integers).
- The `TypedDict` declarations (`_StageJson`, `_RetryPolicyJson`) document intent but are not runtime-enforced; keep them consistent with the new checks.

## Acceptance Criteria
- A workflow JSON with `"timeout_sec": 0`, `"timeout_sec": "120"`, `"timeout_sec": true`, or `"max_attempts": 2.5` fails `WorkflowLoader.load()` with a `WorkflowLoadError` naming the field.
- No bare `int()` coercion remains in `workflow_loader.py`.
- All three loader call sites surface the same error type for bad numbers.
- Loader tests cover the new rejection cases; full workflow test suite and lint/type checks stay green.

## Testing Expectations
- Unit tests in `tests/agent/workflow/test_workflow_loader.py` for each rejected value class and range edge.
- Regression check that the shipped `config/workflows/default.json` still loads.
- Lint/type checks per `rules/toolchain.md`.

## Documentation Impact
State the accepted value types and ranges for workflow definition fields (`timeout_sec >= 1`, `max_attempts >= 1`, `backoff_sec >= 0`, strict `int`) in the workflow/engine documentation that describes `config/workflows/*.json`, and record the config rejection behavior (`WorkflowLoadError` with field name).

## Out of Scope
- Schema or migration changes to `workflow.sqlite`.
- Engine behavior changes (`asyncio.timeout` handling, lease margin).
- The `require_approval` removal already enforced at `workflow_loader.py:121-125`.

## Dependencies
- Related (same validation gate, different problem): `issues/20261031-135607_wfschema001_schema-preflight-creates-database.md` (open) touches the preflight path in `scripts/agent/services/workflow_schema.py`; if both land, the preflight exception contract must stay consistent.

## Unresolved Questions
- 不明: whether the `rules/coding.md` Type-coercion policy (worded for `*_models.py` config loaders) is intended to bind `workflow_loader.py` directly; the rationale plainly applies, but the plan should record the scope decision rather than assume it.
- 不明: whether `timeout_sec >= 1` is the right lower bound (vs a configurable minimum); current stage values are 10-120.

## AI Implementation Instruction
Validate types and ranges before constructing `StageDefinition`/`RetryPolicy`; never coerce after validation. Keep all rejection paths inside `WorkflowLoadError`. Do not touch engine timeout semantics.

## Traceability
- **Workflow phase**: `python-code-review` (adversarial review of `scripts/agent/workflow/` and integration points), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261103-134147
- **Related target files**: `scripts/agent/workflow/workflow_loader.py`, `tests/agent/workflow/test_workflow_loader.py`
