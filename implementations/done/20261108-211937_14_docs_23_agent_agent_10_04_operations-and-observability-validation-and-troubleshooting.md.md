## Goal
Update the Invalid Retry Policy symptom text in `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` so the quoted validator message names the renamed key (`REQ-003`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 14 only: `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`.

## Assumptions
- HEAD citation: the Invalid Retry Policy symptom line (HEAD L79) reads `**Symptom:** The validator reports \`retry_policy.max_attempts must be >= 1\` or \`retry_policy.backoff_sec must be >= 0\`.` — the second quoted message matches the loader label that procedure 04 renames.
- No sibling pending procedure touches this file (census of plan Related Documents rows).

## Design decisions
- Quote-rename only: the symptom text must match the message operators will actually see after procedure 04 lands (`retry_policy.retry_wait_sec must be >= 0`); the surrounding Symptom/Response structure and the `max_attempts` message are unchanged.

## Alternatives considered
- Leave the runbook quoting the old message: rejected — the plan's grep gate (`backoff_sec` absent from `docs/`) fails, and the runbook would send operators to a key that no longer exists.

## Implementation
### Target file
`docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`

### Procedure
One quoted-text edit.

### Method
At HEAD L79, replace `` `retry_policy.backoff_sec must be >= 0` `` with `` `retry_policy.retry_wait_sec must be >= 0` ``.

### Details
- After the edit, `grep -n backoff_sec docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` returns nothing.

## Compatibility considerations
- Landing order: after procedure 04 (the loader emits the new message); the doc and the emitted message must agree at deploy time.

## Security considerations
- No change: documentation-only edit.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- Docs checkers per `routing.md` "When to run which tool" (docs staleness/structure checks) on this file.

## Completion criteria
- `REQ-003`: no `backoff_sec` token in the file; the symptom line quotes the post-rename validator message.

## Out of Scope
- Other runbook sections (required-stages symptom, workflow.sqlite section).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-092921 | 20261109-092921 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261109-092921 | 20261109-092921 | N/A: documentation-only procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-092921 | 20261109-092921 | Full suite 11904 passed; 3 pre-existing env errors in test_workflow_status_vocabulary.py (/tmp/opencode missing); diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-092921 | 20261109-092921 | — |

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
- **Related target files**: docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md
