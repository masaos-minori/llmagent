## Goal
- Document the required-versus-optional capability distinction and the health state mapping (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the naming convention status section and the capability model; the reason codes (seq 34) are out.

## Assumptions
- Verified in Step 3a: line 86 states the convention is optional and no production server declares `capabilities`; after seq 16 and seq 17 the GitHub server declares `github.operations` (required) and `github.api` (optional), so that statement becomes stale.

## Design decisions
- Required-ness is derived by the Agent from the catalog `required_capability` of a `required=true` server (D-6); servers that declare no capabilities keep the legacy reading rule.

### Corrected in Step 3b
- Re-checked in this cycle: GitHub is the only production server that declares a capability block, so the Status section names it alone. The Overview's optional statement is unchanged; the Status section now scopes optionality to servers that do not declare capabilities, which is what makes the two sections agree.
- Two sections were added before Status: Required And Optional Capabilities (required versus optional, FATAL versus warning, required-ness derived from the catalog rather than declared by the server, the no-declaration reading rule) and Capability Health States (the three-state closed vocabulary, only `ok` proves readiness, the reason code, and the tool dependency rule).
- Requirement IDs are not written into the document, per `check_docs_quality.py` Current-Specification-Only Policy.
- The existing example names are unchanged, per Method; `github.api` already follows the domain-dot-action form.
- `required capability` and `capability state` were added to Keywords.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_08_tool_capability_naming_convention.md`

### Procedure
1. Update the Status section to name the declaring server (GitHub: `github.operations`, `github.api`).
2. Add the required-versus-optional rule and the state mapping (`ok`, `degraded`, `unavailable`).

### Method
- Keep the existing example names unchanged; `github.api` already follows the domain-dot-action form.

### Details
- Record that `github.operations` is required and `github.api` optional (seq 16, seq 17).

## Compatibility considerations
- N/A: the convention stays optional for non-declaring servers.

## Security considerations
- N/A: documentation-only; capability identifiers only.

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
| 1 | Update the document and run the docs gates (`rules/tool-gates.md`) | Completed | 20261126-195752 | 20261126-195752 | Changed file: docs/22_mcp/mcp_08_tool_capability_naming_convention.md. Added Required And Optional Capabilities and Capability Health States sections, and replaced the stale Status claim with the declaring server (GitHub: github.operations required, github.api optional). Docs gates pass: quality, structure, content policy, consistency --domain mcp, japanese. Full suite pending at end of batch. |

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
- **Related target files**: `docs/22_mcp/mcp_08_tool_capability_naming_convention.md`