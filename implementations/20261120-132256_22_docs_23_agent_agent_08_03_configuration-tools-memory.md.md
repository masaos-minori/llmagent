## Goal

Describe `allowed_tools` semantics per mode instead of an unconditional denial in the configuration-tools-memory reference (`REQ-003`, `REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 34 states an empty `allowed_tools` denies every tool at runtime (including after reload) and is rejected by the production validator at load.
- Line 87 repeats that `allowed_tools=[]` denies every tool and is a production-validator error.

## Design decisions
- At lines 34 and 87, replace the unconditional denial with mode-aware wording: valid and non-denying in `discovered` (base visibility applies), fatal in `explicit_allowlist`; remove the production-validator unconditional-reject claim.

## Alternatives considered
- Deleting the empty-list mention: rejected because it is still meaningful under `explicit_allowlist`.

## Implementation
### Target file
`docs/23_agent/agent_08_03_configuration-tools-memory.md`

### Procedure
Edit the `allowed_tools` config-reference bullet (line 34) and the related note (line 87) to be mode-aware.

### Method
Add mode qualification; drop the unconditional production-validator reject claim.

### Details
- Line 34: empty `allowed_tools` valid under `discovered`, fatal under `explicit_allowlist`; no longer a blanket production-validator rejection.
- Line 87: same mode-aware qualification.

## Compatibility considerations
Documentation accuracy only; no behavior change.

## Security considerations
No security impact: wording matches the enforced behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run the doc checker named in `routing.md` after editing.

## Completion criteria
Both bullets are mode-aware; the doc checker passes.

## Out of Scope
Runtime enforcement (`runtime_tool_registry.py`) and production validation (`production_config_validator.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests |

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
- **Related target files**: `docs/23_agent/agent_08_03_configuration-tools-memory.md`
