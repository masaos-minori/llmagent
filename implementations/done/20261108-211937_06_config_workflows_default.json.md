## Goal
Rename the shipped workflow definition's retry-policy key to `retry_wait_sec` in `config/workflows/default.json` so the loader (row 4) accepts the shipped file (`REQ-003`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 6 only: `config/workflows/default.json`.

## Assumptions
- Landing order: after procedures 03 and 04; `config/workflows/` contains exactly this one file (census 2026-11-08), and the loader's `_REQUIRED_POLICY_KEYS` makes the key mandatory.
- Deploy coupling: `config/workflows/` is a deploy-synced artifact; the production copy `/opt/llm/config/workflows/default.json` carries `backoff_sec` at the time of the pass (plan UNK-01 evidence), so code and config must ship in the same deploy step.

## Design decisions
- Single-key rename in the `retry_policy` object (HEAD L23): `"backoff_sec": 1` -> `"retry_wait_sec": 1`; value 1 unchanged, preserving `REQ-004` numerics for the shipped policy.

## Alternatives considered
- Ship the config rename separately from the code rename: rejected — the loader accepts only one key name, so a separated rollout breaks workflow loading between the two deploy steps.

## Implementation
### Target file
`config/workflows/default.json`

### Procedure
Rename one JSON key.

### Method
In the top-level `retry_policy` object, the line `"backoff_sec": 1,` (HEAD L23) -> `"retry_wait_sec": 1,`. No other key, value, or the surrounding `stages` array changes.

### Details
- JSON validity: rename only; key order inside `retry_policy` (`max_attempts`, `retry_wait_sec`, `retry_on`) preserved.

## Compatibility considerations
- Deploy step (plan UNK-01 pre-check): `grep -r backoff_sec /opt/llm/config/workflows/` — the hit on the production `default.json` is migrated in the same deploy step (deploy syncs `config/` per the deploy skill); a production config left with the old key fails the loader with the missing-keys error.

## Security considerations
- No change to data handling.

## Rollback considerations
- Revert the commit together with rows 3-4 so code and shipped config agree on one key name.

## Validation plan
- Loader tests that load the shipped `config/workflows/default.json` (in `tests/agent/workflow/test_workflow_loader.py`) pass after rows 4 and 6 land.
- `uv run pytest tests/agent/workflow/ tests/agent/test_orchestrator.py -q` (orchestrator fixtures load the shipped definition).
- Deploy pre-check command above recorded in the implementation pass.

## Completion criteria
- `REQ-003`: `grep -rn backoff_sec config/` returns nothing; the shipped definition loads with `retry_wait_sec: 1`.

## Out of Scope
- The production-side sync command itself (owned by the deploy step, not this file row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-092921 | 20261109-092921 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261109-092921 | 20261109-092921 | N/A: tests covered by procedures 07-12 and 15 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-092921 | 20261109-092921 | Full suite 11904 passed; 3 pre-existing env errors in test_workflow_status_vocabulary.py (/tmp/opencode missing); diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-092921 | 20261109-092921 | N/A: docs covered by procedures 13-14 |

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
- **Related target files**: config/workflows/default.json
