## Goal

Create the test for ADR-003 INV-03: routing, approval, and auditing use the same Safety Tier from one `RuntimeTool` (AAL-033).

## Scope
**Release unit**: N/A: not part of a release unit

One new test module. No production change.

## Assumptions

- Approval risk comes from `classify_risk` and `is_plan_mode_blocked` through the declared tier (`scripts/agent/tool_policy.py:77`, `:428`, `:453`; re-read in Step 3a).
- The audit event takes the risk as an argument, computed by the approval path (`scripts/agent/tool_audit.py:114`), so the consumers to compare are routing, `classify_risk`, plan-mode blocking, and the audit record.

## Design decisions

- Register one tool per tier in a `RuntimeToolRegistry`, drive each through `run_approval_checks` (`scripts/agent/tool_approval.py:336`), and compare with the registry tier.
- Flip the tiers in the registry and assert every consumer changes with it, proving there is no second source.

## Alternatives considered

Compare constants: rejected, it would not catch a consumer reading another map.

## Implementation
### Target file
`tests/agent/test_safety_tier_single_source.py` (new)

### Procedure
1. Read `tests/agent/test_tool_approval_risk.py` for fixtures that build an `AgentContext` and prepared calls.
2. Create `tests/agent/test_safety_tier_single_source.py` (new) with module docstring and the fixtures.
3. Add a test per tier asserting routed server key, `classify_risk` result, plan-mode block, and the audit risk string agree with the registry tier.
4. Add a flip test that rebuilds the registry with changed tiers and asserts all consumers follow.

### Method
- Use `shared.runtime_tool.build_runtime_tool` as `tests/shared/test_tool_executor_routing.py` does.
- Capture the audit call through the existing audit seam used by `tests/agent/test_tool_audit.py`.

### Details
- Mutation check: make `classify_risk` read a hard-coded set for one tool temporarily, confirm the test fails, revert.
- Cite the tests in ADR-003's INV-03 row and the index matrix in procedures 07 and 11.

## Compatibility considerations

N/A: adds a test only; no production behavior changes.

## Security considerations

N/A: no secret, permission, or input handling is touched; test fixtures use dummy tokens only.

## Rollback considerations

N/A: revert the commit (the file is new).

## Validation plan

- `uv run pytest tests/agent/test_safety_tier_single_source.py -q`
- ruff and mypy on the file

## Completion criteria

- The module passes and fails under the mutation.
- Only the new file was added.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Mutation-check the new test: break the invariant temporarily, confirm the test fails, revert the break | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (one Safety Tier source for routing, approval, audit (ADR-003 INV-03)), `REQ-008` (no production change, every test mutation-checked)
- **Source issue**: issues/20261123-164658_gov006_restore-blocking-verification-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-165432_gov006_restore-blocking-verification-rows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-165833
- **Related target files**: `tests/agent/test_safety_tier_single_source.py`
