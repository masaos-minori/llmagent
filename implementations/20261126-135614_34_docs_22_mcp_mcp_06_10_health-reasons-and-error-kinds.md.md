## Goal
- Present the degraded reason codes as the closed contract vocabulary (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the reason-code catalog; the health schema section (seq 33) is out.

## Assumptions
- Verified in Step 3a: this file is the canonical home of the health reason catalog; the contract module (seq 01) defines the closed set this document must match.

## Design decisions
- A code outside the set is a parse failure, not a warning (REQ-004).

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`

### Procedure
1. State the codes as a closed vocabulary that producers may emit only.
2. State that an out-of-vocabulary code is rejected by the strict parser.

### Method
- Names must equal the constants in `scripts/shared/mcp_health_contract.py`.

## Compatibility considerations
- N/A: existing reason descriptions stay.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- docs gate: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_docs_japanese.py`; then `rules/toolchain.md`.

## Completion criteria
- The document states the rule as implemented; docs gates pass.

## Out of Scope
- Code changes and the other docs files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the document and run the docs gates (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Related target files**: `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`
