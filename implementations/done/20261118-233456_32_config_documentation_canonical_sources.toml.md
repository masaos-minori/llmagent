## Goal

Register the approval claims this Plan documents in the canonical source registry so each claim resolves
to exactly one canonical source (REQ-010).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- Registry schema fields: `decision_target`, `claim_type`, `source_paths`, `area`, `notes`
  (`tools/check_canonical_source_registry.py` validates them, including single-normative-source
  enforcement and claim-type membership).
- No `approval_risk_rules` / `tool_safety_tiers` entry exists today (grep), so all entries below are new.

## Design decisions
- Register code as the normative source for behavior claims and the ADR for boundary claims; documents
  link to the registry rather than becoming sources.
- Reuse existing areas (`Agent`, `MCP`) and existing claim types (`runtime-behavior`,
  `configuration-schema`, `architecture-decision`) instead of inventing categories.

## Alternatives considered
Registering the approval documents themselves as sources — rejected; it would let documentation become
normative for behavior (AC-010).

## Implementation
### Target file
`config/documentation_canonical_sources.toml`
### Procedure
1. Add `agent.approval-risk-evaluation` (`claim_type = "runtime-behavior"`,
   `source_paths = ["scripts/agent/tool_policy.py"]`, `area = "Agent"`).
2. Add `agent.approval-configuration-posture` (`claim_type = "configuration-schema"`,
   `source_paths = ["config/agent.toml"]`, `area = "Agent"`).
3. Add `agent.argument-validation-default` (`claim_type = "runtime-behavior"`,
   `source_paths = ["scripts/agent/tool_arg_validator.py"]`, `area = "Agent"`).
4. Add `mcp.risk-tier-mapping` (`claim_type = "runtime-behavior"`,
   `source_paths = ["scripts/agent/tool_policy.py"]`, `area = "MCP"`).
5. Add `agent.approval-server-boundary` (`claim_type = "architecture-decision"`,
   `source_paths = ["docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md"]`,
   `area = "Agent"`).
### Method
Append `[[canonical_sources]]` blocks in the existing style; no existing entry changes.
### Details
- Each `notes` line names the document that defers to the source (rows 21/24/25/26).

## Compatibility considerations
`check_canonical_source_registry.py` enforces path existence and one normative source per
`decision_target`; a duplicate target with an existing entry must be merged, not duplicated.

## Security considerations
N/A: registry metadata.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_canonical_source_registry.py`

## Completion criteria
Every approval claim the Plan documents resolves to exactly one registered canonical source (AC-010).

## Out of Scope
The documents that link to these sources (rows 21/24/25/26).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the five registry entries per Procedure | Completed | 20261119-081707 | 20261119-081707 | Five `[[canonical_sources]]` blocks appended in existing style: `agent.approval-risk-evaluation`, `agent.approval-configuration-posture`, `agent.argument-validation-default`, `mcp.risk-tier-mapping`, `agent.approval-server-boundary`. Verified all five decision_targets were absent before (grep showed no approval_* entries); no existing entry changed; each `notes` names the deferring document (rows 21/24/25/26) |
| 3 | Run `check_canonical_source_registry.py` and the docs checkers | Completed | 20261119-081707 | 20261119-081707 | "Registry validation passed" (single-normative-source and claim-type gates); check_docs_consistency --domain agent and check_docs_quality pass |

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
- **Requirement ID**: `REQ-010` (canonical source registration)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `config/documentation_canonical_sources.toml`
