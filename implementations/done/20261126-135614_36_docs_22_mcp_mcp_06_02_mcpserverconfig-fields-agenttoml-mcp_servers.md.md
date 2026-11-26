## Goal
- Document that `health_timeout` must be greater than 0 (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `health_timeout` field description; the readiness and timeout-cap rules (seq 33) are out.

## Assumptions
- Verified in Step 3a: the current wording allows 0 as unlimited, which seq 02 removes.
- Re-checked in this cycle: the wording is a blanket statement over the timeout fields, not a `health_timeout` statement, and the other timeout fields still accept 0, so the statement was scoped rather than replaced. `health_timeout` was not named anywhere in the document before this change.

## Design decisions
- The value must be greater than 0, the default when unset stays 5.0, and the resolver always returns a positive float (D-3).

### Corrected in Step 3b
- The document never named `health_timeout`; the zero-means-unlimited wording was a blanket statement over the timeout fields. The rule was applied by scoping that statement to the per-call and startup fields, which still accept 0 (`call_timeout_sec >= 0`, `startup_timeout_sec >= 0`), and adding a `health_timeout` bullet for the greater-than-0 rule.
- The concrete default is not written into the document, per `skills/DESIGN.md` No concrete configuration values; the document states that the resolver returns the configured value when set and the default when unset, and points to `scripts/shared/mcp_config.py` as the canonical source.
- "Keep the field table shape" has no table to keep: this document has no field table, and the generated-table check covers `config/agent.toml`, which is unaffected.
- Rejection at direct construction was verified against `McpServerConfig._validate_timeouts()`, which is what both the config-load path and a direct construction run.
- `health_timeout` was added to Keywords.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`

### Procedure
1. Replace the zero-means-unlimited wording with the greater-than-0 rule, rejected at config load and direct construction.
2. Keep the field table shape so the generated-table check stays stable.

### Method
- Point to `scripts/shared/mcp_config.py` as the canonical source for the validation rule.

### Details
- The accepted-range wording (greater than 0) must match the load error produced by seq 02.

## Compatibility considerations
- N/A: no repository config sets the key, so no documented configuration becomes invalid.

## Security considerations
- N/A: documentation-only; the field is described without any token value.

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
| 1 | Update the document and run the docs gates (`rules/tool-gates.md`) | Completed | 20261126-195433 | 20261126-195433 | Changed file: docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md. Scoped the blanket zero-means-unlimited statement to the per-call and startup fields, which still accept 0, and added the health_timeout bullet stating the greater-than-0 rule rejected at config load and direct construction, always a positive value, with the canonical source named and the cap rule linked to seq 33's document. Added the keyword. Docs gates pass: quality, structure, content policy, consistency --domain mcp, japanese, generate_reference_table --check. Full suite pending at end of batch. |

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
- **Related target files**: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`