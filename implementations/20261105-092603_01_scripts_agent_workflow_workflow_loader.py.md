## Goal
- Make `WorkflowLoader` accept only strict `int` values for `timeout_sec`, `max_attempts`, and `backoff_sec`, enforce `timeout_sec >= 1`, report every rejection as `WorkflowLoadError` naming the field, and leave no bare `int()` coercion in the module (`REQ-001`, `REQ-002`, `REQ-003`; tests `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit
- Edits `scripts/agent/workflow/workflow_loader.py` and adds tests in the companion `tests/agent/workflow/test_workflow_loader.py`.
- The `except` tuple of `check_workflow_schema` and the validate CLI are not changed.

## Assumptions
- Shipped `config/workflows/default.json` holds valid integers (checked in the Plan); no test or config in the repository passes a float, string, or bool for these fields to the loader (`rg` over `tests/` and `config/` found none).
- `get_typed` is not reused: it raises `ValueError` and its `isinstance(value, int)` check accepts `bool`.
- Existing tests match the messages `max_attempts must be >= 1` and `backoff_sec must be >= 0`; the range messages keep those substrings.
- A non-object element of `stages` still raises `AttributeError` (out of scope, Plan UNK-01).

## Design decisions
- One private helper validates a value with `type(value) is int` (rejects `bool`, `float`, `str`, `None`) and a minimum, and raises `WorkflowLoadError`.
- `_validate` is the only place that checks; `load()` then reads the validated values directly because the JSON `TypedDict` fields are already typed `int`.

## Alternatives considered
- Wrapping `get_typed` and converting `ValueError`: rejected (accepts `bool`, adds a second exception path).
- Having `load()` re-run the helper: rejected because it validates the same value twice.

## Implementation
### Target file
`scripts/agent/workflow/workflow_loader.py`

### Procedure
1. Add the helper `_require_int` (new) next to `_validate_retry_on`, with parameters `(value: object, label: str, minimum: int) -> int`.
2. In `_validate`, inside the existing loop over `stages_data` that checks required keys, call `_require_int(stage["timeout_sec"], f"stages[{i}].timeout_sec", 1)` (new) after the missing-keys check.
3. In `_validate`, replace `int(policy["max_attempts"])` and `int(policy["backoff_sec"])` with `_require_int(policy["max_attempts"], "retry_policy.max_attempts", 1)` (new) and `_require_int(policy["backoff_sec"], "retry_policy.backoff_sec", 0)` (new), and delete the two now-redundant `< 1` and `< 0` comparisons and their raises.
4. In `WorkflowLoader.load`, remove the three `int(...)` calls (`timeout_sec=s["timeout_sec"]`, `max_attempts=policy_data["max_attempts"]`, `backoff_sec=policy_data["backoff_sec"]`).

### Method
- The helper raises `WorkflowLoadError(f"{label} must be an integer, got {type(value).__name__}: {value!r}")` for a wrong type, and `WorkflowLoadError(f"{label} must be >= {minimum}")` for a value below the minimum.
- Keep the `retryable` handling (`bool(...)`) as is: the Issue and Plan cover numeric fields only, and `bool(...)` there is not an `int()` coercion.
- Keep `_StageJson` and `_RetryPolicyJson` unchanged.

### Details
- After the change `rg "int\(" scripts/agent/workflow/workflow_loader.py` must find no call; a mention in a docstring is acceptable only if it is not a call.
- Update the docstring of `_validate` to say it also checks numeric types and ranges.

### Companion test files
- `tests/agent/workflow/test_workflow_loader.py`
  - Procedure: add a class `TestWorkflowLoaderNumericValidation` (new). Build each case from `copy.deepcopy(_VALID)` (add `import copy`) and write it with `_write_json`. `test_non_int_timeout_sec_rejected` (new): parametrize `bad` over `True`, `"120"`, `2.5`, `None` and set the `execute` stage's `timeout_sec`; expect `WorkflowLoadError` with `match="timeout_sec"`. `test_non_positive_timeout_sec_rejected` (new): parametrize over `0` and `-1`; expect `match="timeout_sec must be >= 1"`. `test_non_int_policy_number_rejected` (new): parametrize the field over `max_attempts` and `backoff_sec` and the value over `True`, `"3"`, `2.5`, `None`; expect `WorkflowLoadError` naming the field.
  - Validation: run the new class first and confirm the cases fail on the current code (the loader coerces or raises `ValueError`); then confirm they pass after the source change, together with the existing `test_default_json_has_no_retry_stage`, `test_shipped_default_workflow_has_no_require_approval_key`, `test_negative_backoff_sec_rejected`, and `test_invalid_retry_policy_rejected`; `uv run pytest tests/agent/workflow/test_workflow_loader.py -v`.

## Compatibility considerations
- A malformed number now raises `WorkflowLoadError` instead of `ValueError`; `Orchestrator.__init__`, `check_workflow_schema`, and `validate.py` all handle `WorkflowLoadError` (the preflight tuple already included it).
- A deployed workflow file with a float, string, or bool number stops loading; the shipped file is valid, and the validate CLI check below covers a deployed one before a restart.

## Security considerations
- The change tightens validation of an operator-edited config file at the trust boundary; the error text echoes the offending value, which is configuration, not a secret.

## Rollback considerations
- Revert the commit; no persisted data depends on the new messages.

## Validation plan
- `uv run pytest tests/agent/workflow tests/agent/test_repl_health.py`; before the source edit, `rg "ValueError" tests/agent/workflow tests/agent/test_repl_health.py` to confirm no test relies on the loader's `ValueError`.
- `uv run ruff check scripts/agent/workflow/workflow_loader.py tests/agent/workflow/test_workflow_loader.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `uv run python tools/check_module_size.py`.
- `uv run python -m agent.workflow.validate config/workflows/default.json` prints OK.

## Completion criteria
- `"timeout_sec": 0`, `"120"`, `true`, `2.5`, and `"max_attempts": 2.5` each fail with `WorkflowLoadError` naming the field; no bare `int()` call remains; `default.json` loads unchanged; all existing loader tests pass.

## Out of Scope
- Engine timeout or lease behavior, `check_workflow_schema`'s `except` tuple, non-object `stages` elements, and the docs update (procedure `_03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the rejection tests to the companion file and confirm they fail on the current code | Pending | — | — | |
| 2 | Add `_require_int` (new), the `timeout_sec` check, and remove the `int()` calls | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the validate CLI | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (strict int), `REQ-002` (`timeout_sec >= 1`), `REQ-003` (no bare `int()`), `REQ-004` (rejection tests)
- **Source issue**: issues/20261103-134147_wfreview003_workflow-loader-bare-int-coercion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-085821_wfreview003_workflow-loader-bare-int-coercion.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092603
- **Related target files**: `scripts/agent/workflow/workflow_loader.py`, `tests/agent/workflow/test_workflow_loader.py`
