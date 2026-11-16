## Goal

Make `retry_on` a required `retry_policy` loader key and reject an absent key, while preserving supported-kind validation, unknown-kind rejection, and Decision 2 (an explicit empty list `retry_on: []` is valid and means "retry nothing"). Shipped `default.json` uses `["exception"]`, so shipped behavior is unchanged (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_REQUIRED_POLICY_KEYS` is the single gate that decides which `retry_policy` keys are mandatory; adding `retry_on` there is the only functional change needed to make it required.
- `_validate_retry_on` is called unconditionally by `load()` after the key-presence check, so removing its absent-key fallback does not leave an unguarded path.
- Decision 2 (Plan `Design`): only the absent-key fallback is removed; element-kind validation and the empty-list case are preserved.

## Design decisions
- **Keep `_validate_retry_on` responsible for both presence-independent validation and (currently) the absent default**: after adding `retry_on` to `_REQUIRED_POLICY_KEYS`, the loader rejects an absent key first (via the missing-keys check), then `_validate_retry_on` validates the present value. The empty-list `[]` still passes through to `tuple([])` ("retry nothing"); only the `raw is None` branch is replaced with a raise.

## Alternatives considered
- **Leaving the absent-key fallback in place**: would let a definition omit `retry_on` and silently fall back to `("exception",)`, defeating REQ-001. Rejected.

## Implementation
### Target file
`scripts/agent/workflow/workflow_loader.py`
### Procedure
1. `REQ-001`: add `"retry_on"` to `_REQUIRED_POLICY_KEYS`.
2. `REQ-001`/`REQ-002`: remove the absent-key fallback in `_validate_retry_on` so it raises `WorkflowLoadError` naming `retry_policy.retry_on`.
3. `REQ-002`: keep supported-kind validation and unknown-kind rejection; preserve the empty-list (`[]`) = "retry nothing" case.
4. Update the `_RetryPolicyJson` docstring to state `retry_on` is required.
### Method
Two small edits: set membership and one conditional branch, plus a docstring word.
### Details
- Line 57: change
  `_REQUIRED_POLICY_KEYS = {"max_attempts", "retry_wait_sec"}`
  to
  `_REQUIRED_POLICY_KEYS = {"max_attempts", "retry_wait_sec", "retry_on"}`.
  This makes the missing-keys check at `_validate` line 152 (`missing_p = _REQUIRED_POLICY_KEYS - retry_policy_data.keys()`) reject an absent `retry_on` before `_validate_retry_on` is reached.
- Lines 74-76 in `_validate_retry_on`: replace
  ```python
      raw = policy.get("retry_on")
      if raw is None:
          return ("exception",)
  ```
  with
  ```python
      raw = policy["retry_on"]
  ```
  The key is guaranteed present by the `_REQUIRED_POLICY_KEYS` check, so subscripting is safe and an absent key now surfaces as the missing-keys `WorkflowLoadError` from step 1. The subsequent `isinstance(raw, list)` / kind checks (lines 77-85) are unchanged and still validate `[]` (returns `tuple([])`) and reject unknown kinds.
- Lines 26-28 in the `_RetryPolicyJson` docstring: change "``retry_on`` is optional." to "``retry_on`` is required."

## Compatibility considerations
Additive for shipped config (which supplies `retry_on: ["exception"]`). A definition that previously omitted `retry_on` now fails load with a `WorkflowLoadError` identifying `retry_policy.retry_on` — this is the intended contract enforcement.

## Security considerations
N/A: no untrusted-input handling beyond existing validation.

## Rollback considerations
Revert the commit; the change is two set-membership/branch edits and a docstring word.

## Validation plan
- Load JSON without `retry_policy.retry_on` → expect `WorkflowLoadError` naming it.
- Load unknown kind (`["halt"]`) → expect rejection (unchanged).
- Load explicit empty `retry_on: []` → expect success ("retry nothing").
- Load `config/workflows/default.json` → expect success with exception-only retry.
- Command: `uv run pytest tests/agent/workflow/test_workflow_loader.py`.

## Completion criteria
- `_REQUIRED_POLICY_KEYS` contains `"retry_on"`.
- An absent `retry_on` raises `WorkflowLoadError`; an empty `[]` loads successfully; unknown kinds still rejected.
- `test_workflow_loader.py` has a rejection test naming `retry_policy.retry_on` and an empty-`retry_on` semantics test.

## Out of Scope
Changing `max_attempts`/`retry_wait_sec` required-key handling; the model-layer empty-stage guard (seq 01); the loader's `'stages' must be a non-empty list` guard (kept intact per Decision 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by `tests/agent/workflow/test_workflow_loader.py` (seq 09). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs handled by seq 03. |

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
- **Requirement ID**: `REQ-001` (make `retry_on` a required loader key), `REQ-002` (empty-`retry_on` semantics)
- **Source issue**: `issues/20261116-114753_compat001_workflow-definition-strict-contract.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261116-214100_compat001_workflow-definition-strict-contract.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-005004
- **Related target files**: `scripts/agent/workflow/workflow_loader.py`
