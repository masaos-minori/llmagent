## Goal
- Document the `browser_fetch` network boundary so the text no longer implies that the extracted-text limit is a complete resource control (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `browser_fetch` security boundary section of `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`.
- Out of scope: the GitHub and file-read sections, and the allowlist normalization and audit text (other Plans edit those sections of this file).

## Assumptions
- Overlap judgment (Plan overlap check): this file is also targeted by the configuration and audit Plan (allowlist normalization, audit, health wording, Bearer examples), the file MCP hardening Plan (file-read policy), and the MCP design docs update Plan (GitHub and file-read corrections plus a final sweep). This document edits only the `browser_fetch` security boundary bullets, so the four are compatible; the phases rebase onto each other.
- Written after the code procedures so each statement cites implemented behavior; the section currently lists the allowlist, the clamped `max_response_kb`, byte-based truncation, and the separate health and metrics singletons (`mcp_04_01...md:44-55`).

## Design decisions
- Add bullets rather than restructuring the section; write in English with normative terms.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`

### Procedure
1. In the `browser_fetch` security boundary list, add bullets for: DNS resolution of every A and AAAA answer with rejection of loopback, private, link-local, reserved, multicast, unspecified, and IPv4-mapped prohibited addresses, and rejection of a mixed answer as a whole; the pinned connection with the original host kept as `Host` and TLS server name; no use of environment proxies.
2. Add bullets for: redirects followed manually up to 5 hops with the scheme, allowlist, DNS, and address checks repeated per hop; only 2xx is a result and 3xx without a usable redirect, 4xx, 429, and 5xx are errors with distinct categories and error types.
3. Add bullets for: supported content types (`text/html`, `text/plain`) and the four independent limits (raw, decoded, parser input, returned), with the response flags `download_truncated` and `truncated`; state that the returned-text limit alone does not bound network or parser use.
4. Add the metrics and health rule: which categories count as browser health failures and which are metrics-only.

### Method
- Use the values and names from the implemented code, not from the Plan; if a value differs, the code wins.

### Details
- Keep the existing bullets; edit one only when it now misstates behavior (the sentence that describes truncation as the size control).

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only; do not publish example internal addresses beyond reserved documentation ranges.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- The documentation checkers named in `rules/tool-gates.md` "When to run which tool", through `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The section states the REQ-009 items consistently with the implemented behavior and the documentation gates report no finding.

## Out of Scope
- Allowlist normalization, audit redaction, health wording, Bearer examples, and the GitHub and file-read sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `browser_fetch` boundary section | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-009` (fetch boundary documentation)
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114539_mcpws001_websearch-fetch-network-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-122333
- **Related target files**: `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`
