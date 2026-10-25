# Implementation Procedure — docs/22_mcp/mcp_02_01_endpoints-and-transport.md

## Goal

State the correlation-id invariant in the MCP transport doc: `X-Session-Id` is set at
agent startup AND refreshed whenever the active session id changes (REQ-006, AC-006).

## Scope

- Modify one wording block in `docs/22_mcp/mcp_02_01_endpoints-and-transport.md`
  (line 50 at HEAD b5c215cdb).
- No other file is modified by this procedure (code side: procedures 01-03).

## Assumptions

- Verified 2026-10-25: line 50 currently reads:
  "`X-Session-Id` is set during agent startup via `ToolTransportInvoker.set_session_id()`
  and is injected into all POST requests by `HttpTransport.call()`."
- `docs/22_mcp/mcp_03_03_transport-and-health.md:64` ("spans the entire session")
  remains accurate per-session after the fix — not edited (plan target table).
- Docs are written in English per `skills/DESIGN.md` Output language.

## Design decisions

- Invariant + failure behavior only, no code detail (issue Documentation Impact,
  verbatim intent; `skills/DESIGN.md` docs content policy — existing symbol mentions
  `ToolTransportInvoker.set_session_id()` / `HttpTransport.call()` stay as the
  canonical-source pointers).
- Single-sentence-pair edit in place; no new section, no front matter change.

## Alternatives considered

- Also editing `mcp_03_03:64`: rejected — verified still true (the invariant now
  guarantees it per session).

## Implementation
### Target file
`docs/22_mcp/mcp_02_01_endpoints-and-transport.md`

### Procedure
Replace the line-50 sentence with the invariant statement.

### Method
From:

> `X-Session-Id` is set during agent startup via `ToolTransportInvoker.set_session_id()`
> and is injected into all POST requests by `HttpTransport.call()`.

To:

> `X-Session-Id` is set during agent startup via `ToolTransportInvoker.set_session_id()`
> and refreshed whenever the agent's active session id changes (session restore,
> new-session clear). It is injected into all POST requests by `HttpTransport.call()`.
> If a session-id change is not followed by a refresh, tool calls keep the previous
> session's id and server-side audit attribution is wrong for the rest of the run.

### Details
- Keep the surrounding correlation-keys table (lines ~55-62) unchanged.
- If the docs structure checker requires it, no front matter or Keywords change is
  expected — the edit stays inside the existing section body.

## Compatibility considerations

- `check_docs_consistency.py --domain mcp` cross-checks symbol references against
  `scripts/`: both cited symbols exist at HEAD (`tool_transport_invoker.py:73`,
  `http_transport.py` `call()`); no new symbols are introduced by this doc.
- `mcp_03_03` link/wording unaffected.

## Security considerations

N/A: documentation only.

## Rollback considerations

Revert the sentence to the line-50 text quoted above.

## Validation plan

- Docs checkers per `routing.md` after the edit:
  `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_02_01_endpoints-and-transport.md`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain mcp`,
  `uv run python tools/check_docs_japanese.py`.
- AC-006 gate: all five report no findings for this file.

## Completion criteria

- AC-006: `mcp_02_01` states the startup + refresh invariant and the failure behavior;
  docs checkers pass.

## Out of Scope

- Code changes (procedures 01-03).
- `mcp_03_03_transport-and-health.md` (verified no change needed).
- Server-side handling of session ids (issue out-of-scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the line-50 sentence with the invariant statement | Pending | — | — | |
| 2 | Run the five docs checkers | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: `issues/done/20261025-115646_sess003_stale-session-id-header.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123521_sess003_stale-session-id-header.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-134617
- **Related target files**: docs/22_mcp/mcp_02_01_endpoints-and-transport.md
