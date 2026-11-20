## Goal

Replace the absolute empty-list denial statement for `allowed_tools` with the mode-aware contract in the concurrency-safety doc (`REQ-003`, `REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 33 states an empty `allowed_tools` denies every tool at runtime (including after reload) and that `ProductionConfigValidator` rejects it at load.
- Line 66 lists `allowed_tools=[]` as a fail-closed gate.

## Design decisions
- At line 33, qualify the empty-list denial by mode: valid and non-denying in `discovered`, fatal in `explicit_allowlist`; remove the `ProductionConfigValidator` unconditional-reject claim.
- At line 66, qualify the fail-closed bullet so `allowed_tools=[]` is fail-closed only under `explicit_allowlist`.

## Alternatives considered
- Deleting the fail-closed mention: rejected because an empty list is still fail-closed under `explicit_allowlist`.

## Implementation
### Target file
`docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`

### Procedure
Edit the tool-whitelist row (line 33) and the fail-closed bullet (line 66) to be mode-aware.

### Method
Add mode qualification; remove the unconditional production-validator reject claim.

### Details
- Line 33: empty `allowed_tools` is valid in `discovered` (base visibility applies) and fatal in `explicit_allowlist`; drop "rejected by the production validator at load".
- Line 66: keep `allowed_tools=[]` fail-closed only under `explicit_allowlist`.

## Compatibility considerations
Documentation accuracy only; no behavior change.

## Security considerations
No security impact: the mode-aware wording matches the enforced behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run the doc checker named in `routing.md` after editing.

## Completion criteria
Both statements are mode-aware; the doc checker passes.

## Out of Scope
Runtime enforcement (`runtime_tool_registry.py`) and production validation (`production_config_validator.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-191800 | 20261120-191800 | Edited `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`: line 33 now states empty `allowed_tools` denies every tool only under `explicit_allowlist` (fail closed) and is valid/non-denying in `discovered`; dropped the stale `ProductionConfigValidator` unconditional-reject claim (verified absent from `production_config_validator.py`; `validate_allowed_tools` marks empty list valid). Line 66 fail-closed bullet qualified with `under explicit_allowlist`. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-191800 | 20261120-191800 | Doc accuracy only; no behavior change. check_docs_quality/structure/content_policy(--strict) all pass; check_docs_consistency --domain agent reports only a pre-existing unrelated warning in agent_14 (not the edited file). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`, `REQ-007`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`
