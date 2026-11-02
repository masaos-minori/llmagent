# Document the HTTP status contract

## Goal

State the tool-level vs transport status contract in
`docs/22_mcp/mcp_03_03_transport-and-health.md` and fix the two bullets that currently claim every
non-2xx raises `TransportError` (Plan REQ-006 / AC).

## Scope

- The `## HttpTransport` section bullets at lines 26 and 30, plus one new "Status classification"
  bullet. Nothing else in the file; `mcp_health.py` behavior text is unchanged (the registry is not
  modified by this Plan).

## Assumptions

- Verified 20261102: line 26 says transport failures "non-2xx HTTP … never directly returns
  `is_error=True`" and line 30 says non-retryable `HTTPStatusError` propagates immediately — both
  become inaccurate once row 01 lands; the doc must land with the code.
- Wording must match the adopted contract recorded in the plan (UNK-01 Option A, UNK-02 set):
  tool-level `{400, 403, 404, 409, 422}`; transport `401` + all `5xx` + timeouts + malformed
  responses + retry exhaustion.

## Design decisions

- Add the "why" in one sentence per the Plan: tool-level outcomes are server-domain results and
  must not trip the health circuit; `401` stays transport so auth faults remain visible (REQ-006).

## Alternatives considered

- N/A: docs-only.

## Implementation
### Target file
`docs/22_mcp/mcp_03_03_transport-and-health.md`

### Procedure
- New bullet after the retry bullet (:29): **Status classification:** `/v1/call_tool` responses with
  tool-level statuses `400/403/404/409/422` do NOT raise `TransportError`; they return
  `ToolCallResult(is_error=True, error_type="tool")` with the server's reason (`detail` or `result`
  body field, raw text fallback) and count as health-registry successes (`record_success`), so
  repeated tool errors never cool the server down. `401`, all `5xx`, timeouts, malformed bodies and
  retry exhaustion remain `TransportError` and record health failures. The write-tool fail-closed
  gate on `502/503/504` (ADR-004) is unchanged.
- Amend :26 to "non-2xx HTTP outside the tool-level set" and :30 to `HTTPStatusError` for statuses
  other than 429/502/503/504 and the tool-level set.

### Details
- No new section heading; keep the bullet style of the section.

## Compatibility considerations

- N/A: documentation only.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py`,
  `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain mcp`
  per `routing.md` Tools "When to run which tool".

## Completion criteria

- The file states the two status sets and the registry consequence; no remaining claim that every
  non-2xx raises `TransportError`; docs checkers pass.

## Out of Scope

- Option B wording (Option B was not selected); any other MCP doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the classification bullet and amend the two status bullets | Pending | — | — | Land with row 01 |
| 2 | Run the docs checkers (`routing.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (status contract documented)
- **Source issue**: issues/20261101-073450_healthcascade001_tool-4xx-trips-circuit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141054_healthcascade001_tool-4xx-trips-circuit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132712
- **Related target files**: docs/22_mcp/mcp_03_03_transport-and-health.md
