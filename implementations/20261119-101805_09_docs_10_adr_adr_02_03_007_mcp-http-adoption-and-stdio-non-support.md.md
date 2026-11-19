## Goal

Apply the same Operational Consequences clarification to ADR-007's identical reload/restart bullet (REQ-005: wording/evidence edit per Plan DT-03).

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 3)

- In scope: one Operational Consequences bullet in this ADR.

## Assumptions
- The bullet at `:185` ("A configuration change requires restarting the owning process") is byte-identical to the ADR-002 one handled by the seq 08 document; the same approved wording pattern (DT-03 Option A) applies, with `mcp_servers/*` changes as this ADR's local example: MCP server definition changes remain restart-required (this Plan does not change MCP classification).
- Per `docs/00_governance/governance_01_documentation-policy.md` ADR Change Protocol (`:315-320`), a decision-preserving edit does not reopen approval; Decision, Status, and Approval Record texts stay byte-identical.

## Design decisions
- Mirror the seq 08 document's clause so the two ADRs state the same split pointing at the same canonical registry.

## Alternatives considered
- N/A: DT-03 approved; the alternative (leaving the contradictory bullet) is the defect this Plan fixes.

## Implementation
### Target file
`docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`

### Procedure
1. At the Operational Consequences bullet (`:185`), state the split the same way as the seq 08 document: registry-listed reloadable fields (`registry/manifests/config_ownership.yaml`) are applied by `/reload` without restarting the agent process; startup-only fields and MCP server configuration changes still require restarting the owning process.
2. Keep the neighboring Health Check bullets and all Decision/Status/Approval Record content byte-identical.

### Method
- One-bullet wording change; no new headings, no front-matter change.

### Details
- Do not enumerate individual field names in the ADR (docs content policy: reference the canonical registry).

## Compatibility considerations
- No ADR-sited test gate cites this bullet; `tools/check_adr_structure.py` validates structure only.

## Security considerations
- Documents that MCP server changes stay outside the reload gate, preserving this ADR's restart semantics.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| ADR structure | `uv run python tools/check_adr_structure.py` | Pass |
| Docs checkers (`routing.md` Tools) | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`; `uv run python tools/check_docs_content_policy.py` | Pass |

## Completion criteria
- The ADR states the reload/restart split pointing at the registry manifest, and every Decision/Status/Approval Record line is unchanged (AC-004).

## Out of Scope
- The ADR's Decision text; ADR-002 (seq 08 document); any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the one-bullet wording change | Pending | — | — | |
| 2 | Run `tools/check_adr_structure.py` and the `routing.md` Tools docs checkers | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (ADR wording/evidence clarification, decision unchanged)
- **Source issue**: issues/20261117-123004_adrchk004_hot-reload-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-094759_adrchk004_hot-reload-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-101805
- **Related target files**: `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`
