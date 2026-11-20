## Goal

Reflect that an empty `allowed_tools` is valid in `discovered` mode in the MCP-approval observation note (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 131 observes the empty-list denial as an absolute.

## Design decisions
- Qualify the observation at line 131: an empty `allowed_tools` is valid under `discovered` (base visibility applies) and fatal under `explicit_allowlist`.

## Alternatives considered
- Deleting the observation: rejected because the mode-dependent behavior is worth documenting.

## Implementation
### Target file
`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

### Procedure
Edit the observation at line 131 to qualify the empty-list denial by mode.

### Method
Append a mode qualifier to the observation.

### Details
- Line 131: empty `allowed_tools` valid under `discovered`, fatal under `explicit_allowlist`.

## Compatibility considerations
Documentation accuracy only; no behavior change.

## Security considerations
No security impact: wording matches the enforced behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run the doc checker named in `routing.md` after editing.

## Completion criteria
The observation is mode-aware; the doc checker passes.

## Out of Scope
Runtime enforcement (`runtime_tool_registry.py`).

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
