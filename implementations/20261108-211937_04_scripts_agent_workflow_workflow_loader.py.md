## Goal
Make `scripts/agent/workflow/workflow_loader.py` accept and validate only the renamed retry-policy key `retry_wait_sec` — JSON DTO field and docstring, `_REQUIRED_POLICY_KEYS`, the `_require_int` validation call, and the `RetryPolicy` construction (`REQ-003`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 4 only: `scripts/agent/workflow/workflow_loader.py`.

## Assumptions
- Landing order: after `implementations/20261108-151141_01_scripts_agent_workflow_workflow_loader.py.md` (wfaudit004, adds `_require_dict` and stage-shape checks in the `_validate` region) and after procedure 03 (models), per the plan's Related Documents row and Phase 3 order; all edits here are quoted-text anchored because wfaudit004 shifts line numbers in the same file.
- Missing-key behavior is the generic `WorkflowLoadError` message `retry_policy missing keys: {...}` (set repr), now naming `retry_wait_sec`; no compatibility shim accepts an old `backoff_sec` payload (plan UNK-02 decision, consistent with the `require_approval`-removal precedent in the same function and with `tools/check_compat_shims.py` policy).

## Design decisions
- Rename all five HEAD occurrences as a unit so validation, error text, and construction stay mutually consistent: the docstring sentence (HEAD L22), the `_RetryPolicyJson` field (L27), `_REQUIRED_POLICY_KEYS` (L53), the `_require_int` call pair `policy["backoff_sec"], "retry_policy.backoff_sec"` (L132), and the construction kwarg `backoff_sec=policy_data["backoff_sec"]` (L172).
- `_require_int` itself is untouched: its label argument carries the new field name, which is what the loader error text (`retry_policy.retry_wait_sec must be >= 0`) and the test match string rely on.

## Alternatives considered
- Accept both keys during a transition window: rejected — a config key rename ships with the config file in one deploy step (plan Notes: code and config deploy together); a dual-key window would need a shim this repo's compat-shim policy prohibits.

## Implementation
### Target file
`scripts/agent/workflow/workflow_loader.py`

### Procedure
Rename the retry-policy key at every loader site.

### Method
1. `_RetryPolicyJson` docstring: "max_attempts and backoff_sec are required at runtime" -> "max_attempts and retry_wait_sec are required at runtime".
2. `_RetryPolicyJson` field line `backoff_sec: int` -> `retry_wait_sec: int`.
3. `_REQUIRED_POLICY_KEYS = {"max_attempts", "backoff_sec"}` -> `_REQUIRED_POLICY_KEYS = {"max_attempts", "retry_wait_sec"}`.
4. `_require_int(policy["backoff_sec"], "retry_policy.backoff_sec", 0)` -> `_require_int(policy["retry_wait_sec"], "retry_policy.retry_wait_sec", 0)` (minimum 0 unchanged).
5. Construction: `backoff_sec=policy_data["backoff_sec"],` -> `retry_wait_sec=policy_data["retry_wait_sec"],`.

### Details
- After the edits `grep -n backoff_sec scripts/agent/workflow/workflow_loader.py` returns nothing.
- The `retry_policy missing keys` path: a payload omitting `retry_wait_sec` raises with the missing-set repr — no renamed-key special case.

## Compatibility considerations
- Old JSON files (repo or `/opt/llm/config/workflows/`) fail to load with the missing-keys error after this lands — the plan's UNK-01 deploy probe (`grep -r backoff_sec /opt/llm/config/workflows/`) migrates the production copy in the same deploy step as row 6.
- `tests/agent/test_repl_health.py` workflow-JSON fixture strings (row 12) must land with this row or those fixtures fail to load.

## Security considerations
- No change to validation strength: the same integer/minimum checks apply under the new name.

## Rollback considerations
- Revert the commit together with row 6 (config) and row 3 (models) so loader and shipped config agree on one key name.

## Validation plan
- `tests/agent/workflow/test_workflow_loader.py` (procedure 07): renamed fixtures, the parametrized field-list test, and the `retry_wait_sec must be >= 0` match string.
- Shipped-config load tests (the test that loads `config/workflows/default.json`) pass once row 6 lands.
- `uv run pytest tests/agent/workflow/ -q`, then full `uv run pytest tests/ -q` at unit completion; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- `REQ-003`: `backoff_sec` absent from the file; a definition carrying only `retry_wait_sec` loads; one omitting it fails with the missing-keys error naming `retry_wait_sec`.

## Out of Scope
- Stage-shape validation additions (wfaudit004's `151141_01` owns the `_validate` shape region).
- The `retry_on` validation logic (`_validate_retry_on` untouched).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: scripts/agent/workflow/workflow_loader.py
