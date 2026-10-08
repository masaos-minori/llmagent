## Goal
State that MCP health probes authenticate. (REQ-006 of the Plan).

## Scope
- Only `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`; no other file is modified by this procedure.

## Assumptions
- User decision (2026-10-08): keep `/health` authenticated and add the Bearer token to the Agent-side probes.

## Design decisions
- Facts only; cite the exact symbols.

## Alternatives considered
- Exempting `/health` in `attach_auth_middleware()`: rejected by the user decision above.

## Implementation
### Target file
docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md

### Procedure
1. Add one Key Constraints bullet naming the probe sites and `McpServerConfig.auth_headers()`.

### Method
Facts only; cite the exact symbols.

### Details
Keep the section order.

## Compatibility considerations
- Documentation only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- the documentation checkers (check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_consistency --domain agent).

## Completion criteria
- The described change is in place and the validation commands pass (REQ-006).

## Out of scope
- Any file other than `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-180404 | 20261008-180404 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-180404 | 20261008-180404 |  |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20261008-165923_mcphealthauth01_send-the-bearer-token-in-the-post-startup-mcp-health-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-174859_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-175533
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md