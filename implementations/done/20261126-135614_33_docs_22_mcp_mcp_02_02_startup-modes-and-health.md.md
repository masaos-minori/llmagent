## Goal
- Document the health body schema, the report-based readiness rule, and the timeout rules (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: the health schema and startup-health sections; reason codes (seq 34) and the config field rule (seq 36) are out.

## Assumptions
- Verified in Step 3a: the document describes `status`/`ready`/`dependencies` only (`mcp_02_02_startup-modes-and-health.md:26-40`).
- Re-checked in this cycle: the cited range covers `status`, `ready`, and `liveness`; the document also describes `restart_recommended`, `operator_action_required`, `details`, and the `security` block further on. None of the three contract fields this procedure adds (`health_schema_version`, `degraded_reasons`, `capabilities`) was present, so the procedure still applies.

## Design decisions
- Readiness is the proven required capability, or `ready` for a legacy body (D-6); timeout is a positive per-server value capped by the remaining time to the deadline (D-3, D-4).

### Corrected in Step 3b
- The document already described `liveness` and `ready` as producer fields, so the contract section names the five contract fields and details only the ones the contract added (`health_schema_version`, `degraded_reasons`, `capabilities`); the existing bullets were kept and the `ready` bullet now points to the readiness rule.
- The readiness and timeout rules were added as two subsections under `## HTTP Startup Modes`, which is where the startup poll is described.
- The `health_timeout` field rule itself is not restated here (seq 36 owns it); this document states only the consequence the cap needs, the effective value is always positive, and links to seq 36's file. No concrete default value is stated, per `skills/DESIGN.md` No concrete configuration values.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_02_02_startup-modes-and-health.md`

### Procedure
1. Add the contract fields (`health_schema_version`, `liveness`, `ready`, `degraded_reasons`, `capabilities`) and the legacy-body rule.
2. Replace the readiness wording with the report-based rule and add the timeout rules.

### Method
- Behavior level only; `scripts/shared/mcp_health_contract.py` is the canonical source for field names.

### Details
- The readiness wording must match the implemented rule (proven required capability, legacy fallback), not the old liveness-only wording (seq 01, seq 03).

## Compatibility considerations
- N/A: legacy servers stay described through the legacy branch.

## Security considerations
- N/A: documentation-only; the rule that the token is never logged is stated without a value.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- docs gate: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_docs_japanese.py`, `generate_reference_table.py --check`; then `rules/toolchain.md`.

## Completion criteria
- The document states the rule as implemented; docs gates pass.

## Out of Scope
- Code changes and the other docs files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the document and run the docs gates (`rules/tool-gates.md`) | Completed | 20261126-194713 | 20261126-194713 | Changed file: docs/22_mcp/mcp_02_02_startup-modes-and-health.md. Added the Startup Readiness Rule and the Health Check Timeout Rules subsections under HTTP Startup Modes, the contract-fields table plus the legacy-body rule in Standard /health Response Semantics, and the ready bullet pointing to the readiness rule. Docs gates pass: check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_consistency --domain mcp, check_docs_japanese. Full suite pending at end of batch. |

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
- **Requirement ID**: `REQ-009` (Documentation Impact)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`