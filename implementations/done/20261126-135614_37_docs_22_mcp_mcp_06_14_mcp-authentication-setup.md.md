## Goal
- Document the one-token health authentication model (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the authentication model section; the health schema (seq 33) is out.

## Assumptions
- Verified in Step 3a: `auth_token` is already the single credential covered by `register_secret`, and `auth_headers()` becomes the only health header path after seq 03 removes the second one.

## Design decisions
- `auth_token` is the health credential, `auth_headers()` is the only header path, and the token never appears in a health log line or error message (D-1, REQ-003).

### Corrected in Step 3b
- Verified against the code: every health caller reads the header through `auth_headers()` (the startup poll, the health probe, and the tool-definition check), so the single-header-path statement is accurate as written.
- The no-token-in-logs rule was written as behavior plus the masking of captured text such as child stderr, because the health failure path logs the server key and the failure and passes captured text through the secrets masker; a bare "not the credential" wording would have hidden that mechanism.
- The section was placed as a subsection under "Setting up MCP authentication", after Setup Requirements and before Troubleshooting, which is where the model statement belongs.
- `auth_token` and `health requests` were added to Keywords.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`

### Procedure
1. State that health requests use the same `auth_token` as the other MCP requests, with no separate health credential.
2. State the single header path and the no-token-in-logs rule.

### Method
- Point to `auth_headers()` in `scripts/shared/mcp_config.py` as the canonical source; no example may show a token value.

### Details
- Keep the no-token-in-logs rule as one sentence pointing at the health failure path (seq 03).

## Compatibility considerations
- N/A: existing setups that set `auth_token` are unaffected.

## Security considerations
- The document must not contain a token value or a secret-looking example.

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
| 1 | Update the document and run the docs gates (`rules/tool-gates.md`) | Completed | 20261126-195544 | 20261126-195544 | Changed file: docs/22_mcp/mcp_06_14_mcp-authentication-setup.md. Added the Health Requests Use the Same Token subsection: same auth_token as every other MCP request, no separate health credential or second config key, auth_headers() as the single header path used by the startup poll and the health probe, and the no-token-in-logs rule stated with the masking of captured text. Added keywords. Docs gates pass: quality, structure, content policy, consistency --domain mcp, japanese. Full suite pending at end of batch. |

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
- **Related target files**: `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`