## Goal

Declare the extended required field set on the `McpTool` TypedDict that every producer `TOOL_LIST` literal is typed against (REQ-003; AC-03).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- This row was added during procedure generation by the owner's decision: the producer literals cannot type-check against the extended set without the TypedDict being extended.

## Design decisions
- Use the type aliases from `scripts/shared/tool_metadata.py` as the value types, so the TypedDict and the closed value sets have one definition.
- `resource_scope_keys` value type becomes the key-to-`ResourceKeyKind` mapping, matching row 03.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/mcp_servers/models.py`
### Procedure
- Add the new `Required[]` entries to `McpTool` and change the `resource_scope_keys` annotation to the mapping type.
### Method
- No field is added as `NotRequired`: a field the plan requires must be declared, so an omitted key fails at type-check time as well as at validation.
### Details
- Verified 2026-11-21: `McpTool` currently declares `name`, `description`, `inputSchema`, `status`, `config_dependent`, `is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys` as `Required`; producer literals are typed as `list[McpTool]`.

## Compatibility considerations
- The TypedDict is the type the 13 producer files are written against; it lands with them in the same release unit.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- Every producer literal carries the extended set, and `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` reports no missing key.
- The value types are the same definitions the contract test checks.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 3; release unit: contract-and-producers |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/mcp_servers/models.py`
