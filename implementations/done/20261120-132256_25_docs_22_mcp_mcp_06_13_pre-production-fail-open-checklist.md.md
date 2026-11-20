## Goal

Fix the pre-production fail-open checklist gate so it permits an empty `allowed_tools` under `discovered` mode (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 20 gates on `allowed_tools=[]` as a fail-open violation unconditionally.

## Design decisions
- Qualify the checklist gate at line 20: an empty `allowed_tools` is a fail-open concern only under `explicit_allowlist`; under `discovered` it is valid.

## Alternatives considered
- Deleting the gate: rejected because an empty allowlist is still a fail-open concern under `explicit_allowlist`.

## Implementation
### Target file
`docs/22_mcp/mcp_06_13_pre-production-fail-open-checklist.md`

### Procedure
Edit the checklist gate at line 20 to qualify the empty-list check by mode.

### Method
Append a mode qualifier to the gate.

### Details
- Line 20: empty `allowed_tools` is a fail-open gate under `explicit_allowlist`; permitted under `discovered`.

## Compatibility considerations
Documentation accuracy only; no behavior change.

## Security considerations
No security impact: wording matches the enforced behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run the doc checker named in `routing.md` after editing.

## Completion criteria
The checklist gate is mode-aware; the doc checker passes.

## Out of Scope
Runtime enforcement (`runtime_tool_registry.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-193700 | 20261120-193700 | Edited `docs/22_mcp/mcp_06_13_pre-production-fail-open-checklist.md` line 20 checklist gate: qualified the empty-list check to `explicit_allowlist` (denies every tool at runtime, including after `/reload`) and added that an empty list is valid (base visibility) under `discovered`; dropped the stale "ProductionConfigValidator.validate() rejects allowed_tools=[]" claim (verified absent from `production_config_validator.py`; `validate_allowed_tools` accepts empty list). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-193700 | 20261120-193700 | Doc accuracy only; no behavior change. check_docs_quality/structure/content_policy(--strict) all pass; check_docs_consistency --domain mcp reports no issues. |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `docs/22_mcp/mcp_06_13_pre-production-fail-open-checklist.md`
